var textid = 0;
var assignmentid = 0; 
var workerid = 0;
var hitid = 0;

var experiment = 0;
var replay = false;
var numClicks = 0;
var retainer = false;
var retainerType = "random";

var isChatroom = true;

// Timing
var timingLoaded = false;
var offset = 0;

var times = {
    accept : null,
    show : null,
    go : null,
    first : null,
    submit : null,
}

var TEST_TEXT_ID = 25;

try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }


$(function() {
    $.ajaxSetup({ cache: false })
    initDatePrototype();    // some browsers don't have toISOString()
    loadParameters();
    initServerTime();
    initUserReady();
    //initChatroom();
    
    // loadParameters and initServertime call testReady()
    // once they return, which calls main() once they have
    // both returned ready
    // javascript sucks at semaphores and things, so this
    // seemed to be the way that the internet recommended
    // doing it
    $('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
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

    // These should be entered by the HTML template, just echoing
    console.log('alert: ' + isAlert + " | reward: " + isReward);    
}

/**
 * Finds out if the user has already OK'ed our information,
 * and if not, sets up the button listener.
 */
function initUserReady() {
    if (isPreview()) { 
        logEvent("preview"); 
        // Return so that we don't show the "I understand" button
        return;
    }    
    
    $('#instructionsOK').click(function() {
        // When they click to say they understand
        $('#instructionsOK').hide();
        if (!isPreview()) {
            // Tell the server that they don't need to click it again.
            $.get('rts/agreement/set?workerid=' + workerid);
            
            $('#agreementContainer').append("Great! We signaled our server that you are ready for a task. You shouldn't have to click this button again.");
        }
        instructionsOK();
    });
}

/**
 * User has indicated via button press or DB call that they understand
 * the instructions
 */
function instructionsOK() {
    userReady = true;
    $.get('rts/agreement/set?workerid=' + workerid)    
    testReady();
}

/**
 * Starts the timers and shows everything to the user.
 */
function beginTask() {
    if (assignmentid != 0) {
        logEvent("accept");
	times.accept = getServerTime();
    }       
    
    if (retainer) {
        scheduleRetainer();
        retainerHide();
    }
    loadTaskParagraph();
    registerDoneBtnListener();
    registerFocusBlurListeners(); 
}

/**
 * Calls main if all required AJAX calls have returned
 */
function testReady() {
    if (timingLoaded && userReady) {
        beginTask();
    }
}

/**
 * Gets a random paragraph from the server
 */
function loadTaskParagraph() {
    $.getJSON("rts/gettext", {'textid': textid }, insertText);
}

/**
 * Takes the paragraph text and inserts it (hidden) into the DOM
 */
function insertText(data) {
    if (textid == TEST_TEXT_ID && parseInt(data['pk']) != TEST_TEXT_ID) {
        // if we're supposed to be showing the test text, and we're getting a callback for some other text, ignore it. Otherwise a callback to gettext might override our test text
        return;
    }
    
    
    $("#taskText").html("<p>"+ data.text + "</p>");
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
    
    $.post("rts/log", logData,        
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
    if (times.first == null) {
	// first word clicked, so record the time
	times.first = getServerTime();
    }

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

function registerDoneBtnListener() {
    if (isPreview()) {
        $('#donebtn').attr("disabled", "true").html("Accept HIT to submit work");
    } else {
        var functionGenerator = function(callback) { return function() {
            $(this).attr("disabled", "true").html("Submitting..."); 
            
            var verbs = getSelectedVerbs();
            var postData = {
                'textid': textid,
                'verbs[]': verbs
            };
            
            $.post('rts/verify', postData, function(data) {
                verifyResults(data, callback);
            });
        }}; 
        
        $('#donebtn').click(functionGenerator(submitForm));
        $('#surebtn').click(submitForm);
    }
}

/**
 * Checks the submitter's precision/recall values against minimum passable
 * values and submits or errors as necessary.
 */
var MIN_PRECISION = .75;
var MIN_RECALL = .66;
function verifyResults(precision_recall, callback) {
    var precision = precision_recall['precision']
    var recall = precision_recall['recall']
    console.log("precision: " + precision)
    console.log("recall: " + recall)
    
    // we can keep track of how they do
    logEvent("verify", precision_recall, null);
    
    if (precision >= MIN_PRECISION && recall >= MIN_RECALL) {
        console.log("work accepted");
        logEvent("submit", { numHighlighted: $(".word.word-on").length }, callback);                    
    } else {
        var errorMessage = "";
        if (precision < MIN_PRECISION) {
            errorMessage = errorMessage + "Warning: You have highlighted many words that our backup algorithm did not classify as verbs.<br/>"
        }
        if (recall < MIN_RECALL) {
            errorMessage = errorMessage + "Warning: You have left many words un-highlighted that our backup algorithm classified as verbs.<br/>"
        }
        errorMessage = errorMessage + "If you are sure that your selections are correct, click the 'I'm Sure' button. We will review your work and reject it if it does not meet our threshold.<br/>Otherwise, change your selections and click 'Try Again' to see if you agree more with our algorithm."

        $('#donemsg').html(errorMessage)
        $('#donebtn').attr("disabled", "").html("Try Again"); 
        $('#surebtn').show();
    }
}

/**
 * Returns an array of verb word indices that have been selected
 */
function getSelectedVerbs() {
    return $(".word.word-on").map(function() { return parseInt($(this).attr('id').substr(4)) }).get();
}

function submitForm() {
    // record the time of submission in the times array
    times.submit = getServerTime();

    var form = $('#completeForm');

    // Add everything to the form that we want in the database
    // using short names for the fields so we have as much URL space as possible
    //
    // Comments above each added form element give the db column name on the left
    // and the form element name on the right

    // assignmentid = assignmentId  (Amazon requires this to be called "assignmentId")
    form.append('<input type="hidden" name="assignmentId" value="' + assignmentid + '" />');

    // workerid = w
    form.append('<input type="hidden" name="w" value="' + workerid + '" />');

    // experiment = e
    form.append('<input type="hidden" name="e" value="' + experiment + '" />');

    // textid = t
    form.append('<input type="hidden" name="t" value="' + textid + '" />');

    // wordarray = wa
    wa = getSelectedVerbs();
    wa_json = JSON.stringify(wa); 
    form.append('<input type="hidden" name="wa" value="' + wa_json + '" />');

    // accept = a
    a = times.accept == null ? "" : times.accept.toISOString()
    form.append('<input type="hidden" name="a" value="' + a + '" />');

    // show = sh
    sh = times.show == null ? "" : times.show.toISOString()
    form.append('<input type="hidden" name="sh" value="' + sh + '" />');

    // go = g
    g = times.go == null ? "" : times.go.toISOString()
    form.append('<input type="hidden" name="g" value="' + g + '" />');

    // first = f
    f = times.first == null ? "" : times.first.toISOString()
    form.append('<input type="hidden" name="f" value="' + f + '" />');

    // submit = su
    su = times.submit == null ? "" : times.submit.toISOString()
    form.append('<input type="hidden" name="su" value="' + su + '" />');
    
    form.submit();
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