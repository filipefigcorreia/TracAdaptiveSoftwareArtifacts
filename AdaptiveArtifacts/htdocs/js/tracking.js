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

Tracker.prototype.track_it_start = function(url){
    var url_obj = null;
    if (typeof url == "string"){
        url_obj = document.createElement('a');
        url_obj.href = url;
    } else {
        url_obj = url;
    }
    var parts = this.parse_url(url_obj.pathname, url_obj.search);
    if (parts != null){
        //console.log(["start", parts]);
        var me = this;
        Requests.track_it_start(parts[0], parts[1], parts[2], function(data) {
            me.session_id = data["id"];
        });
    }
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

    $(window).on("focus", function() {
        if (page_tracker.session_id != null){
            page_tracker.track_it_end();
        }
        page_tracker.track_it_start(location);
    });

    $(window).blur(function() {
        page_tracker.track_it_end();
    });

    window.onbeforeunload = function() {
        page_tracker.track_it_end();
    };

    page_tracker.track_it_start(location);
});

