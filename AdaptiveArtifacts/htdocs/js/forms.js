$(document).ready(function(){
    attachFormEventHandlers($("body"));
});

function throttle(fn, delay) {
  var timer = null;
  return function () {
    var context = this, args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () {
      fn.apply(context, args);
    }, delay);
  };
}

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
    // Attributes
    context.find("tr.addattr input").focus(function() {
        return addAttributeFromPhantom(context, $(this).parents("tr.phantom"));
    });
    context.find("a.delattr").click(delAttribute);

    // Values
    context.find("tr.addvalue input").focus(function() {
        return addValueFromPhantom(context, $(this).parents("tr.phantom"));
    });
    context.find("a.delvalue").click(delAttribute);
    context.find("a.tomultiline").click(toMultiline);
    context.find("a.touniline").click(toUniline);
    context.find("a.reorder-down,a.reorder-up").click(reorder);

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
    $("input#spec").bind("change keyup input",
        throttle(function(){
            if (!this.value){
                $("div#is_valid_spec").removeClass("invalid");
                $("div#is_valid_spec").removeClass("valid");
                updateAttributeSuggestions([]);
            }else{
                Requests.searchSpecDetails(this.value, function(data){
                            if (data.spec == null){
                                $("div#is_valid_spec").addClass("invalid");
                                $("div#is_valid_spec").removeClass("valid");
                                updateAttributeSuggestions([])
                            }else{
                                $("div#is_valid_spec").removeClass("invalid");
                                $("div#is_valid_spec").addClass("valid");
                                updateAttributeSuggestions(data.attr_suggestions)
                            }
                        });
            }
        }, 500)
    );

    context.find("tr.attribute td.attrname input").blur(function() {
            $(this).val($(this).val().trim());
        });
}

function addAttributeFromPhantom(context, phantom){
    var name = phantom.find("input[name^='attr-name-']").attr("value");
    phantom.hide();
    var inputs = addAttribute(context, name);
    var name_input = inputs[0];
    var type_input = inputs[1];
    if (phantom.hasClass("suggestion")){
         phantom.remove();
        type_input.focus();
    } else {
        phantom.show(1000);
        name_input.focus();
        name_input.select();
    }
    return false;
}

function addAttribute(context, name){
    var newid = uuid.v4();
    var copy = context.find("tr.attribute.prototype").clone(true);
    copy.removeClass('prototype');
    var name_input = copy.find("input[name^='attr-name-']");
    name_input.attr("name", "attr-name-" + newid);
    name_input.attr("value", name);
    var type_input = copy.find("select[name^='attr-type-']");
    type_input.attr("name", "attr-type-" + newid);
    type_input.attr("value", "");
    var multiplicity_input = copy.find("select[name^='attr-multiplicity-']");
    multiplicity_input.attr("name", "attr-multiplicity-" + newid);
    multiplicity_input.attr("value", "");
    context.find("table.attributes tr:not(.phantom):last").after(copy);
    return [name_input, type_input, multiplicity_input];
}

function delAttribute(){
    $(this).parents("tr.attribute").remove();
    return false;
}

function addValueFromPhantom(context, phantom){
    var name = phantom.find("input[name^='attr-name-']").attr("value");
    var value = phantom.find("input[name^='attr-value-']").attr("value");
    phantom.hide();
    var inputs = addValue(context, name, value);
    var name_input = inputs[1];
    var value_input = inputs[2];
    if (phantom.hasClass("suggestion")){
         phantom.remove();
         value_input.focus();
    } else {
        phantom.show(1000);
        name_input.focus();
        name_input.select();
    }
    return false;
}

function addValue(context, name, val, newid){
    newid = typeof newid !== "undefined" ? newid : uuid.v4();

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
    context.find("table.attributes tr:not(.phantom):last").after(copy);
    return [copy, name_input, value_input];
}

function addPhantomValue(context, name, val){
    var tr = addValue(context, name, val, "X")[0];
    tr.attr("class", tr.attr("class") + " phantom addvalue suggestion");
    tr.find("td.attristitle, td.attrreorder, td.attrdelete").remove().after($("<td/>"));
    tr.find("a.tomultiline").remove();
    tr.find("input").focus(function() { //add event missing in the copied prototype
        return addValueFromPhantom(context, $(this).parents("tr.phantom"));
    });
    return tr;
}

function updateAttributeSuggestions(attributes){
    var suggestion_phantoms = $("tr.suggestion.phantom")
    suggestion_phantoms.remove()

    context = $("fieldset#properties");
    for (var i=attributes.length; i>0; i--) {
        if (context.find("input[name^='attr-name-'][value='" + attributes[i-1] + "']").length==0)
            addPhantomValue(context, attributes[i-1], "")
    }
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
    if (!confirm("You may loose wiki markup and line breaks, are you sure?"))
        return false;

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

function reorder(){
    var table = $(this).parents("table");
    var moving_row = $(this).parents("tr:first");
    if ($(this).is(".reorder-up")) {
        if (!moving_row.is(table.find("tr.attribute:not(.prototype):not(.addvalue,.addattr):not(:has(td.readonly)):first"))){
            moving_row.hide();
            moving_row.insertBefore(moving_row.prev());
            moving_row.show(1500);
        }
    } else {
        if (!moving_row.is(table.find("tr.attribute:not(.prototype):not(.addvalue,.addattr):not(:has(td.readonly)):last"))){
            moving_row.hide();
            moving_row.insertAfter(moving_row.next());
            moving_row.show(1500);
        }
    }
    return false;
}