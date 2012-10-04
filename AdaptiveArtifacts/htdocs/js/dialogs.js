$(document).ready(function(){
    $('.opendialog.newartifact').click( function() { showCreateArtifactDialog() });
});

showCreateArtifactDialog = function(){
    createASADialogFromUrl(
            "/my-trac-environment/adaptiveartifacts/artifact?action=new&format=dialog",
            {
                title: 'Artifact',
                success: function(data, textStatus, jqXHR) { attachFormEventHandlers($(this)) },
                buttons: { "Create": function() { submitDialogForm($(this)) } }
            }
        ).dialog('open');
}

/*
Submits a jquery-ui dialog. The dialog is closed if
submission goes flawlessly, and shows an error message
otherwise.
 */
submitDialogForm = function(dialogdiv) {
    var form=dialogdiv.find('form');
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        context: dialogdiv, //so that we can call $(this) on the success and error callbacks
        success: function(data){
            $(this).dialog("close");
            $(this).dialog("destroy");
            $(this).remove();
        },
        error: function(data){
            $(this).html("An error occurred, sorry.");
            $(this).dialog("option", "buttons", [
                {
                    text: "Close",
                    click: function() {
                        $(this).dialog("close");
                        $(this).dialog("destroy");
                        $(this).remove();
                    }
                }
            ] );
        }
    });
}

function createASADialogFromUrl(url, options){
    var dialogdiv = createDialogFromUrl(url, options, 'asa-dialog');
    $('<input>').attr({
        type: 'hidden',
        name: 'format',
        value: 'dialog'
    }).appendTo(dialogdiv.find('form'));
    return dialogdiv;
}

function createDialogFromUrl(url, options, dialogdivclass){
  options = options || {};
  var dialogdiv = $('<div class="{0}"></div>'.format(dialogdivclass));
  $.ajax({
    url: url,
    type: (options.type || 'GET'),
    beforeSend: options.beforeSend,
    error: options.error,
    complete: options.complete,
    success: function(data, textStatus, jqXHR) {
      if(typeof data == "object" && data.html) { //response is assumed to be JSON
        dialogdiv.html(data.html).dialog({modal: options.modal, title: data.title, buttons: options.buttons});
      } else { //response is assumed to be HTML
        dialogdiv.html(data).dialog({modal: options.modal, title: options.title, buttons: options.buttons});
      }
      $.isFunction(options.success) && (options.success).call(dialogdiv, data, textStatus, jqXHR);
    }
  });
  return dialogdiv;
}
