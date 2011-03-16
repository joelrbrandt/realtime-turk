var textid = 0;
var assignmentid = 0; 
var workerid = 0;
var hitid = 0;
var offset = 0;
var experiment = 0;
var replay = false;
var numClicks = 0;
var retainer = false;
var retainerType = "random";

var TEST_TEXT_ID = 25;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }


$(function() {
    $.ajaxSetup({ cache: false })
    initDatePrototype();    // some browsers don't have toISOString()
    loadParameters();
    initServerTime(timeOffsetReady);
});

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
    
    textid = parseInt($(document).getUrlParam("textid"));
    if (textid == null || isNaN(textid)) {
        textid = Math.floor(Math.random() * 24) + 1;
    }
    
    experiment = parseInt($(document).getUrlParam("experiment"));
    if (experiment == null || isNaN(experiment)) {
        experiment = 0;
    }
    
    var retainerURL = $(document).getUrlParam("retainer");
    retainer = (retainerURL === '1');
    
    retainerType = $(document).getUrlParam("retainertype");
    if (retainerType == null) {
        retainerType = "random";
        // other types: "5min"
    }
        
    replay = $(document).getUrlParam("replay") == "1";
}

function timeOffsetReady() {
    if (assignmentid == 0) {
        logEvent("preview");
    } else {
        logEvent("accept");
    }       
    
    if (retainer) {
        scheduleRetainer();
        retainerHide();
        setRetainerCallback();
    }
    loadTaskParagraph();
    registerDoneBtnListener();
    registerFocusBlurListeners(); 
}

function loadTaskParagraph() {
    $.getJSON("http://flock.csail.mit.edu/rts/msbernst/gettext", {'textid': textid }, insertText);
}

function insertText(data) {
    if (textid == TEST_TEXT_ID && parseInt(data['pk']) != TEST_TEXT_ID) {
        // if we're supposed to be showing the test text, and we're getting a callback for some other text, ignore it. Otherwise a callback to gettext might override our test text
        return;
    }
    
    
    $("#task-paragraph").html("<p>"+ data.text + "</p>");
    $(".word").each(function(i, e) { $(e).addClass("word-off") });    	$(".word").click(function() { toggleWord($(this));});
    if (replay) {
        replayLog(textid);
    }
}

// jqe: JQuery Element (span tag) containing the word
// span tag is expected to store the index of the word in its id
// and have either the class "word-on" or "word-off" storing click state
//
function toggleWord(jqe) {
    var i = parseInt(jqe.attr("id").substring(4)); // get the index of the word

    if (jqe.hasClass("word-on")) { // word was on before click
        jqe.removeClass("word-on");
        jqe.addClass("word-off");
        logClick(i, false);
    } else if (jqe.hasClass("word-off")) { // word was off before click
        jqe.removeClass("word-off");
        jqe.addClass("word-on");
        if (assignmentid != 0) {
            logClick(i, true);
        }
    }
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
    
    // if there's no bucket, send it jan 1 1970
    var bucketDate = null;
    if (bucket && bucket != null) {
        bucketDate = bucket;
    } else {
        bucketDate = new Date(0);
    }
    
    var logData = {
        event: eventName,
        detail: JSON.stringify(detail), 
        textid: textid, 
        assignmentid: assignmentid,
        workerid: workerid,
        experiment: experiment,
        time: getServerTime().toISOString(),
        bucket: bucketDate.toISOString(),
    }
    
    $.post("http://flock.csail.mit.edu/rts/msbernst/log", logData,        
        function(reply) {
            console.log(logData.event + " " + logData.time + " " + JSON.stringify(detail));
            if (finishedCallback != null) {
                finishedCallback(reply);
            }
        }
    );
    
}

// wordid: the index of the word in the paragraph, which is assigned by the server and stored
// in the id of the span surrounding the word
//
// highlighted: true iff the word was toggled 'on' using this click
//
function logClick(wordid, highlighted) {
    console.log("word clicked: " + wordid + " " + highlighted);
    var event = highlighted ? "highlight" : "unhighlight";
    
    var detail = new Object();
    detail.wordid = wordid;    
    
    var logTime = getServerTime();
    if (retainer) {
        // we will be benchmarking it against when it showed up        
        detail.showTime = showTime.toISOString();
        detail.clickTime = logTime.clone().toISOString();        
        
        // use Unix epoch as zero time
        //logTime = Date.parse("January 1 1970 00:00:00 GMT").add(logTime - showTime).milliseconds();
    }
    
    logEvent(event, detail, null);
    numClicks++;
}

/**
 * Gets the time from a CSAIL server, calculates the offset, and stores it.
 */
function initServerTime(callback) {
    var startTime = new Date();
    $.get("http://flock.csail.mit.edu/rts/msbernst/time",
        function(data) {            
            var travelTime = (new Date() - startTime)/2;                
            var serverTime = parseDate(data.date);
            console.log(serverTime.getMilliseconds());

            serverTime.addMilliseconds(travelTime);
            offset = (serverTime - new Date());
            console.log("clock synch complete. offset: " + offset);
            
            callback();
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

function registerDoneBtnListener() {
    if (isPreview()) {
        $('#donebtn').attr("disabled", "true").html("Accept HIT to submit work");
    } else {
        var functionGenerator = function(callback) { return function() {
            $('#donebtn').attr("disabled", "true").html("Submitting..."); 
            logEvent("submit", { numHighlighted: $(".word.word-on").length }, callback);
        }}; 
        
        $('#donebtn').click(functionGenerator(submitForm));
    }
}

function submitForm() {
    
    $('#completeForm').append('<input type="hidden" name="assignmentId" value="' + assignmentid + '" />')
    .append('<input type="hidden" name="numClicks" value="' + numClicks + '" />')
    .submit();
}

function registerFocusBlurListeners() {
    $(window).focus(function() {
        logEvent("focus");
    });
    $(window).blur(function() {
        logEvent("blur");
    });
}

function isPreview() {
    return (assignmentid == null || assignmentid == 0 || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE");
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