/**
 * Based on code from: http://www.sanraul.com/2009/12/17/using-html5-canvas-to-capture-frames-from-a-video/
 */

var SCALE_FACTOR = 0.25;
var RANDOM_TASK_URL = "rts/video/random";

var snapshots = [];

var assignmentId = 0;
var workerid = 0;
var hitid = 0;

var isTetris = false;
var isAlert = true;
var isReward = false;

var timingLoaded = false;

var times = {
    accept: null,
    show: null,
    go: null,
    submit: null
};

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }

$(document).ready(function() {
	$.ajaxSetup({ cache: false });
	loadParameters();
	initDatePrototype();    // some browsers don't have toISOString()
	initServerTime();

	$('#snapshotBtn').click(shoot);
	$('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
});

/**
 * Initializes any URL parameters
 */
function loadParameters() {
    assignmentid = $(document).getUrlParam("assignmentId");
    if (assignmentid == null || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE") {
        assignmentid = 0;
    }

    workerid = $(document).getUrlParam("workerId");
    if (workerid == null) {
        workerid = 0;
    }    

    hitid = $(document).getUrlParam("hitId");
    if (hitid == null) {
        hitid = 0;
    }
}

/**
 * Takes video data from the server and adds it to the page
 */
function videoDataCallback(data) {
    var videoElement = $("<video id='vid' width=" + data['width'] + " height=" + data['height'] + " preload='true' controls='true'>")
    var sources = data['sources'];
    for (var i=0; i<sources.length; i++) {
	var source = $("<source src='" + sources[i].src + "' type='" + sources[i].type + "'  />");
	videoElement.append(source);
    }
    videoElement.append( document.createTextNode('If you can see this, please return the HIT. Your browser does not support HTML5 video. You may try it with recent versions of Chrome, Firefox, Safari, or Internet Explorer.') );

    $('#videoContainer').append(videoElement);

    setRandomFrame();
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

    // record the time of submission in the times array
    times.submit = getServerTime();

    var form = $('#completeForm');

    // assignmentid = assignmentId  (Amazon requires this to be called "assignmentId"
    form.append('<input type="hidden" name="assignmentId" value="' + assignmentid + '" />');

    // workerid = w
    form.append('<input type="hidden" name="w" value="' + workerid + '" />');

    // accept = a
    a = times.accept == null ? "" : times.accept.toISOString()
    form.append('<input type="hidden" name="a" value="' + a + '" />');

    // show = sh
    sh = times.show == null ? "" : times.show.toISOString()
    form.append('<input type="hidden" name="sh" value="' + sh + '" />');

    // go = g
    g = times.go == null ? "" : times.go.toISOString()
    form.append('<input type="hidden" name="g" value="' + g + '" />');

    // submit = su
    su = times.submit == null ? "" : times.submit.toISOString()
    form.append('<input type="hidden" name="su" value="' + su + '" />');

    // framearray = fa
    timestamps_json = JSON.stringify(getSnapshotTimestamps());
    form.append('<input type="hidden" name="fa" value="' + timestamps_json + '" />');

    form.submit();
}

// Date prototype hacking in case the browser does not support it
// ref: http://williamsportwebdeveloper.com/cgi/wp/?p=503

function initDatePrototype() {
    if (Date.prototype.toISOString == null) {
        console.log("Adding to Date prototype.");
        Date.prototype.toISOString = toISOString;
    }
}

function toISOString() {
    var d = this;
     return d.getUTCFullYear() + '-' +  padzero(d.getUTCMonth() + 1) + '-' + padzero(d.getUTCDate()) + 'T' + padzero(d.getUTCHours()) + ':' +  padzero(d.getUTCMinutes()) + ':' + padzero(d.getUTCSeconds()) + '.' + pad2zeros(d.getUTCMilliseconds()) + 'Z';
 }
 
function padzero(n) {
    return n < 10 ? '0' + n : n;
}

function pad2zeros(n) {
    if (n < 100) {
         n = '0' + n;
     }
     if (n < 10) {
         n = '0' + n;
     }
     return n;     
 }

/**
 * Gets the time from a CSAIL server, calculates the offset, and stores it.
 */
function initServerTime() {
    var startTime = new Date();
    $.get("rts/time",
        function(data) {            
            var travelTime = (new Date() - startTime)/2;                
            var serverTime = parseDate(data.date);

            serverTime.addMilliseconds(travelTime);
            offset = (serverTime - new Date());
            console.log("clock sync complete. offset: " + offset);
            
            timingLoaded = true;
            testReady();
        }
    );
}

function parseDate(dateString) {
    var dateInt = parseInt(dateString);
    var parsedDate = new Date(dateInt)
    return parsedDate;
}

function getServerTime() {
    return (new Date().addMilliseconds(offset));
}

/**
 * Calls main if all required AJAX calls have returned
 */
function testReady() {
    if (timingLoaded) {
        beginTask();
    }
}

/**
 * Starts the timers and shows everything to the user.
 */
function beginTask() {
    if (assignmentid != 0) {
        logEvent("accept");
	times.accept = getServerTime();
    }       
    
    scheduleRetainer(videoDataCallback, RANDOM_TASK_URL);
    retainerHide();

    registerDoneBtnListener();
    registerFocusBlurListeners(); 
}

function isPreview() {
    return (assignmentid == null || assignmentid == 0 || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE");
}

function registerDoneBtnListener() {
    if (isPreview()) {
        $('#donebtn').attr("disabled", "true").html("Accept HIT to submit work");
    } else {
            $(this).attr("disabled", "true").html("Submitting..."); 
	    $('#donebtn').click(submitForm);
    }
}

function registerFocusBlurListeners() {
    $(window).focus(function() {
        logEvent("focus");
    });
    $(window).blur(function() {
        logEvent("blur");
    });
}

function logEvent(eventName) {
    logEvent(eventName, {}, null);
}

// eventName: "submit", "preview", "blur", etc.
// data: any context-specific JSON to send to the server
// finishedCallback: any function to call when done logging
function logEvent(eventName, detail, finishedCallback) {
    if (detail == null) {
        detail = {};
    }
    
    var logData = {
        event: eventName,
        detail: JSON.stringify(detail), 
        assignmentid: assignmentid,
	workerid: workerid,
	hitid: hitid,
        time: getServerTime().toISOString()
    }
    
    $.post("rts/video/log", logData,        
        function(reply) {
            console.log(logData.event + " " + logData.time + " " + JSON.stringify(detail));
            if (finishedCallback != null) {
                finishedCallback(reply);
            }
        }
    );
    
}
