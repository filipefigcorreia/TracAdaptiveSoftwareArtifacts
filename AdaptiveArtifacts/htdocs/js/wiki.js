function view_artifact_ajax_call(asa_token_content, editor){
    var pattern = /\[asa[:]([0-9]+)(?:[\s+|\.](?:[^\]]+)?)?\]/g;
    var match = pattern.exec(asa_token_content);
    if (match == null){
        alert("Sorry, can't figure out which custom artifact this is.");
        return;
    }
    var id = match[1];

    createASAFormDialogFromUrl('View Custom Artifact', baseurl+"/artifact/"+id+"?action=view",
        {
            "Edit": function() {
                $(this).dialog("close");
                createASAFormDialogFromUrl('Edit Custom Artifact', baseurl+"/artifact/"+id+"?action=edit",
                    {
                        "Save   ": function() {
                            addAttributeOrderFields($("#artifact-form"));
                            submitASAFormDialog(
                                $(this),
                                {
                                    success: function(data){
                                        var statesLength = editor.session.bgTokenizer.states.length;
                                        editor.session.bgTokenizer.fireUpdateEvent(0,statesLength);
                                        editor.session.bgTokenizer.start(0);
                                    }
                                }
                            )},
                        "Close": function() { $(this).dialog("close"); }
                    }
                ).dialog('open');
            },
            "Close": function() { $(this).dialog("close"); } },
            {
                error: function(){
                    alert("Sorry, the custom artifact with id #"+id+" \ncould not be found.");
            }
        }
    ).dialog('open');

}

function link_to_existing_artifact_ajax_call(click_callback, value){
    createASAFormDialogFromUrl('Select Custom Artifact',  baseurl+"/search/by_filter?",
        [
            {
                id:'button-choose',
                text:'Choose',
                click: function(){
                    click_callback();
                    $(this).dialog("close");
                }
            },
            {
                id:'button-cancel',
                text:'Cancel',
                click: function() { $(this).dialog("close"); }
            }
        ],
        {
            open: function(){
                $("#button-choose").button("disable");

                var selectionUpdated = function(selected){
                    var content_div = $(".artifacts #asa-wrapper #dialog-content");
                    var asa_div = $(".artifacts #asa");
                    var close_button = $("#button-choose");
                    if (selected.length==0){
                        close_button.button("disabled");
                        content_div.html("").hide();
                        asa_div.addClass('invisible');
                        return;
                    }
                    selected.prop('checked', true);
                    close_button.button("enable");
                    Requests.getArtifactHtml(selected.val(), function(data){
                        content_div.html(data).show();
                        asa_div.removeClass('invisible');
                    });
                };
                $('table.listing tbody tr').click(function() {
                    selectionUpdated($(this).find('td input[type=radio]'));
                });

                var clearRows = function(){
                    $(".artifacts table.listing tbody tr:not(.prototype)").remove();
                };
                var addResultRow = function(id, spec_name, title){
                    var copy = $(".artifacts table.listing tr.prototype").clone(true);
                    copy.removeClass('prototype');
                    copy.find("input[type^='radio']").attr("value", id);
                    $(copy.find("td")[1]).text(title);
                    $(copy.find("td")[2]).text(spec_name);
                    $(".artifacts table.listing tbody").append(copy) ;
                };
                var addMessageRow = function(text){
                    var messageRow = $('<tr><td colspan="3" class="message">' + text + '</td></tr>');
                    $(".artifacts table.listing tbody").append(messageRow);
                };
                var timer;
                var delayedUpdateResults = function(){
                    clearTimeout(timer);
                    timer = setTimeout(function(){
                        var spec = $('.filter #spec').val();
                        var attr_name = $('.filter #attribute').val();
                        var attr_value = $('.filter #value').val();
                        var attribute = {};
                        attribute[attr_name] = [attr_value];

                        Requests.searchArtifacts(spec, attribute, function(data){
                            clearRows();
                            if(data.length==0){
                                addMessageRow('No Custom Artifacts found');
                            }
                            for(var i=0;i<data.length;i++)
                                addResultRow(data[i].id, data[i].spec, data[i].title);
                            selectionUpdated($('form#artifact-select input[name=selected]:checked'));
                        })
                    }, 1000)
                };
                $(".filter #spec").on('input',function(){delayedUpdateResults();});
                $(".filter #attribute").on('input',function(){delayedUpdateResults();});
                $(".filter #value")
                    .on('input',function(){delayedUpdateResults();})
                    .val(value)
                    .focus();
                delayedUpdateResults();
                $('.asa-dialog').parent().css('top', Math.max($('.asa-dialog').parent().position().top-100, 0) + 'px');
            }
        }
    ).dialog('open');
}

var setupEditor = function() {
    // Hide trac's textarea and show a contenteditable div in its place
    var textarea = $('textarea#text,textarea#field-description');
    textarea.hide().before('<div id="editor" style="clear: left;"/>');

    var editor = ace.edit("editor");
    //Get Ace Keyboard Handler and remove Find Events
    var khandler = editor.getKeyboardHandler();
    for(var key in khandler.commmandKeyBinding) {
        for(var prop in khandler.commmandKeyBinding[key]) {
            if(khandler.commmandKeyBinding[key].hasOwnProperty(prop))
                var control = khandler.commmandKeyBinding[key][prop].bindKey.win;
                var SupressingList = ["Ctrl-Shift-R", "Ctrl-R","Ctrl-F"];
                if(SupressingList.indexOf(control) != -1 )
                    khandler.commmandKeyBinding[key][prop] = null;
        }
    }
    editor.setKeyboardHandler(khandler);

    editor.setTheme("ace/theme/trac_wiki");
    editor.getSession().setUseWrapMode(true);
    editor.setHighlightActiveLine(false);
    editor.setShowPrintMargin(false);
    editor.renderer.setShowGutter(false);

    editor.getSession().setValue(textarea.val());
    editor.getSession().on('change', function(){
        textarea.val(editor.getSession().getValue());
    });

    // Initially a copy of trac/htdocs/js/resizer.js
    // Allow resizing <textarea> elements through a drag bar
    var setupEditorResizing = function(editor, editordiv) {
        var offset = null;

        function beginDrag(e) {
            offset = editordiv.height() - e.pageY;
            editordiv.blur();
            $(document).mousemove(dragging).mouseup(endDrag);
            return false;
        }

        function dragging(e) {
            editordiv.height(Math.max(32, offset + e.pageY) + 'px');
            editor.resize();
            return false;
        }

        function endDrag(e) {
          editordiv.focus();
          $(document).unbind('mousemove', dragging).unbind('mouseup', endDrag);
        }

        var grip = $('#editor').parent().find('.trac-grip').mousedown(beginDrag)[0];
        if (grip != undefined){
            editordiv.wrap('<div class="trac-resizable"><div></div></div>')
                .parent().append(grip);
            grip.style.marginLeft = (this.offsetLeft - grip.offsetLeft) + 'px';
            grip.style.marginRight = (grip.offsetWidth - this.offsetWidth) +'px';
        }
    };
    setupEditorResizing(editor, $('#editor'));

    // Originally copied from trac/wiki/templates/wiki_edit.html
    // Rewires the event of checking the "Adjust edit area height" box
    $("#editrows").change(function() {
        $('#editor').height(this.options[this.selectedIndex].value * $("div.ace_gutter-layer").find(".ace_gutter-cell:first").height());
        editor.renderer.onResize(true);
    });

    // Ensure the editor is updated after showing it (in case it was hidden...)
    $("#modify").parent().bind('classremoved', function(ev, newClasses) {
        editor.resize();
        editor.renderer.updateFull();
    });

    return editor;
};

var setupToolbar = function(editor){
    var wrapSelection = function(prefix, sufix){
        var value = editor.getCopyText();
        editor.insert(prefix + value + sufix);
        editor.focus();
    };

    var toolbar = $('#editor').closest("fieldset").find(".wikitoolbar");

    // Rewire the event handlers of the toolbat buttons to work with the div instead of the textarea
    toolbar.find("#strong").click(function() {
        wrapSelection("'''", "'''");
    });

    toolbar.find("#heading").click(function() {
        wrapSelection("\n== ", " ==\n");
    });

    toolbar.find("#em").click(function() {
        wrapSelection("''", "''");
    });

    toolbar.find("#link").click(function() {
        wrapSelection("[", "]");
    });

    toolbar.find("#code").click(function() {
        wrapSelection("\n{{{\n", "\n}}}\n");
    });

    toolbar.find("#hr").click(function() {
        wrapSelection("\n----\n", "");
    });

    toolbar.find("#np").click(function() {
        wrapSelection("\n\n", "");
    });

    toolbar.find("#br").click(function() {
        wrapSelection("[[BR]]\n", "");
    });

    toolbar.find("#img").click(function() {
        wrapSelection("[[Image(", ")]]");
    });

    // Add custom buttons to the toolbar

    toolbar.after('<div class="wikitoolbar" id="asa_toolbar"></div>');
    var asa_toolbar = $('#asa_toolbar');
    asa_toolbar.append('<a href="#" id="asa_create_button" title="Create and link to custom artifact" tabindex="400"></a>');
    asa_toolbar.append('<a href="#" id="asa_link_button" title="Link to existing custom artifact" tabindex="400"></a>');

    var updateToolbarButtonState = function(){
        if(!editor.getSelection().isEmpty()){
            $("#asa_create_button").removeClass('disabled');
            $("#asa_link_button").removeClass('disabled');
        }else{
            $("#asa_create_button").addClass('disabled');
            $("#asa_link_button").addClass('disabled');
        }
    };
    editor.getSession().selection.on('changeSelection', function(){
        updateToolbarButtonState();
    });
    updateToolbarButtonState();

    // Events for the custom toolbar buttons
    $("#asa_create_button").click(function() {
        editor.focus();
        if(!editor.getSelection().isEmpty()){
            createASAFormDialogFromUrl('Create Custom Artifact',  baseurl+"/artifact?action=new",
                { "Create": function() {
                    addAttributeOrderFields($("#artifact-form"));
                    submitASAFormDialog(
                        $(this),
                        {
                            success: function(data){
                                wrapSelection("[asa:"+data[0].resource_id+" ", "]");
                                var statesLength = editor.session.bgTokenizer.states.length;
                                editor.session.bgTokenizer.fireUpdateEvent(0,statesLength);
                                editor.session.bgTokenizer.start(0);
                            },
                            error: function(){
                                console.log("Invalid Artifact Create");
                            }
                        }
                    )}
                },
                {
                    open: function(){
                        addValue(this, "Name", editor.getCopyText());
                    }
                }
            ).dialog('open');
        }
        return false;
    });

    $("#asa_link_button").click(function() {
        if(!editor.getSelection().isEmpty()){
            link_to_existing_artifact_ajax_call(function() {
                var artifact_id = $('form#artifact-select input[name=selected]:checked').val();
                wrapSelection("[asa:"+artifact_id+" ", "]");
            }, "")
        }
        return false;
    });

};

var setupTokenizer = function(editor){
    var Tokenizer = require("ace/tokenizer").Tokenizer;
     // words in database
    var goodWords = Object.create(null);
    // words checked to not be in database. this can be omitted if it is ok to check for same words several times
    var words = Object.create(null);

    // cache for words pending resolution
    var pending = [];

    var tokenizer = new Tokenizer({
        "start": [
            {token : function(val){
               return "asa_artifact";
            }, regex : "\\[asa[:][0-9]+(?:[\\s+|\\.](?:[^\\]]+)?)?\\]"},
            {token : function(val){
                val = val.toLowerCase();
                if (goodWords[val])
                    return "keyword";
                if (words[val])
                    return "just-a-word";
                if (pending.indexOf(val) == -1)
                    pending.push(val);
                return "unknown";
            }, regex : "\\w+"},
            {token : "special_character", regex : "."},
            {token : "text", regex : "[^\\w]+"}


        ]
    });

    var queryTimeout = null;
    var dirtySessions = [];
    var attachToSession = function(session) {
        var self = session.bgTokenizer;
        self.rehighlight = function() {
            var states = this.states;
            var lines = this.lines;
            for (var i = states.length; i--;){
                if (states[i] || !lines[i])
                    continue;
                states[i] = "start";
                lines[i].forEach(function(t){
                    var term = t.value.toLowerCase();
                    if (goodWords[term])
                        t.type = "keyword";
                    else if (words[term])
                        t.type = "just-a-word";
                });
            }
            // this can be smarter and update only changed lines
            this.fireUpdateEvent(0, states.length);
        };
        self.$tokenizeRow = function(row) {
            // tokenize
            var line = this.doc.getLine(row);
            var data = this.tokenizer.getLineTokens(line, "start").tokens;
            // if we found new words schedule server query
            if (pending.length && !queryTimeout)
                queryTimeout = setTimeout(queryServer, 700);
            if (dirtySessions.indexOf(this) == -1)
                dirtySessions.push(this);
            // set state to null to indicate that it needs updating
            this.states[row] = null;
            return this.lines[row] = data;

        };
        self.setTokenizer(tokenizer);
    };


    var queryServer = function() {
        queryTimeout = null;
        Requests.searchArtifacts(undefined, {'': pending}, function(serverWords){
            // update goodWords and words based on serverWords
            goodWords = Object.create(null);
            for(var i=0;i<serverWords.length; i++){
                goodWords[serverWords[i].term.toLowerCase()] = true;
            }
            //goodWords = serverWords;
            words = Object.create(null);
            // then
            dirtySessions.forEach(function(x){
                x.rehighlight();
            });
            dirtySessions = [];
            // some code to reset queryTimeout
            // shedule again if there are more words in pending
            // etc...
            pending = [];
        })
    };

    /// use this instead of setMode
    attachToSession(editor.session);
};

var timeout;

var setupBalloons = function(editor){
    var balloon;
    var editordiv = $('#editor');

    editor.on('mousemove', function(e) {

        var canvasPos = editor.renderer.scroller.getBoundingClientRect();
        var position = e.getDocumentPosition();
        if (position.column == editor.session.getLine(position.row).length){
            // Likely hovering on the whitespace to the right of the end of the line
            // To be absolutely sure we'd need a textCoordinatesToScreen()
            clearTimeout(timeout);
            balloon && editordiv.hideBalloon();
            return;
        }
        var session = editor.session;
        var token = session.getTokenAt(position.row, position.column);

        if (token){
            if (token.type == 'keyword' || token.type == 'asa_artifact') {

                if(token!=null && timeout){
                    clearTimeout(timeout);
                }
                timeout = setTimeout(function(){
                    var screenPosition = editor.renderer.textToScreenCoordinates(position.row, token.start + token.value.length);
                    // 35: magic number for the expected width of the balloon.
                    balloon = editordiv.showBalloon(
                        {
                            position: "top left",
                            offsetX: screenPosition.pageX - $("#editor").offset().left + 35 + editor.renderer.characterWidth*2/3,
                            offsetY: canvasPos.top - screenPosition.pageY - editor.renderer.lineHeight*1.5,
                            tipSize: 0,
                            delay: 0,
                            minLifetime: 200,
                            showDuration: 300,
                            hideDuration: 100,
                            showAnimation: function(d) { this.fadeIn(d); },
                            contents: function(){
                                var content = $('<a href="#"></a>');
                                if (token.type == 'asa_artifact'){
                                    content.attr("id", "asa_view_button_tooltip");
                                    content.attr("title", "View Custom Artifact");
                                    content.click(function(){
                                        balloon && editordiv.hideBalloon();
                                        view_artifact_ajax_call(token.value, editor);
                                        return false;
                                    });
                                }else if (token.type == 'keyword'){
                                    content.attr("id", "asa_link_button_tooltip");
                                    content.attr("title", "Link to existing Custom Artifact");
                                    content.click(function(){
                                        balloon && editordiv.hideBalloon();
                                        link_to_existing_artifact_ajax_call(function() {
                                            var artifact_id = $('form#artifact-select input[name=selected]:checked').val();
                                            editor.session.insert({row: position.row, column: token.start + token.value.length}, "]");
                                            editor.session.insert({row: position.row, column: token.start}, "[asa:"+artifact_id+" ");
                                            editor.focus();
                                        }, token.value);
                                        return false;
                                    });
                                }
                                return content;
                            }
                        }
                    ).data("balloon");
                },1000);
                if(balloon) {
                    balloon.mouseleave(function(e) {
                        clearTimeout(timeout);
                        editordiv.hideBalloon();
                    }).mouseenter(function(e) {
                        clearTimeout(timeout);
                    });
                }
            }else{
                clearTimeout(timeout);
                balloon && editordiv.hideBalloon();
            }
            e.stop();
        }else{
            clearTimeout(timeout);
        }
    });
};

var timeout_pages;
var setupListing = function(editor){
    $('fieldset#changeinfo').css('width', '56%');
    $('fieldset#changeinfo').css('min-width', '56%');
    $('fieldset#changeinfo').css('float', 'left');
    $('form#edit .buttons').css('float', 'left');
    $('#comment').css('width', '98%');
    var height_box = $('fieldset#changeinfo').height();
    $('#changeinfo').after('<fieldset id="listing"/>');
    $('fieldset#listing').css('float', 'right');
    $('fieldset#listing').css('width', '39%');
    $('fieldset#listing').css('min-height', height_box);
    $('fieldset#listing').css('height', 'auto');
    $('fieldset#listing').html('<legend>Pages that refer the same Custom Artifacts</legend>' +
        '<div id="equivalent_pages_list" class="search"><dl class="related"></dl></div>' );

    addRelatedPages(editor);

    editor.on('change', function(){
        clearTimeout(timeout_pages);
        timeout_pages = setTimeout(function(){
            addRelatedPages(editor);
        }, 500);
    });

}

function addRelatedPages(editor){
    var text = editor.session.getValue();
    var regex = /\[(asa):[0-9]+\s+[^[]+\]/g;
    var artifacts=  text.match(regex);
    var artifacts_by_id = new Array();
    var counter =0;
    if(artifacts!=null){
        for (var i=0;i<artifacts.length; i++){
            var asa_token_content = artifacts[i];
            var id = asa_token_content.match(/\d+/g);
            if(artifacts_by_id.indexOf(id[0])==-1){
                artifacts_by_id[counter] = id[0];
                counter++;
            }
        }
    }
    Requests.searchRelatedPages(artifacts_by_id, function(data){

        $('#equivalent_pages_list dl.related').empty();
        if(data.length==0){
            $('#equivalent_pages_list dl.related').append('<dt>'+'No pages were found'+'</dt>');
        }
        for(var i=0;i<data.length;i++){
            if(data[i].results.length>0){
                var artifact_search = $('#equivalent_pages_list dl.related').append('<dt><a class="asa-link" href="' + data[i].href + '">'+data[i].title+'</a></dt>');
                addResultRow(data[i].results, artifact_search);
            }
        }

    }, function(data){
        $('#equivalent_pages_list').empty();
        $('#equivalent_pages_list').append('<dt>'+'Error in search'+'</dt>');
    })
}

function addResultRow(results, artifact_search){
    for(i = 0 ; i< results.length; i++){
        var result = results[i];
        $('#equivalent_pages_list dl.related').append('' +
            '<dd style="margin-top:0.2em"><a class="wiki" href="'+result.href+'">'+result.title+'</a></dd>' +
            '<dd>' +
                '<span class="author">By '+result.author+'</span> &mdash; ' +
                '<span class="date">'+result.date+'</span>' +
            '</dd>');
    }
}

(function() {
    var ev = new $.Event('classremoved');
    var orig = $.fn.removeClass;
    $.fn.removeClass = function() {
        var result = orig.apply(this, arguments);
        $(this).trigger(ev, arguments);
        return result;
    }
})();

$(document).ready(function(){
    var editor = setupEditor();
    setupToolbar(editor);
    setupTokenizer(editor);
    setupBalloons(editor);
    setupListing(editor);
});