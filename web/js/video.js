/**
 * Based on code from: http://www.sanraul.com/2009/12/17/using-html5-canvas-to-capture-frames-from-a-video/
 */

var SCALE_FACTOR = 0.25;
var snapshots = [];
var assignmentId = 0;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }

$(document).ready(function() {
	getURLParams();
	setRandomFrame();
	$('#snapshotBtn').click(shoot);
	$('#donebtn').click(submitForm);
});

/**
 * Initializes any URL parameters
 */
function getURLParams() {
    assignmentid = $(document).getUrlParam("assignmentId");
    if (assignmentid == null || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE") {
        assignmentid = 0;
    }

}

/**
 * Sets the video to a random frame when it finishes loading
 */
function setRandomFrame() {
    $('#vid').bind('loadeddata', function() {
	    var randomTimestamp = Math.random() * $('#vid')[0].duration;
	    $('#vid')[0].currentTime = randomTimestamp;
	});
}

/**
 * Captures a image frame from the provided video element.
 * 
 * @param {Video} video HTML5 video element from where the image frame will be captured.
 * @param {Number} scaleFactor Factor to scale the canvas element that will be return. This is an optional parameter.
 * 
 * @return {Canvas}
 */
function capture(video, scaleFactor) {
    if(scaleFactor == null){
	scaleFactor = 1;
    }
    var w = video.videoWidth * scaleFactor;
    var h = video.videoHeight * scaleFactor;
    var canvas = document.createElement('canvas');
    canvas.width  = w;
    canvas.height = h;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);

    var snapshot = {
	'canvas': canvas,
	'timestamp': video.currentTime
    }
    return snapshot;
} 
 
 
/**
 * Invokes the <code>capture</code> function and attaches the canvas element to the DOM.
 */
function shoot(){
    var video  = $('#vid')[0];
    var snapshot = capture(video, SCALE_FACTOR);
    //    canvas.onclick = function(){
    //	window.open(this.toDataURL());
    //    };

    if ($.inArray(snapshot.timestamp, getSnapshotTimestamps()) != -1) {
	$('#submitError').html("You already have that picture. Choose another one.");
    }
    else {
	snapshots.unshift(snapshot);
	$('#submitError').html('');
    }
    
    refreshShots();
}

function getSnapshotTimestamps() {
    var timestamps = $.map(snapshots, function(item, i) {
	    return item.timestamp;
	});
    return timestamps;
}

/**
 * Refreshes the set of pictures
 */
function refreshShots() {
    var output = $('#output');
    output.html("")
    for(var i=0; i<snapshots.length; i++){
	var ssElement = $("<div class='snapshot' id='snapshot" + i + "'></div>");
	ssElement.append(snapshots[i].canvas);
	ssElement.append("<div>" + Math.round(snapshots[i].timestamp*100)/100 + "sec</div>");
	ssElement.append("<a href='#' class='remove'>(remove)</a>");
	output.append(ssElement);
    }
    
    $('.remove').click(function() {
	    var snapshot = $(this).parent(".snapshot");
	    var ssId = parseInt(snapshot.attr('id').substring("snapshot".length));
	    snapshots.splice(ssId, 1);
	    refreshShots();
    });
}

function submitForm() {
    if (snapshots.length < 3) {
	$('#submitError').html("You have selected fewer than three photos. Please select at least three photos and then submit.");
	return;
    }

    var form = $('#completeForm');

    // assignmentid = assignmentId  (Amazon requires this to be called "assignmentId")                                                                                                   
    form.append('<input type="hidden" name="assignmentId" value="' + assignmentid + '" />');

    timestamps_json = JSON.stringify(getSnapshotTimestamps());
    form.append('<input type="hidden" name="timestamps" value="' + timestamps_json + '" />');

    form.submit();
}
