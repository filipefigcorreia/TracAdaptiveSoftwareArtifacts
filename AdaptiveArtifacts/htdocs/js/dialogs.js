$(document).ready(function(){
    $('.opendialog.newartifact').click( function() {
        createASAFormDialogFromUrl('Artifact', this.href,
                                    { "Create": function() { submitASAFormDialog($(this)) } }
                                  ).dialog('open');
        return false;
    });
    $('.opendialog.viewartifact').click( function() {
        createASAFormDialogFromUrl('Artifact', this.href,
                                    { "Close": function() { $(this).dialog("close"); } }
                                  ).dialog('open');
        return false;
    });
});


/* * * * * * * * * * * * * * * * * * * * * * * * * * * * *
Submits a jquery-ui dialog. The dialog is closed if
submission goes flawlessly, and shows an error message
otherwise.
 */
function submitASAFormDialog(dialogdiv, options) {
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
            options['success'](data);
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
                        options['error'](data);
                    }
                }
            ] );
        }
    });
}

function createASAFormDialogFromUrl(title, url, buttons, functions){
    var dialogdiv = createDialogFromUrl(
                        url + "&format=dialog",
                        {
                            modal: true,
                            title: title,
                            success: function(data, textStatus, jqXHR) {
                                $('<input>').attr({
                                    type: 'hidden',
                                    name: 'format',
                                    value: 'dialog'
                                }).appendTo(dialogdiv.find('form'));

                                attachFormEventHandlers($(this));
                                functions && $.isFunction(functions.open) && (functions.open).call(this);
                            },
                            buttons: buttons
                        },
                        'asa-dialog');
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
      var opts = {modal: options.modal, width: 'auto', buttons: options.buttons};
      if(typeof data == "object" && data.html) { //response is assumed to be JSON
        dialogdiv.html(data.html).dialog($.extend(opts, {title: data.title}));
      } else { //response is assumed to be HTML
        dialogdiv.html(data).dialog($.extend(opts, {title: options.title}));
      }
      $.isFunction(options.success) && (options.success).call(dialogdiv, data, textStatus, jqXHR);
    }
  });
  return dialogdiv;
}
