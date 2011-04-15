/** If we're in "slow" mode, e.g. no continuous refinement, we pick
 * photos using this interface
 */

var TOTAL_PHOTOS = 1;
var snapshots = [];

$(document).ready(function() {
    $('#taskText').after('<div id="photos"><div><button id="snapshotBtn">Good Photo</button></div><div id="output"></div></div>');
	$('#snapshotBtn').click(shoot);

    var form = $('#completeForm');	
    form.append('<input type="hidden" name="sn" value="" />');
    form.attr("action", "rts/video/slowsubmit");
});

/**
 * Invokes the <code>capture</code> function and attaches the canvas element to the DOM.
 */
function shoot(){
    var video  = $('#player');
    var snapshot = $('#slider').slider('value') / SLIDER_MAX;

    if ($.inArray(snapshot, snapshots) != -1) {
        $('#submitError').html("You already have that picture. Choose another one.");
    }
    else {
        snapshots.unshift(snapshot);
        $('#submitError').html('');
    }
    
    logEvent("picture", { 'timestamp': snapshot }, null);
    refreshShots();
}

/**
 * Refreshes the set of pictures
 */
function refreshShots() {
    var output = $('#output');
    output.html("")
    for(var i=0; i<snapshots.length; i++){
        var ssElement = $("<div class='snapshot' id='snapshot" + i + "'></div>");
        //ssElement.append(snapshots[i].canvas);
        ssElement.append("<div>" +snapshots[i]*100 + "%</div>");
        ssElement.append("<a href='#' class='remove'>(remove)</a>");
        output.append(ssElement);
    }
    
    $('.remove').click(function() {
	    var snapshot = $(this).parent(".snapshot");
	    var ssId = parseInt(snapshot.attr('id').substring("snapshot".length));
	    snapshots.splice(ssId, 1);
	    refreshShots();
    });
    
    if (snapshots.length == 1) {
        $('#donebtn').show().attr("disabled", "");        
        $('#submitError').html("");                
    } else {
        $('#donebtn').attr("disabled", "true");
        $('#submitError').html("You have not selected " + TOTAL_PHOTOS + " photo. Please select exactly one photo (removing ones you don't want) and then submit.");        
    }
    
   timestamps_json = JSON.stringify(snapshots);
   var timestamps = $('#completeForm input:hidden[name="sn"]');	
   timestamps.attr('value', timestamps_json);
}
