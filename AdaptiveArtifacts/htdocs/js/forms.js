$(document).ready(function(){
    attachFormEventHandlers($("body"));
});

// Adds hidden input fields indicating the attributes' order.
// This method works both for a Type's attributes and for
// an AA's values, as both rely on an input named attr-name-*
function addAttributeOrderFields(form){
    var name_fields = form.find("input[name^='attr-name-']:not([name='attr-name-X'])");
    for (var i=0; i<name_fields.length; i++){
        var field_id = name_fields.get(i).name.substring(10);
        var order_field = $('<input />');
        order_field.attr('type', 'hidden');
        order_field.attr('name', 'attr-order-' + field_id);
        order_field.attr('value', i+1);
        form.append(order_field);
    }
}

function attachFormEventHandlers(context){
    context.find("a.addattr").click(addAttribute);
    context.find("a.delattr").click(delAttribute);
    context.find("a.addvalue").click(function() { return addValue(context, "", "") });
    context.find("a.delvalue").click(delValue);
    context.find("a.tomultiline").click(toMultiline);
    context.find("a.touniline").click(toUniline);
    context.find("#artifact-form").submit(function(e){
        addAttributeOrderFields($("#artifact-form"));
    });
    context.find("#type-form").submit(function(e){
        addAttributeOrderFields($("#type-form"));
    });
    $("input#spec").autocomplete(
        {source: function(request, callback){
            Requests.searchSpecNames([request.term], function(data){
                callback(data);
            });
        }}
    );
}

function addAttribute(){
    var newid = uuid.v4();
    var copy = $("tr.attribute:last").clone(true);
    copy.removeClass('prototype');
    var name_input = copy.find("input[name^='attr-name-']");
    name_input.attr("name", "attr-name-" + newid);
    name_input.attr("value", "");
    var type_input = copy.find("select[name^='attr-type-']");
    type_input.attr("name", "attr-type-" + newid);
    type_input.attr("value", "");
    var type_multiplicity = copy.find("select[name^='attr-multiplicity-']");
    type_multiplicity.attr("name", "attr-multiplicity-" + newid);
    type_multiplicity.attr("value", "");
    $("table.attributes").append(copy);
    return false;
}

function delAttribute(){
    $(this).parent().parent().remove();
    return false;
}

function addValue(context, name, val){
    var newid = uuid.v4();
    var copy = context.find("tr.attribute.prototype").clone(true);
    copy.removeClass('prototype');
    var name_input = copy.find("input[name^='attr-name-']");
    name_input.attr("name", "attr-name-" + newid);
    name_input.attr("value", name);
    var value_input = copy.find("input[name^='attr-value-']");
    value_input.attr("name", "attr-value-" + newid);
    value_input.attr("value", val);
    var default_input = copy.find("input[name^='default']");
    default_input.attr("value", newid);
    if ($('form#artifact-form input[name=default]:checked').length==0)
        default_input.attr('checked', true);
    context.find("table.attributes").append(copy);
    name_input.focus();
    return false;
}

function delValue(){
    $(this).parent().parent().remove();
    return false;
}

function toMultiline(){
    var input = $(this).parent().find("input");
    var textarea = $("<textarea/>")
        .attr("name", input.attr("name"))
        .text(input.val());
    input.after(textarea).remove();
    var link = $(this).parent().find("a")
        .clone()
        .attr("title", "Collapse to single-line field")
        .removeClass("tomultiline")
        .addClass("touniline")
        .click(toUniline);
    $(this)
        .after(link)
        .remove();
    return false;
}

function toUniline(){
    var textarea = $(this).parent().find("textarea");
    var input = $("<input/>")
        .attr("type", "text")
        .attr("name", textarea.attr("name"))
        .val(textarea.text());
    textarea.after(input).remove();
    var link = $(this).parent().find("a")
        .clone()
        .attr("title", "Expand to multi-line field")
        .removeClass("touniline")
        .addClass("tomultiline")
        .click(toMultiline);
    $(this)
        .after(link)
        .remove();
    return false;
}