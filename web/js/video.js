/**
 * Based on code from: http://www.sanraul.com/2009/12/17/using-html5-canvas-to-capture-frames-from-a-video/
 */

var SCALE_FACTOR = 0.25;
var RANDOM_TASK_URL = "rts/video/random";
var SLIDER_MAX = 100;

var assignmentid = 0;
var workerid = 0;
var hitid = 0;

/* now in video.mpy
var isTetris = false;
var isAlert = true; 
var isReward = true;
*/

var timingLoaded = false;

var videoid = 0;

var phase = null;
var phases = [];
var phase_last_locations = [];

var videoLoaded = false;
var locationTimeout = null;
var has_moved_slider = false;

var times = {
    accept: null,
    videoUpload: null,
    show: null,
    go: null,
    submit: null
};

// var MIN_ACCURACY comes from video.mpy
var accurateCount = 0;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }

$(document).ready(function() {
	$.ajaxSetup({ cache: false });
	loadParameters();
	initPrototypes();    // some browsers don't have toISOString()
	initServerTime();

	$('#donebtn').hide().attr("disabled", "true").html("HIT will be submittable after job appears");
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
    var videoElement = $('<a href="media/videos/flv/' + data['filename'] + '.flv"'
        + 'style="display:block; width: ' + data['width'] + 'px; ' 
        + 'height: ' + data['height'] + 'px;" id="player"></a>');

    // idea for range background slider from http://stackoverflow.com/questions/2992148/jquery-slider-set-background-color-to-show-desired-range
    var sliderElement = $('<div id="slider" style="width: ' + data['width'] + 'px"><div id="backgroundSlider" class="range"></div><div class="range below">Find photo in this clip</div></div>');

    $('#videoContainer').append(videoElement).append(sliderElement);    
    
    phase = data['phase'];
    phases.push(phase)
    videoid = data['videoid'];
    
    times.videoUpload = new Date();
    times.videoUpload.setTime(data['creationtime'] * 1000);
    
    console.log("Phase " + phase['phase']);

    initializeVideo();
    
    if (isSlow) {
        $('#snapshotBtn').show();
    }
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
                onStart: function() {
                    // bug in flowplayer: random frame doesn't work onStart
                    //window.setTimeout( function() {
                        videoReady();
                        showGoButton();
                    //}, 250);
                }                 
            },
                
            // disable default controls
            plugins: {
                controls: null
            },
            
            onLoad: function() {
                console.log("video player loaded");
                $f().getPlugin("play").hide();
            },
            
            onBeforeFullscreen: function() { return false; },
            
            onBeforeResume: function() { return false; }
        });
    
    $( "#slider" ).slider( {
        slide: function(event, ui) {
            if (videoLoaded) {
                var percent = ui.value / SLIDER_MAX;
                var smallestPossiblePhase = getStreamPhase();
                if (percent < smallestPossiblePhase['min'] || percent > smallestPossiblePhase['max']) {
                    return false;
                }
    
                seekVideoToPercent(percent);
            }
                
            if (!has_moved_slider) {
                has_moved_slider = true;
            }
            
            /*
            if (!isReplay) {
                uploadLocation(false);
            }
            */
        },
        
        min: 0,
        max: SLIDER_MAX,
        step: 1
    });
}


/**
 * Event called when the video is ready to navigate
 */
function videoReady() {
    videoLoaded = true;
    setRandomFrame();
    updateSliderBackgroundRange();
    
    stream();
    
    if (!isReplay && !isSlow) {
        locationPing();     // start the notification
    }
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
function updateSliderBackgroundRange(updatePhase) {
    if (!updatePhase) {
        updatePhase = phase;    // use current phase
    }

    var left = updatePhase['min'] * 100;
    var width = (updatePhase['max'] - updatePhase['min']) * 100; // percent
    $(".range").css( { "left": left + "%", 
                        "width": width + "%" } )
    
    if (width < 5) {
        $(".range.below").text("");
    }    
    else if (width < 10) {
        $(".range.below").text("clip");
    }    
    else if (width < 20) {
        $(".range.below").text("In this clip");
    }

    // make sure the slider's current position is in range
    var slider = $('#slider');
    var currentValue = slider.slider('value');
    var minSlider = (updatePhase['min'] * SLIDER_MAX);
    var maxSlider = (updatePhase['max'] * SLIDER_MAX);
    if (currentValue < minSlider || currentValue > maxSlider) {
        setRandomFrame();
    }
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

function getBackgroundRange() {
    var left = $('#backgroundSlider').position()['left'];
    var width = $('#backgroundSlider').width();
    var wholeWidth = $('#slider').width();
    
    var start = left / wholeWidth;
    var end = start + (width / wholeWidth);
    
    return { start: start, end: end }
}

// Returns a random number between min and max
function getRandomArbitrary(min, max)
{
  return Math.random() * (max - min) + min;
}
 
function submitForm() {
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

    // phases = p
    var phase_nums = $.map(phases, function(elem, index) { return elem['phase']; } )
    phases_json = JSON.stringify(phase_nums);
    form.append('<input type="hidden" name="p" value="' + phases_json + '" />');
    
    // phase_last_locations = loc
    last_locations_json = JSON.stringify(phase_last_locations);
    form.append('<input type="hidden" name="loc" value="' + last_locations_json + '" />');    
    
    // validation = v
    var validationPicture = $('input:radio:checked');
    var validationString = ""
    if (validationPicture.length > 0) {
        validationString = validationPicture.val();
    }
    form.append('<input type="hidden" name="v" value="' + validationString + '" />');

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
 * Tells the user how many others are working
 */
function updateCount(numWorkers) {
    // in the worst case they will be playing history
    if (numWorkers == 0) {
        numWorkers = 1;
    }

    var message = numWorkers + " other Turker";
    if (numWorkers > 1) {
        message += "s are "
    } else {
        message += " is "
    }
    message += "working with you."
    $('#workerCount').html(message);
}

/**
 * Checks whether the user was in the agreeing group,
 * then updates the UI and DB with that information
 */
function checkAccuracy(sliderLocation, newPhase) {
    if (newPhase['min'] <= sliderLocation && sliderLocation <= newPhase['max']) {
        // They agreed
        accurateCount++;
        $('#output').html("You agreed with other workers! ").addClass("rightAnswer").removeClass("wrongAnswer");
    } else {
        $('#output').html("The other workers disagreed with you. ").addClass("wrongAnswer").removeClass("rightAnswer");
    }
    
    $('#output').append("Use your slider to agree on a picture in this smaller clip. <br>" + accurateCount + " point" + (accurateCount == 1 ? "" : "s")).effect("highlight");
}


/**
 * Reports end-of-game statistics to the Turker and gives them
 * the opportunity to submit.
 */
function converged() {
    
    var output = $('#output');
    if (accurateCount >= MIN_ACCURACY) {
        output.html("Great, you agreed " + accurateCount + " time" + (accurateCount == 1 ? '' : 's') + " out of " + (phases.length-1) + ". ");
        output.removeClass("wrongAnswer").addClass("rightAnswer");
    } else {
        output.html("Oops. You agreed only " + accurateCount + " times out of " + (phases.length-1) + ". Please answer the backup question below correctly to guarantee payment. Then, submit.");
        output.addClass("wrongAnswer").removeClass("rightAnswer");
        
        showBackupTest();
    }
    output.append("Click the submit button below to finish.");
    
    $('#donebtn').removeAttr("disabled").fadeIn();
    
    // add styles
}

/** Shows the backup test if you
 * didn't have much agreement
 */
function showBackupTest() {
    $.getJSON('rts/video/validation',
        function(data) {
            var backup_form = "" 
            for (var i=0; i<data.length; i++) {
                backup_form = backup_form + "<div><input type='radio' name='backup' value='" + data[i] + "'><img src='media/verification/" + data[i]  + "' width='350' /></input></div>"
            }
            
            $('#backupForm').append(backup_form);
            $('#backup').show();
        }
    );
}


/**
 * Tells the server what frame of the video I'm looking at.
 */
var LOCATION_PING_FREQUENCY = 333;  // millis
var CONVERGE_WAIT_TIME = 750;   // millis
function locationPing() {
    uploadLocation(true);
}

function uploadLocation(includeTimeout) {
    var sliderLoc = $('#slider').slider('value') / SLIDER_MAX;
    
    if (!has_moved_slider) {
        window.setTimeout(locationPing, LOCATION_PING_FREQUENCY);
    }
    else{
        var url = "rts/video/location";
        url += "?phase=" + phase['phase'];
        url += "&assignmentid=" + assignmentid;
        url += "&videoid=" + videoid;                
        url += "&location=" + sliderLoc;
        $.getJSON(url,
            function(data) {
                if (data['phase'] != phase['phase']) {
                    console.log("We have a new phase: " + phase['phase'] + " --> " + data['phase'] + ". [" + data['min'] + ', ' + data['max'] + ']'  );
                    
                    // Make sure this isn't just a new name for an old phase
                    // e.g., if the old one just took forever and expired
                    if (data['min'] == phase['min'] && data['max'] == phase['max']) {
                        phases.pop();   // get rid of the old one
                    } else {
                        // OK, this is the real deal. Better test accuracy
                        checkAccuracy(sliderLoc, data);
                    }
                    phase = data;
                    phases.push(phase);
                    phase_last_locations.push(sliderLoc);
                    
                    updateSliderBackgroundRange();
                }
                
                updateCount(data['numworkers']);
            
                
                // Have we converged?
                if (data['max'] - data['min'] == 0 && includeTimeout) {
                    console.log("We converged!");
                    window.setTimeout(converged, CONVERGE_WAIT_TIME);
                } else if (includeTimeout) {
                    window.setTimeout(locationPing, LOCATION_PING_FREQUENCY);
                }
            }
        );
    }
}

/**
 * Returns the current effective phase range. Might be smaller than
 * the full phase if the video is still "streaming" in
 */
function getStreamPhase() {
    var diff = (new Date()) - times.videoUpload;
    var duration = $f().getClip().fullDuration * 1000;
    var percent = Math.min(1.0, diff/duration);
    
    var phaseCopy = $.extend(true, {}, phase);
    var width = phase['max'] - phase['min'];
    phaseCopy['max'] = phase['min'] + (width * percent);
    return phaseCopy;
}

/**
 * Uploads the video as it "comes in" from the server
 */
function stream() {
    if (phase['min'] != 0 || phase['max'] != 1) {
        return;     // we're dooooone
    }    
    
    var phaseCopy = getStreamPhase();
    updateSliderBackgroundRange(phaseCopy);
    
    if (phaseCopy['max'] != phase['max']) { // we're not done yet
        window.setTimeout(stream, 200);
    }
}