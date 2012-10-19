var serializedHighlights = decodeURIComponent(window.location.search.slice(window.location.search.indexOf("=") + 1));
var highlighter;

var initialDoc;
var Ranges = new Array();
var Selections = new Array();
var searchResultApplier ;
var words_array = new Array("database", "extra", "simply", "TracEnvironment", "trac");


function highlightRanges(ranges) {
    for (var i = ranges.length - 1; i >= 0; i--) {
        if ((words_array.indexOf(ranges[i].toString())) != -1) {
            searchResultApplier.applyToRange(ranges[i]);
        } else {
            //TODO: retirar span no caso de estarmos dentro de um

            if (searchResultApplier.isAppliedToRange(ranges[i]))
                searchResultApplier.undoToRange(ranges[i]);

        }
    }
}
window.onload = function() {
    rangy.init();

    searchResultApplier = rangy.createCssClassApplier("divtext_selected_word");

    highlighter = rangy.createHighlighter();

    highlighter.addCssClassApplier(rangy.createCssClassApplier("highlight", {
        ignoreWhiteSpace: true,
        tagNames: ["span", "a"]
    }));

    highlighter.addCssClassApplier(rangy.createCssClassApplier("note", {
        ignoreWhiteSpace: true,
        elementTagName: "a",
        elementProperties: {
            href: "#",
            onclick: function() {
                var highlight = highlighter.getHighlightForElement(this);
                if (window.confirm("Delete this note (ID " + highlight.id + ")?")) {
                    highlighter.removeHighlights( [highlight] );
                }
                return false;
            }
        }
    }));

    var fullRange = rangy.createRange();
    fullRange.selectNodeContents(document.getElementById("divtext").childNodes[0]);
    var splittedRanges = splitRange(fullRange);
    highlightRanges(splittedRanges);
};


function splitRange(fullRange) {
    var fullRangeText = fullRange.toString().split('\n').join(' ');

    var start = 0;
    var idx = 0;
    var splittedRanges = [];
    while (idx != -1) {
        idx = fullRangeText.indexOf(' ', start);
        var end;
        if (idx != -1)
            end = idx;
        else
            end = fullRangeText.length;
        var splittedRange = rangy.createRange();

        splittedRange.setStart(fullRange.startContainer, fullRange.startOffset + start);
        splittedRange.setEnd(fullRange.endContainer, fullRange.startOffset + end);
        splittedRange.expand('word', {includeTrailingSpace:false});
        splittedRanges.push(splittedRange);
        start = idx + 1;
    }
    return splittedRanges;
}
$(document).ready(function(){

    //Hide TextArea and show Div
    $('#text').hide().before('<div id="divtext" contenteditable="true"/>' );
    $('#divtext').text ( $('#text').val());

    //Analyze the text content and create spans
    var text = $('#divtext');


    /*var counter = 0;
    while(counter<words_array.length){
        var reg=new RegExp(words_array[counter], "g");
        var subst =  "<span class='.divtext_selected_word' style='color:red'>" + words_array[counter] +  "</span>";
        text.html( text.html().replace(reg, subst)) ;
        counter++;
    }*/





    $("#strong").click(function() {
        changeTagOnSelectedString("'''", "'''");
    });

    $("#heading").click(function() {
        changeTagOnSelectedString("\n== ", " ==\n");
    });

    $("#em").click(function() {
        changeTagOnSelectedString("''", "''");
    });

    $("#link").click(function() {
        changeTagOnSelectedString("[", "]");
    });

    $("#code").click(function() {
        changeTagOnSelectedString("\n{{{\n", "\n}}}\n");
    });

    $("#hr").click(function() {
        changeTagOnSelectedString("\n----\n", "");
    });

    $("#np").click(function() {
        changeTagOnSelectedString("\n\n", "");
    });

    $("#br").click(function() {
        changeTagOnSelectedString("[[BR]]\n", "");
    });

    $("#img").click(function() {
        changeTagOnSelectedString("[[Image(", ")]]");
    });

    setInterval(function(){
        $('#text').val( $('#divtext').text()  );
    },100);

    var timeout;
    var delay = 500;
    var isLoading = false;

    jQuery(document).bind('keydown', function (evt){
            if (event.which == 13) {
                evt.preventDefault();
                //var enterRange = rangy.getSelection().getRangeAt(0);
                insertHtmlAfterSelection('\n');
                return true;
            }
        }
    );


    $('#divtext').keyup(function(event) {


        if (timeout) {
            clearTimeout(timeout);
        }

        //var newRange = rangy.createRange();
        //newRange.selectNodeContents(document.getElementsByClassName("divtext")[0]);

        var newRange = rangy.getSelection().getRangeAt(0);

        var oldRange = Ranges[Ranges.length-1];
        if(oldRange && oldRange.endContainer == newRange.startContainer && oldRange.endOffset >= newRange.startOffset-3){
            Ranges[Ranges.length-1].setEnd(newRange.endContainer, newRange.endOffset);
            console.log("Atualizei o seguinte: ");
            console.log( (Ranges[Ranges.length-1]).toString());
        }else{
            console.log("Comecei o seguinte: ");
            console.log(newRange.toString());
            Ranges.push(newRange);
        }
        //console.log(Ranges[0].cloneRange());
        //console.log(Ranges[0].toString());

        reloadSearch();

    });


    function reloadSearch() {
        //Memory Leak alert!
        if (!isLoading) {

            timeout = setTimeout(function() {

                isLoading = true;
                //Analise da pagina
                var selection1 = rangy.saveSelection(window);


                var i = 0;
                var splittedRanges = [];
                while (Ranges.length>0) {

                    var fullRange = Ranges.shift();
                    console.log("Consumi o seguinte: ");
                    console.log(fullRange.toString());
                    var ranges = splitRange(fullRange);
                    $.merge(splittedRanges, ranges);
                }
                highlightRanges(splittedRanges);

                //
                rangy.restoreSelection(selection1);
                //Fim da analise

                // Simulate a real ajax call
                setTimeout(function() { isLoading = false; }, 500);
            }, delay);

        }
        else {
            console.log("Still loading last search!");
        }
    }

    /*$('#divtext').bind('click', function() {



        var searchScopeRange = rangy.createRange();
        searchScopeRange.selectNodeContents(document.getElementById("divtext"));

        console.log(searchScopeRange);


    });*/


});



function changeTagOnSelectedString(prefix, sufix){
    var text = $('#divtext');
    var selection = text.selection();
    var width = selection.width;

    if(width!=0){

        var content = text.text();
        //alert(content);
        var start = selection.start;
        var end = selection.end;

        var selected  = content.substring(start, end);

        var subst =  prefix + selected + sufix;
        text.text( text.text().substring(0, start) + subst + text.text().substring(end) );
    }
};


function insertHtmlAfterSelection(html) {
    var sel, range;
    if (window.getSelection) {
        // IE9 and non-IE
        sel = window.getSelection();
        if (sel.getRangeAt && sel.rangeCount) {
            range = sel.getRangeAt(0);
            range.deleteContents();

            // Range.createContextualFragment() would be useful here but is
            // non-standard and not supported in all browsers (IE9, for one)
            var el = document.createElement("div");
            el.innerHTML = html;
            var frag = document.createDocumentFragment(), node, lastNode;
            while ( (node = el.firstChild) ) {
                lastNode = frag.appendChild(node);
            }
            range.insertNode(frag);

            // Preserve the selection
            if (lastNode) {
                range = range.cloneRange();
                range.setStartAfter(lastNode);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
            }
        }
    } else if (document.selection && document.selection.type != "Control") {
        // IE < 9
        document.selection.createRange().pasteHTML(html);
    }
}