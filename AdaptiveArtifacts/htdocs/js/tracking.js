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
            resource_type = split[1];
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
        //console.log(["stop"]);
        Requests.track_it_end(this.session_id);
        this.session_id = null;
    }else{
        console.log(["ups"]);
    }
};

$(document).ready(function(){
    page_tracker = new Tracker();

    $(window).focus(function() {
        page_tracker.track_it_start(location);
    });

    $(window).blur(function() {
        page_tracker.track_it_end();
    });

    window.onbeforeunload = function() {
        page_tracker.track_it_end();
    };

    page_tracker.track_it_start(location);

/*
    // set name of hidden property and visibility change event
    var hidden, visibilityChange;
    if (typeof document.hidden !== "undefined") {
    	hidden = "hidden";
    	visibilityChange = "visibilitychange";
    } else if (typeof document.mozHidden !== "undefined") {
    	hidden = "mozHidden";
    	visibilityChange = "mozvisibilitychange";
    } else if (typeof document.msHidden !== "undefined") {
    	hidden = "msHidden";
    	visibilityChange = "msvisibilitychange";
    } else if (typeof document.webkitHidden !== "undefined") {
    	hidden = "webkitHidden";
    	visibilityChange = "webkitvisibilitychange";
    }

    var tracker = new Tracker();

    function handleVisibilityChange() {
    	if (document[hidden]) {
            tracker.track_it_end();
    	} else {
            tracker.track_it_start(location.pathname, location.search);
    	}
    }

    // warn if the browser doesn't support addEventListener or the Page Visibility API
    if (typeof document.addEventListener === "undefined" ||
    	typeof hidden === "undefined") {
    	alert("You need a browser that supports the Page Visibility API.");
    } else {
        // handle page visibility change
        // see https://developer.mozilla.org/en/API/PageVisibility/Page_Visibility_API
        document.addEventListener(visibilityChange, handleVisibilityChange, false);
    }
    */
});

