var page_tracker = null;

var Tracker = function(){
    this.session_id = null;
};

Tracker.prototype.parse_url = function(pathname, query){
    var resource_type = "", resource_id = "", operation = "";
    if (pathname.indexOf(baseurl) == -0){ // it's an asa page
        var rel_path = pathname.substr(baseurl.length);
        if (rel_path == ""){
            resource_type = "index";
            resource_id = "";
            operation = "view"
        } else {
            var split = rel_path.split("/");
            resource_type = "asa_" + split[1];
            resource_id = split[2];
            if (query.indexOf("action=edit")!=-1){
                operation = "edit";
            } else if (query.indexOf("action=new")!=-1){
                operation = "new";
            } else {
                operation = "view";
            }
        }
    } else if (pathname.indexOf("/wiki") != -1){ // it's a wiki page
        resource_type = "wiki";
        resource_id = pathname.split("/wiki")[1];
        operation = query.indexOf("action=edit")!=-1 ? "edit" : "view";
    } else if (pathname.indexOf("/search") != -1){ // we're using trac's search feature
        resource_type = "search";
        resource_id = pathname.split("/search")[1];
        operation = "";
    } else { // another trac area
        // do nothing
        return null;
    }
    return [resource_type, resource_id, operation];
};

Tracker.prototype.get_url_obj = function(url){
    var url_obj = null;
    if (typeof url == "string"){
        url_obj = document.createElement('a');
        url_obj.href = url;
    } else {
        url_obj = url;
    }
    return url_obj;
};

Tracker.prototype.track_it_start = function(url, embedded_in_url){
    var url_obj = this.get_url_obj(url);
    var parts = this.parse_url(url_obj.pathname, url_obj.search);
    if (parts != null){
        this.track_it_start_by_typeidop(parts[0], parts[1], parts[2], embedded_in_url)
    }
};

Tracker.prototype.track_it_start_by_typeidop = function(resource_type, resource_id, operation, embedded_url) {
    var embedded_resource_type = null;
    var embedded_resource_id = null;
    if (embedded_url != undefined && embedded_url != null) {
        var embedded_parts = this.parse_url(this.get_url_obj(embedded_url).pathname, "");
        embedded_resource_type = embedded_parts[0];
        embedded_resource_id = embedded_parts[1];
    }
    var me = this;
    Requests.track_it_start(resource_type, resource_id, operation, embedded_resource_type, embedded_resource_id, function(data) {
        me.session_id = data["id"];
    });
};

Tracker.prototype.track_it_end = function(){
    if (this.session_id != null){
        Requests.track_it_end(this.session_id);
        this.session_id = null;
    }else{
        console.log("Session already ended... Ignoring.");
    }
};

$(document).ready(function(){
    page_tracker = new Tracker();
    var embedded_artifacts_trackers = [];

    $(window).on("focus", function() {
        if (page_tracker.session_id != null){
            stop_all_trackers()
        }
        start_all_trackers();
    });

    $(window).blur(function() {
        stop_all_trackers();
    });

    window.onbeforeunload = function() {
        stop_all_trackers();
    };

    start_all_trackers();

    function start_all_trackers() {
        page_tracker.track_it_start(location);
        if (typeof embedded_artifacts != 'undefined') {
            for(var i = 0; i < embedded_artifacts.length; i++) {
                var artifact_id = embedded_artifacts[i];
                var artifact_tracker = new Tracker();
                artifact_tracker.track_it_start_by_typeidop("asa_artifact", artifact_id, "view", location);
                embedded_artifacts_trackers.push(artifact_tracker);
            }
        }
    }

    function stop_all_trackers(){
        page_tracker.track_it_end();
        for(var i = 0; i < embedded_artifacts_trackers.length; i++) {
            var artifact_tracker = embedded_artifacts_trackers[i];
            artifact_tracker.track_it_end();
        }
        embedded_artifacts_trackers = [];
    }
});

