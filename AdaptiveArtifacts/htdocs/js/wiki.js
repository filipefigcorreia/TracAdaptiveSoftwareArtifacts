$(document).ready(function(){

    // Hide trac's textarea and show a contenteditable div in its place
    var textarea = $('#text');
    textarea.hide().before('<div id="editor"/>').before('<span class="buuu">Lorem ipsum</span>'); //.before('<div>Lorem <span class="ace_keyword">teste</span> ipsum <span class="ace_keyword">teste 2</span> lorem.</div>');

    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/trac_wiki");
    //editor.getSession().setMode("ace/mode/javascript");
    editor.getSession().setUseWrapMode(true);
    editor.setHighlightActiveLine(false);
    editor.setShowPrintMargin(false);
    editor.renderer.setShowGutter(false);

    editor.getSession().setValue(textarea.val());
    editor.getSession().on('change', function(){
      textarea.val(editor.getSession().getValue());
    });

    var Tokenizer = require("ace/tokenizer").Tokenizer;
     // words in database
    var goodWords = Object.create(null);
    // words checked to not be in datebase. this can be omitted if it is ok to check for same words several times
    var words = Object.create(null);

    // cache for words pending resolution
    var pending = []

    var tokenizer = new Tokenizer({
        "start": [
            {token : function(val){
                if (goodWords[val])
                    return "keyword"
                if (words[val])
                    return "just-a-word"
                if (pending.indexOf(val) == -1)
                    pending.push(val)
                return "unknown"
            }, regex : "\\w+"},
            {token : "text", regex : "[^\\w]+"}
        ]
    });

    var queryTimeout = null
    dirtySessions = []
    attachToSession = function(session) {
        var self = session.bgTokenizer;
        self.rehighlight = function() {
            var states = this.states;
            var lines = this.lines;
            for (var i = states.length; i--;){
                if (states[i] || !lines[i])
                    continue;
                states[i] = "start";
                lines[i].forEach(function(t){
                    if (goodWords[t.value])
                        t.type = "keyword";
                    else if (words[t.value])
                        t.type = "just-a-word";
                })
            }
            // this can be smarter and update only changed lines
            this.fireUpdateEvent(0, states.length)
        }
        self.$tokenizeRow = function(row) {
            // tokenize
            var line = this.doc.getLine(row);
            var data = this.tokenizer.getLineTokens(line, "start").tokens;
            // if we found new words schedule server query
            if (pending.length && !queryTimeout)
                queryTimeout = setTimeout(queryServer, 700)
            if (dirtySessions.indexOf(this) == -1)
                dirtySessions.push(this)
            // set state to null to indicate that it needs updating
            this.states[row] = null

            return this.lines[row] = data;
        }
        self.setTokenizer(tokenizer)
    }
    queryServer = function() {
        fetchData(pending, function(serverWords){
            // update goodWords and words based on serverWords
            goodWords = serverWords
            words = []
            // then
            dirtySessions.forEach(function(x){
                x.rehighlight()
            })
            dirtySessions = []
            // some code to reset queryTimeout
            // shedule again if there are more words in pending
            // etc...
            pending = []
        })
    }

    fetchData = function(needles, f) {
        f({'trac':true, 'simply':true});
    }

    /// use this instead of setMode
    attachToSession(editor.session);



    // Initially a copy of trac/htdocs/js/resizer.js
    // Allow resizing <textarea> elements through a drag bar
    setupEditorResizing = function(editor, editordiv) {
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
      }
      setupEditorResizing(editor, $('#editor'));



    /*
    var TokenIterator = require("ace/token_iterator").TokenIterator;
    var iterator = new TokenIterator(editor.getSession(), 0, 0);
    var token = iterator.getCurrentToken();
    while (token){
        console.log(token.type);
        console.log(token.value);
        if (token.type == 'keyword'){
            var xpto = 1;
            token.balloon({
                  position: 'right',
                  contents: '<img src="../media/loading.gif" alt="loading..." width="25" height="25" />',
                  url: baseurl+'/adaptiveartifacts/artifact?action=new&format=dialog',
                  ajaxComplete: function(res, sts, xhr) { alert(sts); }
                });
        }
        token = iterator.stepForward();
    }
    */


    var balloon;
    editor.on('mousemove', function(e) {
            var position = e.getDocumentPosition();
            var session = editor.session;

            // If the user clicked on a fold, then expand it.
            var token = session.getTokenAt(position.row, position.column, 1);
            if (token){
                var canvasPos = editor.renderer.scroller.getBoundingClientRect();
                var editordiv = $('#editor');
                if (token.type == 'keyword') {
                    balloon = editordiv.showBalloon(
                        {
                            position: "top left",
                            offsetX: e.clientX - canvasPos.left,
                            offsetY: canvasPos.top - e.clientY + 10,
                            tipSize: 20,
                            delay: 500,
                            minLifetime: 500,
                            showDuration: 1000,
                            hideDuration: 200,
                            showAnimation: function(d) { this.fadeIn(d); },
                            contents: token.value
                        }
                    ).mouseenter(function(e) {
                            editordiv.showBalloon();
                        }).data("balloon");
                    if(balloon) {
                        balloon.mouseleave(function(e) {
                            editordiv.hideBalloon();
                        }).mouseenter(function(e) { editordiv.showBalloon(); });
                    }
                }else{
                    balloon && editordiv.hideBalloon();
                }
                e.stop();
            }
        });

/*

      */

    /*
    editor.getSession().on('change', function(){
        $('.ace_keyword').mouseup(function(){
            alert("Bam!");
        });
    });
    */

                 /*
        var kws = $(".buuu");
        var cenas = {
                    position: 'right',
                    contents: '<img src="../media/loading.gif" alt="loading..." width="25" height="25" />',
                    url: baseurl+'/adaptiveartifacts/artifact?action=new&format=dialog',
                    ajaxComplete: function(res, sts, xhr) { alert(sts); }
                  };
        kws.balloon(cenas);
        */

    /*
        //$(".buuu").click(function(e){
    console.log("aaa");
    var bl = $(".buuu").showBalloon(
                {
                    position: "left",
                    offsetX: 50,
                    offsetY: 50,
                    tipSize: 20,
                    css: {
                        maxWidth: "17em",
                        border: "solid 5px #463974",
                        color: "#463974",
                        fontWeight: "bold",
                        fontSize: "130%",
                        backgroundColor: "#efefef"
                    },
                    contents: "cenas"
                }
            );
    bl.toggle(
        function(){ $(this).hideBalloon(); },
        function(){ $(this).showBalloon(); }
      );

        //});
*/

/*
    var net = require("ace/lib/net");
    var Range = require("ace/range").Range;
    var util = require("ace/demo/kitchen-sink/util");
    var layout = require("ace/demo/kitchen-sink/layout");
    var modelist = require("ace/demo/kitchen-sink/modelist");
    var doclist = require("ace/demo/kitchen-sink/doclist");
    var TokenTooltip = require("ace/demo/kitchen-sink/token_tooltip").TokenTooltip;
    */

    //var ttt = new TokenTooltip(editor);

    /*
    var states = editor.session.bgTokenizer.states;
    var lines = editor.session.bgTokenizer.lines;
    for (var i = states.length; i--;){
        if (!lines[i])
            continue;
        lines[i].forEach(function(t){
            console.log(t.type);
            console.log(t.value);
        })
    }
    */

    /*$('.ace_keyword').balloon({
      position: 'right',
      contents: '<img src="../media/loading.gif" alt="loading..." width="25" height="25" />',
      url: baseurl+'/adaptiveartifacts/artifact?action=new&format=dialog',
      ajaxComplete: function(res, sts, xhr) { alert(sts); }
    });*/
});