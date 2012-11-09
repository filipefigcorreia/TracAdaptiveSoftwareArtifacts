/*$(function () {
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
            updateArtifactList(data.rslt.obj.attr("id").substring(5)); // trim 'spec-' from the start of the id
        });
});

function updateArtifactList(specName){
    updateSummaryAndOptions(specName);
    updateAdaptiveArtifactsList(specName);
}

function updateSummaryAndOptions(specName){
    //update the links
}

function updateAdaptiveArtifactsList(specName){
    //make ajax call that will return json
    //clone the prototype row and update it with the contents
    var columns = ['#', 'Attr1', 'Attr2', 'Attr3'];
    var rows = [[1, 'val1', 'val2', 'val3'], [2, 'val', 'val', 'val']]

    var tableContents= '<thead><tr>';
    for (var i = 0; i < columns.length; i++){
        tableContents += '<th>' + columns[i] + '</th>';
    }
    tableContents += '<th></th></tr></thead>';

    for (var j = 0; j < rows.length; j++){
        tableContents += '<tr>';
        for (var k = 0; k < rows[j].length; k++){
            tableContents += '<td>' + rows[j][k] + '</td>';
        }
        tableContents += '<td><a href="">[pages (32)]</a><a href="">[view]</a><a href="">[edit]</a></td></tr>';
    }
    $('table.listing').empty().append(tableContents);
}

*/