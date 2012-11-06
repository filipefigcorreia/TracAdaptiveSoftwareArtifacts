$(document).ready(function(){
    attachFormEventHandlers($("body"));

    $("input#spec").autocomplete(
        {source: function(request, callback){
            Requests.searchSpecNames([request.term], function(data){
                callback(data);
            });
        }}
    );
});

function attachFormEventHandlers(context){
    context.find("a.addattr").click(addAttribute);
    context.find("a.delattr").click(delAttribute);
    context.find("a.addvalue").click(function() { addValue(context, "", "") });
    context.find("a.delvalue").click(delValue);
}

function addAttribute(){
    var newid = uuid.v4()
    var copy = $("tr.attribute:last").clone(true)
    copy.removeClass('prototype')
    var name_input = copy.find("input[name^='attr-name-']")
    name_input.attr("name", "attr-name-" + newid)
    name_input.attr("value", "")
    var type_input = copy.find("select[name^='attr-type-']")
    type_input.attr("name", "attr-type-" + newid)
    type_input.attr("value", "")
    var type_multiplicity = copy.find("select[name^='attr-multiplicity-']")
    type_multiplicity.attr("name", "attr-multiplicity-" + newid)
    type_multiplicity.attr("value", "")
    $("table.attributes").append(copy)
}

function delAttribute(){
    $(this).parent().parent().remove()
}

function addValue(context, name, val){
    var newid = uuid.v4()
    var copy = context.find("tr.attribute:last").clone(true)
    copy.removeClass('prototype')
    var name_input = copy.find("input[name^='attr-name-']")
    name_input.attr("name", "attr-name-" + newid)
    name_input.attr("value", name)
    var value_input = copy.find("input[name^='attr-value-']")
    value_input.attr("name", "attr-value-" + newid)
    value_input.attr("value", val)
    var default_input = copy.find("input[name^='default']")
    default_input.attr("value", newid)
    context.find("table.attributes").append(copy)
}

function delValue(){
    $(this).parent().parent().remove()
}