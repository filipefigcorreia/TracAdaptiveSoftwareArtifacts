$(function () {
    var listroot = $("#entry-points #specs");
	listroot
		.jstree(
            {
                "themes" : {
                    "theme" : "default",
                    "icons" : false
              		},
                "plugins" : ["themes","html_data", "ui"]
            }
        ).bind('loaded.jstree', function() {
            listroot.jstree('open_all');
            listroot.jstree("set_focus");
          }
        ).bind("select_node.jstree", function (event, data) {
            // `data.rslt.obj` is the jquery extended node that was clicked
            updateArtifactList(data.rslt.obj.attr("id"));
        });
});

function updateArtifactList(id){
    alert(id);
}

$(function () {
	$("#entry-points #others")
		.jstree(
        {
            "themes" : {
                "theme" : "default",
                "dots" : false,
                "icons" : false
          		},
            "plugins" : ["themes","html_data", "ui"]
        }
    );
    $("#entry-points #others").jstree("set_focus");
});