$(document).ready(function(){
    $('a#dialog').click(showNewArtifactDialog);
});

showNewArtifactDialog = function(){
    var dlg = $('.dialog');
    var tag = createDialogFromUrl(
            "/my-trac-environment/adaptiveartifacts/artifact?action=new&format=dialog",
            {
                title: 'Artifact',
                success: function(data, textStatus, jqXHR){
                    attachFormEventHandlers($(".dialog"));
                },
                buttons: {"Create": function() {
                    var form=$('.dialog').find('form');
                    $.ajax({
                        type: form.attr('method'),
                        url: form.attr('action'),
                        data: form.serialize(),
                        context: $(this), //so that we can call $(this) on the success and error callbacks
                        success: function(data){
                            $(this).dialog("close");
                            $(this).dialog("destroy");
                            $(this).remove();
                        },
                        error: function(data){
                            $(".dialog").html("An error occurred, sorry.");
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
                }}
            }
        );
    $('<input>').attr({
        type: 'hidden',
        name: 'format',
        value: 'dialog'
    }).appendTo($('.dialog').find('form'));
    tag.dialog('open');
}

function createDialogFromUrl(url, options){
  options = options || {};
  var tag = $('<div class="dialog"></div>');
  $.ajax({
    url: url,
    type: (options.type || 'GET'),
    beforeSend: options.beforeSend,
    error: options.error,
    complete: options.complete,
    success: function(data, textStatus, jqXHR) {
      if(typeof data == "object" && data.html) { //response is assumed to be JSON
        tag.html(data.html).dialog({modal: options.modal, title: data.title, buttons: options.buttons});
      } else { //response is assumed to be HTML
        tag.html(data).dialog({modal: options.modal, title: options.title, buttons: options.buttons});
      }
      data.tag = tag;
      $.isFunction(options.success) && (options.success)(data, textStatus, jqXHR);
    }
  });
  return tag;
}
