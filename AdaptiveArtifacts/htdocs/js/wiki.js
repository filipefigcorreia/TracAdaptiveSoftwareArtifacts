function view_artifact_ajax_call(asa_token_content, editor){
    var ind_init = asa_token_content.indexOf(":");
    var sub = asa_token_content.substr(ind_init+1, asa_token_content.length);
    var ind_end = sub.indexOf(" ");
    var id = sub.substr(0, ind_end);

    createASAFormDialogFromUrl('View Adaptive Artifact', baseurl+"/artifact/"+id+"?action=view",
        {
            "Edit": function() {
                $(this).dialog("close");
                createASAFormDialogFromUrl('Artifact', baseurl+"/artifact/"+id+"?action=edit",
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
                                    },
                                    error: function(data){
                                        console.log("Ajax call failed!");
                                    }
                                }
                            )},
                        "Close": function() { $(this).dialog("close"); }
                    }
                ).dialog('open');
            },
            "Close": function() { $(this).dialog("close"); } }
    ).dialog('open');
}

function link_to_existing_artifact_ajax_call(click_callback, value){
    createASAFormDialogFromUrl('Select Adaptive Artifact',  baseurl+"/search/by_filter?",
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
                    var content_div = $(".artifacts #asa #dialog-content");
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
                    copy.find("td")[1].innerText = spec_name;
                    copy.find("td")[2].innerText = title;
                    $(".artifacts table.listing tbody").append(copy);
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
                                addMessageRow('No Adaptive Artifacts found');
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
    var textarea = $('#text');
    textarea.hide().before('<div id="editor"/>');

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

        var grip = $('.trac-grip').mousedown(beginDrag)[0];
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
        $('#editor').height(this.options[this.selectedIndex].value * $("div.ace_gutter-layer").find(".ace_gutter-cell:first").height())
        editor.renderer.onResize(true);
    });

    return editor;
};

var setupToolbar = function(editor){
    var wrapSelection = function(prefix, sufix){
        var value = editor.getCopyText();
        editor.insert(prefix + value + sufix);
        editor.focus();
    };

    // Rewire the event handlers of the toolbat buttons to work with the div instead of the textarea
    $("#strong").click(function() {
        wrapSelection("'''", "'''");
    });

    $("#heading").click(function() {
        wrapSelection("\n== ", " ==\n");
    });

    $("#em").click(function() {
        wrapSelection("''", "''");
    });

    $("#link").click(function() {
        wrapSelection("[", "]");
    });

    $("#code").click(function() {
        wrapSelection("\n{{{\n", "\n}}}\n");
    });

    $("#hr").click(function() {
        wrapSelection("\n----\n", "");
    });

    $("#np").click(function() {
        wrapSelection("\n\n", "");
    });

    $("#br").click(function() {
        wrapSelection("[[BR]]\n", "");
    });

    $("#img").click(function() {
        wrapSelection("[[Image(", ")]]");
    });

    // Add custom buttons to the toolbar
    var toolbar = $('.wikitoolbar');

    toolbar.after('<div class="wikitoolbar" id="asa_toolbar"></div>');
    var asa_toolbar = $('#asa_toolbar');
    asa_toolbar.append('<a href="#" id="asa_create_button" title="Create and link to artifact" tabindex="400"></a>');
    asa_toolbar.append('<a href="#" id="asa_link_button" title="Link to existing artifact" tabindex="400"></a>');

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
            createASAFormDialogFromUrl('Create Adaptive Artifact',  baseurl+"/artifact?action=new",
                { "Create": function() {
                    addAttributeOrderFields($("#artifact-form"));
                    submitASAFormDialog(
                        $(this),
                        {
                            success: function(data){
                                wrapSelection("[asa:"+data[0].resource_id+" ", "]");
                                var statesLength = editor.session.bgTokenizer.states.length;
                                /*var i=0;
                                 while ( i  < statesLength){
                                 editor.session.bgTokenizer.states[i] = null;
                                 i++;
                                 }*/
                                editor.session.bgTokenizer.fireUpdateEvent(0,statesLength);
                                editor.session.bgTokenizer.start(0);
                            },
                            error: function(data){
                                console.log("Ajax call failed!");
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
    });

    $("#asa_link_button").click(function() {
        if(!editor.getSelection().isEmpty()){
            link_to_existing_artifact_ajax_call(function() {
                var artifact_id = $('form#artifact-select input[name=selected]:checked').val();
                wrapSelection("[asa:"+artifact_id+" ", "]");
            }, "")
        }
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
            {token : "asa_artifact", regex : ".\[asa:[0-9]+\\s+[\\s\\w]+\]"},
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

var setupBalloons = function(editor){
    var balloon;
    editor.on('mousemove', function(e) {
        var canvasPos = editor.renderer.scroller.getBoundingClientRect();
        // Originally adapted from the code of screenToTextCoordinates()
        // Accounts for whitespace columns on the end of lines.
        var position = {
            row:e.getDocumentPosition().row ,
            column: Math.round((e.clientX + editor.renderer.scrollLeft - canvasPos.left - editor.renderer.$padding) / editor.renderer.characterWidth)};
        var session = editor.session;

        //Testes para ajustar posicionamento do balao
        //console.log("Janela: "+ editor.offsetLeft+ "   "+editor.offsetTop);
        //console.log(position.row+"      " +position.column ) ;
        //var range = editor.session.getAWordRange(position.row, position.column);
        //console.log(range.start);
        //console.log(range.toScreenRange(editor.session).start);
        //range.end.column-position.column


        // If the user clicked on a fold, then expand it.
        var token = session.getTokenAt(position.row, position.column, 1);
        if (token){

            var editordiv = $('#editor');
            var tooltip_content;
            if (token.type == 'keyword' || token.type == 'asa_artifact') {
               /* console.log("Aqui: ");
                console.log(session.getTabSize());

                console.log("Old");
                console.log(e.clientX);*/

                balloon = editordiv.showBalloon(
                    {
                        position: "top left",
                        offsetX: e.clientX - canvasPos.left ,
                        offsetY: canvasPos.top - e.clientY + 10,
                        tipSize: 10,
                        delay: 500,
                        minLifetime: 500,
                        showDuration: 1000,
                        hideDuration: 200,
                        showAnimation: function(d) { this.fadeIn(d); },
                        contents: function(){
                            var content = $('<a href="#"></a>');
                            if (token.type == 'asa_artifact'){
                                content.attr("id", "asa_view_button_tooltip");
                                content.attr("title", "View Adaptive Artifact");
                                content.click(function(){ view_artifact_ajax_call(token.value, editor)});
                            }else if (token.type == 'keyword'){
                                content.attr("id", "asa_link_button_tooltip");
                                content.attr("title", "Link to existing Adaptive Artifact");
                                content.click(function(){
                                    link_to_existing_artifact_ajax_call(function() {
                                        var artifact_id = $('form#artifact-select input[name=selected]:checked').val();
                                        editor.session.insert({row: position.row, column: token.start + token.value.length}, "]");
                                        editor.session.insert({row: position.row, column: token.start}, "[asa:"+artifact_id+" ");
                                        editor.focus();
                                    }, token.value)
                                });
                            }
                            return content;
                        }
                    }
                ).data("balloon");

                if(balloon) {
                    balloon.mouseleave(function(e) {
                        editordiv.hideBalloon();
                    }).mouseenter(function(e) {
                        editordiv.showBalloon();
                    });
                }

            }else{
                balloon && editordiv.hideBalloon();
            }
            e.stop();
        }
    });
};

$(document).ready(function(){
    var editor = setupEditor();
    setupToolbar(editor);
    setupTokenizer(editor);
    setupBalloons(editor);
});