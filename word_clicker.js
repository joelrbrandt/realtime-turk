var textid = 0;
var assignmentid = 0; 
var workerid = 0;
var offset = 0;
var experiment = 0;
var replay = false;
var numClicks = 0;
var retainer = false;
var retainerType = "random";

var TEST_TEXT_ID = 25;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }


$(function() {
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
    $.getJSON("gettext.cgi", {'textid': textid }, insertText);
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
    
    var logData = {
        event: eventName,
        detail: JSON.stringify(detail), 
        textid: textid, 
        assignmentid: assignmentid,
        workerid: workerid,
        experiment: experiment,
        time: getServerTime().toISOString(),
        bucket: ((bucket && bucket != null) ? bucket.toISOString() : 0),   // if we have a bucket, use it; otherwise, use 0
    }
    
    $.post("logging.cgi", logData,        
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
    $.get("http://needle.csail.mit.edu/realtime/time.cgi",
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
    if (assignmentid == null || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE") {
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