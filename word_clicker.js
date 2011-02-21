var textid = 0;
var assignmentid = 0; 
var workerid = 0;
var offset = 0;
var experiment = 0;
var replay = false;
var numClicks = 0;
var retainer = false;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }


$(function() {
    loadParameters();
    if (retainer) {
        retainerHide();
        setShowCallback();
    }
    loadTaskParagraph();
    getServerTime();
    registerDoneBtnListener();
})

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
    
    replay = $(document).getUrlParam("replay") == "1";    
}

function loadTaskParagraph() {
    $.getJSON("gettext.cgi", {'textid': textid }, function(data) {
    	$("#task-paragraph").html("<p>"+ data.text + "</p>");
	    $(".word").each(function(i, e) { $(e).addClass("word-off") });    	$(".word").click(function() { toggleWord($(this));});
        if (replay) {
            replayLog(textid);
        }
    });
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
        logTime = Date.parse("January 1 1970 00:00:00 GMT").add(logTime - showTime).milliseconds();
    }
    
    $.post("logging.cgi", 
        {
            event: event,
            detail: JSON.stringify(detail), 
            textid: textid, 
            assignmentid: assignmentid,
            workerid: workerid,
            experiment: experiment,
            time: logTime.toISOString()
        }
    );  
    numClicks++;
}

/**
 * Gets the time from a CSAIL server, calculates the offset, and stores it.
 */
function getServerTime() {
    var startTime = new Date();
    $.get("http://needle.csail.mit.edu/realtime/time.cgi",
        function(data) {
            var unixSecs = parseInt(data.date.split('.')[0])
            var unixMillis = (parseInt(data.date.split('.')[1]) / 1000);
            
            var travelTime = (new Date() - startTime)/2;                
            var serverTime = (new Date(unixSecs)).addMilliseconds(unixMillis);
            serverTime.addMilliseconds(travelTime);
            offset = (serverTime - new Date());
            console.log("offset: " + offset);
        }
    );
}

function getServerTime() {
    return (new Date().addMilliseconds(offset));
}

function registerDoneBtnListener() {
    var assignmentID = $(document).getUrlParam("assignmentId");
    if (assignmentID == null || assignmentID == "ASSIGNMENT_ID_NOT_AVAILABLE") {
        $('#donebtn').attr("disabled", "true").html("Accept HIT to submit work");
    } else {
        $('#donebtn').click(submitForm);
    }
}

function submitForm() {
    var assignmentID = $(document).getUrlParam("assignmentId");

    $('#completeForm').append('<input type="hidden" name="assignmentId" value="' + assignmentID + '" />')
    .append('<input type="hidden" name="numClicks" value="' + numClicks + '" />')
    .submit();
}
