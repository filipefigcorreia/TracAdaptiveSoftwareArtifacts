var setupEditor = function() {
    // Hide trac's textarea and show a contenteditable div in its place
    var textarea = $('#text');
    textarea.hide().before('<div id="editor"/>');

    var editor = ace.edit("editor");
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
        editordiv.wrap('<div class="trac-resizable"><div></div></div>')
                .parent().append(grip);
        grip.style.marginLeft = (this.offsetLeft - grip.offsetLeft) + 'px';
        grip.style.marginRight = (grip.offsetWidth - this.offsetWidth) +'px';
    };
    setupEditorResizing(editor, $('#editor'));

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
    asa_toolbar.append('<a href="#" id="asa_create_button" title="Create Adaptive Artifact with text selection" tabindex="400"></a>');
    asa_toolbar.append('<a href="#" id="asa_link_button" title="Link text selection to existing Adaptive Artifact" tabindex="400"></a>');

    // Events for the custom toolbar buttons
    $("#asa_create_button").click(function() {
        editor.focus();
        if(!editor.getSelection().isEmpty()){
            createASAFormDialogFromUrl('Create Adaptive Artifact',  baseurl+"/artifact?action=new",
                { "Create": function() {
                    submitASAFormDialog(
                        $(this),
                        {
                            success: function(data){
                                wrapSelection("[asa:"+data[0].resource_id+" ", "]");
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
            {token : "asa_artifact", regex : ".\[asa:[0-9]+\\s+\\w+\]"},
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
        Requests.searchArtifacts(pending, function(serverWords){
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
            var position = e.getDocumentPosition();
            var session = editor.session;

            // If the user clicked on a fold, then expand it.
            var token = session.getTokenAt(position.row, position.column, 1);
            if (token){
                var canvasPos = editor.renderer.scroller.getBoundingClientRect();
                var editordiv = $('#editor');
                var tooltip_content;
                if (token.type == 'keyword' || token.type == 'asa_artifact') {
                   /* console.log("Aqui: ");
                    console.log(session.getTabSize());

                    console.log("Old");
                    console.log(e.clientX);*/

                    if (token.type == 'asa_artifact'){
                        var token_content = token.value;
                        tooltip_content = "<a href=\"javascript:view_artifact_ajax_call('" + token_content + "');\" id='asa_view_button_tooltip' title='View Adaptive Artifact' ></a>";
                    }else if (token.type == 'keyword')
                        tooltip_content = '<a href="javascript:link_to_existing_artifact_ajax_call();" id="asa_link_button_tooltip" title="Link to existing Adaptive Artifact" ></a>';

                    balloon = editordiv.showBalloon(
                        {
                            position: "top left",
                            offsetX: e.clientX - canvasPos.left,
                            offsetY: canvasPos.top - e.clientY + 10,
                            tipSize: 10,
                            delay: 500,
                            minLifetime: 500,
                            showDuration: 1000,
                            hideDuration: 200,
                            showAnimation: function(d) { this.fadeIn(d); },
                            contents: tooltip_content

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

function view_artifact_ajax_call(asa_token_content){

    var ind_init = asa_token_content.indexOf(":");
    var sub = asa_token_content.substr(ind_init+1, asa_token_content.length);
    var ind_end = sub.indexOf(" ");
    var id = sub.substr(0, ind_end);

    createASAFormDialogFromUrl('View Adaptive Artifact', baseurl+"/artifact/"+id+"?action=view",
        { "Close": function() { $(this).dialog("close"); } }
    ).dialog('open');
}

function link_to_existing_artifact_ajax_call(){
    //This is not the right window to call in this context... waiting for link artifact window to be ready!!!!
    createASAFormDialogFromUrl('Create Adaptive Artifact',  baseurl+"/artifact?action=new",
        { "Create": function() {
            submitASAFormDialog(
                $(this),
                {
                    success: function(data){
                        console.log("Success!");
                    },
                    error: function(data){
                        console.log("Failure!!");
                    }
                }
            )}
        }/*,
        {
            open: function(){
                addValue(this, "Name", editor.getCopyText());
            }
        }*/
    ).dialog('open');
}

$(document).ready(function(){
    var editor = setupEditor();
    setupToolbar(editor);
    setupTokenizer(editor);
    setupBalloons(editor);
});