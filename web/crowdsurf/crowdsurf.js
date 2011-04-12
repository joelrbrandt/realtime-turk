function setup() {
    $("*").each(function(i, e) { $(this).hover(
	function(e) {
	    $(this).css("outline", "red dotted thin");
	    return false;
	},
	function (e) {
	    $(this).css("outline", "");
	    return false;
	}
    ) });

}

$(function() { setup(); });