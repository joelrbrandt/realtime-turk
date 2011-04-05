/**
 * Based on code from: http://www.sanraul.com/2009/12/17/using-html5-canvas-to-capture-frames-from-a-video/
 */

var SCALE_FACTOR = 0.25;
var RANDOM_TASK_URL = "rts/video/random";
var TOTAL_PHOTOS = 3;
var SLIDER_MAX = 100;

var snapshots = [];

var assignmentid = 0;
var workerid = 0;
var hitid = 0;

var isTetris = false;
var isAlert = true;
var isReward = false;

var timingLoaded = false;

var videoid = 0;
var phase = null;

var locationTimeout = null;
var has_moved_slider = false;

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
	initPrototypes();    // some browsers don't have toISOString()
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
    
    video_url = $(document).getUrlParam("videoid");
    if (video_url == null) {
        videoid = 0;
    } else {
        videoid = parseInt(video_url);
    }
}

/**
 * Takes video data from the server and adds it to the page
 */
function videoDataCallback(data) {
    var videoElement = $('<a href="media/videos/' + data['filename'] + '.flv"'
        + 'style="display:block; width: ' + data['width'] + 'px; ' 
        + 'height: ' + data['height'] + 'px;" id="player"></a>');

    // idea for range background slider from http://stackoverflow.com/questions/2992148/jquery-slider-set-background-color-to-show-desired-range
    var sliderElement = $('<div id="slider" style="width: ' + data['width'] + 'px"><div class="range"></div><div class="range below"></div></div>');

    $('#videoContainer').append(videoElement).append(sliderElement);
    
    phase = data['phase'];
    videoid = data['videoid'];
    
    initializeVideo();
}

/**
 * Calls the FlowPlayer code to initialize the video.
 * TODO: get commercial license for FlowPlayer or change code to GPL
 */
function initializeVideo() {
    $f("player", "http://releases.flowplayer.org/swf/flowplayer-3.2.7.swf", {
            // don't start automatically
            clip: {
                autoPlay: false,
                autoBuffering: true,
                onMetaData: function() {
                    // Go to random frame so everyone
                    // doesn't choose the first frame
                    
                    // HACK: video isn't ready when it says it is
                    window.setTimeout(videoReady, 250);
                }                 
            },
                
            // disable default controls
            plugins: {
                controls: null
            },
            
            onLoad: function() {
                $f().getPlugin("play").hide();
            },
            
            onBeforeFullscreen: function() { return false; }
        });
    
    $( "#slider" ).slider( {
        slide: function(event, ui) {
            var percent = ui.value / SLIDER_MAX;
            if (percent < phase['min'] || percent > phase['max']) {
                return false;
            }
            
            seekVideoToPercent(percent);
            
            if (!has_moved_slider) {
                has_moved_slider = true;
            }
        },
        
        min: 0,
        max: SLIDER_MAX,
        step: 1
    });
    
    updateSliderBackgroundRange();
}

/**
 * Moves the video playhead to the desired position
 */
function seekVideoToPercent(percent) {
    var duration = $f().getClip().fullDuration;
    $f().getPlugin("play").hide();
    $f().seek(duration * percent).getPlugin("play").hide();
}

/**
 * Colors the slider and prevents it from 
 * moving outside the given range
 */
function updateSliderBackgroundRange() {
    var left = phase['min'] * 100;
    var width = (phase['max'] - phase['min']) * 100; // percent
    $(".range").css( { "left": left + "%", 
                        "width": width + "%" } )

    // make sure the slider's current position is in range
    var slider = $('#slider');
    var currentValue = slider.slider('value');
    var minSlider = (phase['min'] * SLIDER_MAX);
    var maxSlider = (phase['max'] * SLIDER_MAX);
    if (currentValue < minSlider) {
        slider.slider('value', minSlider);
        seekVideoToPercent(phase['min']);
    } else if (currentValue > maxSlider) {
        slider.slider('value', maxSlider);
        seekVideoToPercent(phase['max']);
    }
}

/**
 * Event called when the video is ready to navigate
 */
function videoReady() {
    setRandomFrame();
    locationPing();     // start the notification
}

/**
 * Sets the video to a random frame when it finishes loading
 */
function setRandomFrame() {
    var duration = $f().getClip().fullDuration;
    var rand = getRandomArbitrary(phase['min'], phase['max']);
    
    $('#slider').slider("value", rand * 100);
    $f().seek(duration * rand).getPlugin("play").hide();
}

// Returns a random number between min and max
function getRandomArbitrary(min, max)
{
  return Math.random() * (max - min) + min;
}
 
/**
 * Invokes the <code>capture</code> function and attaches the canvas element to the DOM.
 */
function shoot(){
    var video  = $('#player');
    var snapshot = $f().getTime();

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
        ssElement.append("<div>" + Math.round(snapshots[i]*100)/100 + "sec</div>");
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
    if (snapshots.length < TOTAL_PHOTOS) {
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
    timestamps_json = JSON.stringify(snapshots);
    form.append('<input type="hidden" name="fa" value="' + timestamps_json + '" />');

    form.submit();
}

// Date prototype hacking in case the browser does not support it
// ref: http://williamsportwebdeveloper.com/cgi/wp/?p=503

function initPrototypes() {
    if (Date.prototype.toISOString == null) {
        console.log("Adding to Date prototype.");
        Date.prototype.toISOString = toISOString;
    }
    if (!Number.prototype.toFixed) {
        Number.prototype.toFixed = function(precision) {
            var power = Math.pow(10, precision || 0);
            return String(Math.round(this * power)/power);
        };
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
            //console.log(logData.event + " " + logData.time + " " + JSON.stringify(detail));
            if (finishedCallback != null) {
                finishedCallback(reply);
            }
        }
    );
    
}

/**
 * Tells the server what frame of the video I'm looking at.
 */
var lastLocation = null;
var MAX_MOVEMENT_PER_PING = 0.03; // make rate the worker can be paging around at and still have this fire
var LOCATION_PING_FREQUENCY = 750;  // millis
function locationPing() {    
    var sliderLoc = $('#slider').slider('value') / SLIDER_MAX;
    
    // TODO: reorganize so we don't need to repeat setTimeout
    if (!has_moved_slider) {
        window.setTimeout(locationPing, LOCATION_PING_FREQUENCY);
    }
    else if (lastLocation != null &&  Math.abs(lastLocation - sliderLoc) > MAX_MOVEMENT_PER_PING) {
        console.log("Moving too fast: " + (lastLocation - sliderLoc));
        lastLocation = sliderLoc;
        window.setTimeout(locationPing, LOCATION_PING_FREQUENCY);
    } else{
        lastLocation = sliderLoc;
        
        var url = "rts/video/location";
        url += "?phase=" + phase['phase'];
        url += "&assignmentid=" + assignmentid;
        url += "&videoid=" + videoid;                
        url += "&location=" + sliderLoc;
        $.getJSON(url,
            function(data) {
                if (data['phase'] != phase['phase']) {
                    console.log("We have a new phase: " + phase['phase'] + " --> " + data['phase'] )
                    phase = data;
                    updateSliderBackgroundRange();
                }
            
                // Have we converged?
                if (data['max'] - data['min'] == 0) {
                    console.log("We converged!");
                } else {
                    window.setTimeout(locationPing, LOCATION_PING_FREQUENCY);
                }
            }
        );
    }
}