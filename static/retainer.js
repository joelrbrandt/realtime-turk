var showTime = null;
var showTimeout;
var checkInterval;
var bucket = null;

var MAX_WAIT_SECONDS = 5;
var REWARD_MAX_SECONDS = 3; // max number of seconds to click the "go" button if you want the reward

// Sets a specific textid if we are near the regular firing period,
// and sets the firing time to be exactly on the dot of the firing period
function scheduleRetainer() {
    if (isPreview()) {
        // don't do this in preview mode
        return;
    }
    checkForTest();
}

// Hides the text from the user
function retainerHide() {
    $('#task-paragraph').hide()
    .after("<div id='retainer' class='task'>In " + MAX_WAIT_SECONDS + " seconds or less, a paragraph will appear here. Act as quickly as you can when it appears to select all the verbs.<br/><br/><img src='media/preview.png' /></div>");
    
    if (isReward) {
        var explanation = "We will give you a <b>two cent bonus</b> if you ";
        if (isAlert) {
            explanation = explanation + " dismiss the alert "
        } else {
            explanation = explanation + " click the Go! button "
        }
        explanation = explanation + "in less than " + REWARD_MAX_SECONDS + " seconds after it appears.";
        
        $('#task-paragraph').before("<p id='bonus-explanation'>" + explanation + "</p><p id='time-report' style='display: none'></p>");        
    }    
    
    $('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
}

// Sets a callback to fire and show the text to the user
function setRetainerCallback() {
    if (showTime == null) { 
        //var waitTime = Math.floor(Math.random()*30) * 1000;
        var waitTime = MAX_WAIT_SECONDS * 1000; 
    } else {
        var waitTime = showTime - getServerTime();
        console.log("presetting wait time");
    }
    console.log("wait time: " + waitTime);
    showTimeout = window.setTimeout(function() {
        window.clearTimeout(checkInterval);
        
        // if we haven't already shown a text, do it now
        if (showTime == null) {
            showGoButton();
        }
    }, waitTime);
    
    /*
    window.setTimeout( function() {
        $('#retainer').html('<div style="font-size: 30pt; color:red;">5 seconds left</div>').effect('shake', { times: 5 }, 300);
    }, waitTime - 5000);
    */
}

function checkForTest() {
    var theURL = 'http://flock.csail.mit.edu/rts/msbernst/testtimer?workerid=' + workerid + '&experimentid=' + experiment + '&textid=' + TEST_TEXT_ID;
    $.get(theURL, function(data) {
        if (data['test']) {
            window.clearTimeout(checkInterval);
            window.clearTimeout(showTimeout);
            textid = TEST_TEXT_ID;
            bucket = parseDate(data['bucket'])
            insertText(data);
            console.log("showing test text")
            showGoButton();
        } else {
            checkInterval = window.setTimeout(checkForTest, 1000);
        }
    });
}

function showGoButton() {
    $('#retainer').hide();
    $('#donebtn').hide();

    showTime = getServerTime();
    logEvent("display", { 'showTime': showTime }, null);
    
    if (isAlert) {
        alert('Start now!');
        // log immediately after they click the OK button
        showText();
    } else {
        $('#task-paragraph').after("<div id='readycontainer' class='task'><button id='readybtn'>Go!</button></div>");
        $('#readybtn').click(showText);    
    }
}

// Shows the text to the user
function showText() {
    var goTime = getServerTime();
    logEvent("go");     // log that they're starting the task
    
    if (isReward) {
        var timeDiff = goTime - showTime;
        var timeString = "You clicked the Go button in " + (timeDiff / 1000) + " seconds.";
        if (timeDiff < REWARD_MAX_SECONDS * 1000) {
            timeString = timeString + " You get the bonus!";
            $('#time-report').css('color', 'red');
            grantBonus();
        }
        $('#time-report').html(timeString).fadeIn();
    }
    
    $('#donebtn').show();
    $('#readycontainer').hide();
    if (assignmentid != 0) {
        $('#donebtn').attr("disabled", "").html("Done");    
    }
    $('#task-paragraph').show().effect('highlight', {}, 3000);    
}

function grantBonus() {
    var theURL = 'http://flock.csail.mit.edu/rts/msbernst/bonus?workerId=' + workerid + '&assignmentId=' + assignmentid + '&hitId=' + hitid;

    $.get(theURL, function(data) {
        console.log("bonus logged");
    });
}