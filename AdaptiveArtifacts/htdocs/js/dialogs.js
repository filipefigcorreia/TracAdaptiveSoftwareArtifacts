$(document).ready(function(){
    $('a#dialog').click(showNewArtifactDialog);
});

showNewArtifactDialog = function(){
    var tag = showUrlInDialog(
        "/my-trac-environment/adaptiveartifacts/artifact?action=new&format=dialog",
        {
            title: 'Basic Dialog',
            success: function(data, textStatus, jqXHR){
                attachFormEventHandlers($(".dialog"));
                form = $(".dialog").find("form");
                form.submit(function(e){
                    alert("bu!");
                    var form=$(this);
                    $('<input>').attr({
                        type: 'hidden',
                        name: 'format',
                        value: 'dialog'
                    }).appendTo(form);
                    $.ajax({
                        type: form.attr('method'),
                        url: form.attr('action'),
                        data: form.serialize(),
                        success: function(data){
                            $(".dialog").html(data);
                        },
                        error: function(data){
                            $(".dialog").html("bummer!");
                        }
                    });
                    return false; // suppress the normal submit action
                });

            }
        }
    );
}

function showUrlInDialog(url, options){
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
        tag.html(data.html).dialog({modal: options.modal, title: data.title}).dialog('open');
      } else { //response is assumed to be HTML
        tag.html(data).dialog({modal: options.modal, title: options.title}).dialog('open');
      }
      data.tag = tag;
      $.isFunction(options.success) && (options.success)(data, textStatus, jqXHR);
    }
  });
  return tag;
}
