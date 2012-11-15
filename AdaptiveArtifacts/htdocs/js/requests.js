var Requests = function(){};

Requests.searchSpecNames = function(needles, callback) {
    $.ajax({
        url: baseurl+'/search/spec',
        type: 'post',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        data: {'__FORM_TOKEN':form_token, 'q':needles}
    });
};

/*
 * Searches artifacts by attribute value.
 * The "attributes" argument is an object, with each key being the attribute name and
 * each value being an array of values to look for.
 * Eg: {'__any': ['eeny', 'meeny'], 'name': ['miny', 'curly moe'], }
 * '__any' denotes 'any attribute name'.
 * The 'name' attribute would be search with the pseudo-expression:
 * 'eeny' OR 'meeny' OR 'miny' OR ('curly' AND 'moe')
 * */
Requests.searchArtifacts = function(spec, attributes, callback) {
    $.ajax({
        url: baseurl+'/search/artifact',
        type: 'post',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        data: {'__FORM_TOKEN':form_token, 'q':JSON.stringify(attributes)}
    });
};

