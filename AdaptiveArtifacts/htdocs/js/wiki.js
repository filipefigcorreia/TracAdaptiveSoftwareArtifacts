var Ranges = new Array();
var searchResultApplier ;

//Converter o array de ranges, depois de feito o split, para strings (toString() devolve-nos o texto de cada range)
//Enviar array final por POST para o server
//Tratar json recebido e retirar palavras selecionadas, fazer match com o array de ranges, e utilizar os ranges selecionados

var words_array = new Array("database", "extra", "simply", "TracEnvironment", "trac");

function highlightRanges(ranges) {
    for (var i = ranges.length - 1; i >= 0; i--) {
        if ((words_array.indexOf(ranges[i].text())) != -1) {
            searchResultApplier.applyToRange(ranges[i]);
        }else {
            //TODO: retirar span no caso de estarmos dentro de um
            if (searchResultApplier.isAppliedToRange(ranges[i]))
                searchResultApplier.undoToRange(ranges[i]);
        }
    }
    holdCluetipOnElement( $("span.divtext_selected_word") );
}

function splitRange(fullRange) {
    var fullRangeText = fullRange.text().split('\n').join(' ');

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

    $('.wikitoolbar')[0].setAttribute('style', 'width:260px');
    $('.wikitoolbar').append('<a href="#" id="asaselect" title="Create artifact through selection" tabindex="400"></a>');


    rangy.init();
    searchResultApplier = rangy.createCssClassApplier("divtext_selected_word",
        {
            ignoreWhiteSpace: true,
            elementTagName: "span"
            /*elementProperties: {
                href: "#",
                onclick: function() {
                    var highlight = highlighter.getHighlightForElement(this);
                    if (window.confirm("Delete this note (ID " + highlight.id + ")?")) {
                        highlighter.removeHighlights( [highlight] );
                    }
                    return false;
                }
            }*/
        });

    var fullRange = rangy.createRange();
    fullRange.selectNodeContents(document.getElementById("divtext").childNodes[0]);
    var splittedRanges = splitRange(fullRange);
    highlightRanges(splittedRanges);


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

    $("#asaselect").click(function() {
        //changeTagOnSelectedString("[[Image(", ")]]");
        if(!rangy.getSelection().getRangeAt(0).collapsed){
            createASAFormDialogFromUrl('Artifact',  "/trac/adaptiveartifacts/artifact?action=new",
                { "Create": function() {
                    submitASAFormDialog(
                        $(this),
                        {
                            success: function(){
                                console.log("Sucesso!");
                                //console.log(rangy.getSelection().getRangeAt(0));
                            },
                            error: function(){
                                    alert("Falhaaaaa!!");
                            }
                        }
                    )}
                }


            ).dialog('open');
        }
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

        var newRange = rangy.getSelection().getRangeAt(0);

        var oldRange = Ranges[Ranges.length-1];
        if(oldRange &&
              oldRange.endContainer == newRange.startContainer &&
                oldRange.endOffset >= newRange.startOffset-3){
            if (newRange.endOffset > Ranges[Ranges.length-1].endOffset){
                Ranges[Ranges.length-1].setEnd(newRange.endContainer, newRange.endOffset);
                console.log("Atualizei o seguinte: ");
                console.log( (Ranges[Ranges.length-1]).text());
            }
        }else{
            console.log("Comecei o seguinte: ");
            console.log(newRange.text());
            Ranges.push(newRange);
        }
        reloadSearch();
    });

    $("#cluetip").bind('click', function() {
        createASAFormDialogFromUrl('Artifact',  "/trac/adaptiveartifacts/artifact?action=new",
            { "Create": function() { submitASAFormDialog($(this)) } }
        ).dialog('open');
    });

    function reloadSearch() {
        //Memory Leak alert!
        if (!isLoading) {
            timeout = setTimeout(function() {
                try {
                    isLoading = true;
                    //Analise da pagina
                    var selection1 = rangy.saveSelection(window);

                    var i = 0;
                    var splittedRanges = [];
                    while (Ranges.length>0) {

                        var fullRange = Ranges.shift();
                        console.log("Consumi o seguinte: ");
                        console.log(fullRange.text());
                        var ranges = splitRange(fullRange);
                        $.merge(splittedRanges, ranges);
                    }
                    highlightRanges(splittedRanges);
                    rangy.restoreSelection(selection1);
                    //Fim da analise
                }
                catch(exception){
                    console.log("Exception while processing queue:");
                    console.log(exception);
                }
                finally {
                    isLoading = false;
                }
            }, delay);
        }
        else {
            console.log("Still loading last search!");
        }
    }

    /*$('#divtext').bind('click', function() {

    });*/
});


function changeTagOnSelectedString(prefix, sufix){
    var firstRange = rangy.getSelection().getRangeAt(0);
    if(!firstRange.collapsed){
        var ret = firstRange.cloneContents();
        var html = prefix + ret.textContent + sufix;
        insertHtmlAfterSelection(html);
        var currentRange = rangy.getSelection().getRangeAt(0);
        currentRange.setStart(currentRange.startContainer, currentRange.startOffset-html.length);
        var splittedRanges = splitRange(currentRange);
        highlightRanges(splittedRanges);
    }
};

//Sera mesmo necessario? Substituir pelo rangy
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

function holdCluetipOnElement(JQueryElement){
    JQueryElement.cluetip({arrows: true,width: 50, local:false,
        closeText:'',
        mouseOutClose: true,
        sticky: true,
        hoverClass:'span.divtext_selected_word',
        onShow:   function(){
            $(this).mouseout(function() {     // if I go out of the link, then...
                var closing = setTimeout(" $(document).trigger('hideCluetip')",400);  // close the tip after 400ms
                $("#cluetip").mouseover(function() { clearTimeout(closing); } );    // unless I got inside the cluetip
            });
        },
        splitTitle: '|',
        cursor: 'text',
        cluetipClass: 'rounded',
        showTitle: false});
}
