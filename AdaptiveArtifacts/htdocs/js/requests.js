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

Requests.searchSpecDetails = function(spec, callback) {
    $.ajax({
        url: baseurl+'/search/specdetails',
        type: 'post',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        data: {'__FORM_TOKEN':form_token, 'spec':spec}
    });
};

/*
 * Searches artifacts by attribute value.
 * The "attributes" argument is an object, with each key being the attribute name and
 * each value being an array of values to look for.
 * Eg: {'': ['eeny', 'meeny'], 'name': ['miny', 'curly moe'], }
 * The empty string denotes *any* attribute name.
 * The 'name' attribute would be searched with the pseudo-expression:
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
        data: {'__FORM_TOKEN':form_token, 'spec':JSON.stringify(spec), 'attributes':JSON.stringify(attributes)}
    });
};

Requests.searchRelatedPages = function(artifacts_by_id, callback) {
    $.ajax({
        url: baseurl+'/search/relatedpages',
        type: 'post',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        error: function (data){
            error(data);
        },
        data: {'__FORM_TOKEN':form_token, 'attributes':JSON.stringify(artifacts_by_id)}
    });
};

Requests.getArtifactHtml = function(artifact_id, callback){
    $.ajax({
      url: baseurl+"/artifact/"+artifact_id+"?action=view&format=dialog",
      type: 'GET',
      dataType: 'html',
      traditional: true,
      success: function(data, textStatus, jqXHR) {
          callback(data);
      },
      error: undefined
    });
};

Requests.track_it_start = function(resource_type, resource_id, operation, embedded_in_resource_type, embedded_in_resource_id, callback){
    $.ajax({
        url: baseurl+"/tracking/start",
        type: 'POST',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        data: {'__FORM_TOKEN':form_token, 'resource': JSON.stringify(
            {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'operation': operation,
                'embedded_in_resource_type': embedded_in_resource_type,
                'embedded_in_resource_id': embedded_in_resource_id
            }
        )}
    });
};

Requests.track_it_end = function(id){
    $.ajax({
        url: baseurl+"/tracking/end",
        type: 'POST',
        dataType: 'json',
        traditional: true,
        async: false,
        data: {'__FORM_TOKEN':form_token, 'id': id}
    });
};