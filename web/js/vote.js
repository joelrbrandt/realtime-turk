var assignmentid = 0;
var workerid = 0;
var hitid = 0;

var timingLoaded = false;
var vote;

var times = {
    accept: null,
    show: null,
    go: null,
    submit: null
};

var RANDOM_TASK_URL = "rts/vote/random"

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
}

/**
 * Takes video data from the server and adds it to the page
 */
function voteDataCallback(data) {
    $('#voteContainer').html("<table id='voteTable'><tr><td><h2>Click on the best photo:</h2></td></tr><tr id='voteRow'></tr></table>")
    
    for (var i=0; i<data.photos.length; i++) {
        $('#voteTable').append("<tr><td><img src='" + data.photos[i] + "' width=500 /></td></tr>");
    }
    
    $('#voteTable img').click(function() {
        var location = $(this).attr('src');
        location = location.substring(location.length-7, location.length-4); // just the main filename
        vote = location;
        submitForm();
    }).css("cursor", "pointer");
    
    videoid = data['videoid']
    showGoButton();
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

    // vote = v
    form.append('<input type="hidden" name="v" value="' + vote + '" />');
    
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
        times.accept = getServerTime();            
        logEvent("accept", null, function() {
            scheduleRetainer(voteDataCallback, RANDOM_TASK_URL);
            retainerHide();
        
            registerFocusBlurListeners();        
        });
    }       
}

function isPreview() {
    return (assignmentid == null || assignmentid == 0 || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE");
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
    
    $.post("rts/vote/log", logData,        
        function(reply) {
            //console.log(logData.event + " " + logData.time + " " + JSON.stringify(detail));
            if (finishedCallback != null) {
                finishedCallback(reply);
            }
        }
    );   
}