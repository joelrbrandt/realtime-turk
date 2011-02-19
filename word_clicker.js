var textid = 0;
var assignmentid = 0; 
var offset = 0;
var trial = 0;
var replay = false;
var numClicks = 0;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }


$(function() {
    loadParameters();
    loadTaskParagraph();
    getServerTime();
    registerDoneBtnListener();
})

function loadParameters() {
    assignmentid = $(document).getUrlParam("assignmentId");
    if (assignmentid == null || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE") {
        assignmentid = 0;
    }
    textid = parseInt($(document).getUrlParam("textid"));
    if (textid == null) {
        textid = 0;
    }
    trial = parseInt($(document).getUrlParam("trial"));
    if (trial == null || isNaN(trial)) {
        trial = 0;
    }
    
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
    var i = jqe.attr("id"); // get the index of the word

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
    $.post("logging.cgi", {wordid:wordid, highlighted:highlighted, textid:textid, time:getServerTime().toISOString(), assignmentid:assignmentid, trial:trial});  
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
