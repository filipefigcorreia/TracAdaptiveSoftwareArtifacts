$(document).ready(function(){
    var table = $("table.listing");
    var get_last_column_cells = function(){
        var column_count = table.find("tr th").length;
        var overflows_count = table.find("tr th.overflowed").length;
        return table.find("tr > *:not(.artifact-pages, .artifact-options, .overflowed):nth-child(n+" + (column_count-1-overflows_count) + ")");
    };

    var counter = 0 ;
    while(table.width() > table.parent().width() && counter<1000){
        get_last_column_cells().addClass("overflowed");
        counter++;
    }

    if (counter>0){
        var cells = get_last_column_cells();
        cells.filter("th").after("<th class='bellows'></th>");
        cells.filter("td").after("<td class='bellows'></td>");
    }
});