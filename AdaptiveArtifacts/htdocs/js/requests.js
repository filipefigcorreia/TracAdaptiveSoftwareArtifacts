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

Requests.searchArtifacts = function(needles, callback) {
    $.ajax({
        url: baseurl+'/search/artifact',
        type: 'post',
        dataType: 'json',
        traditional: true,
        success: function (data) {
            callback(data);
        },
        data: {'__FORM_TOKEN':form_token, 'q':needles}
    });
};

