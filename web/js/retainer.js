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
        console.log("In preview mode, not setting timer.");
        return;
    }
    
    // msbernst: turning off bucket test timing
    // checkForTest();
    setRetainerCallback();
    pingAlive();
}

// Hides the text from the user
function retainerHide() {
    $('#taskText').hide()
    //.after("<div id='retainer' class='task'>In " + MAX_WAIT_SECONDS + " seconds or less, a paragraph will appear here. Act as quickly as you can when it appears to select all the verbs.<br/><br/></div>");
    
    /*if (isReward) {
        var explanation = "We will give you a <b>two cent bonus</b> if you ";
        if (isAlert) {
            explanation = explanation + " dismiss the alert "
        } else {
            explanation = explanation + " click the Go! button "
        }
        explanation = explanation + "in less than " + REWARD_MAX_SECONDS + " seconds after it appears.";
        
        $('#task-paragraph').before("<p id='bonus-explanation'>" + explanation + "</p><p id='time-report' style='display: none'></p>");        
    }
    */
    
    $('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
}

// Sets a callback to fire and show the text to the user
function setRetainerCallback() {
    if (showTime == null) { 
        var waitTime = MAX_WAIT_SECONDS * 1000; 
        var waitDelta = Math.random() * (.30 * waitTime);
        waitTime = waitTime - waitDelta;
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
    
}

/* Tells the server that we're still watching */
function pingAlive() {
    logEvent("ping");
    window.setTimeout(pingAlive, 5000);
}


function checkForTest() {
    var theURL = 'rts/testtimer?workerid=' + workerid + '&experimentid=' + experiment + '&textid=' + TEST_TEXT_ID;
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
    console.log("GO!");
    $('#retainer').hide();
    $('#donebtn').hide();

    showTime = getServerTime();
    logEvent("display", { 'showTime': showTime }, null);
    
    if (isAlert) {
        playSound();
        alert('Start now!');
        // log immediately after they click the OK button
        showText();
    } else {
        $('#goContainer').html("<button id='readybtn'>Go!</button>");
        $('#readybtn').click(showText);
    }
}

// Shows the text to the user
function showText() {
    var goTime = getServerTime();
    logEvent("go");     // log that they're starting the task
    
    if (isReward) {
        var timeDiff = goTime - showTime;
        
        var timeString = "You "
        if (isAlert) {
            timeString = timeString + " dismissed the alert "
        } else {
            timeString = timeString + " clicked the Go! button "
        }        
        
        timeString = timeString +  "in " + (timeDiff / 1000) + " seconds.";
        if (timeDiff < REWARD_MAX_SECONDS * 1000) {
            timeString = timeString + " You get the bonus!";
            $('#time-report').css('color', 'red');
            grantBonus();
        }
        $('#time-report').html(timeString).fadeIn();
    }
    
    $('#donebtn').show();
    $('#goContainer').hide();
    if (assignmentid != 0) {
        $('#donebtn').attr("disabled", "").html("Done");    
    }
    $('#taskText').show();
    $('#taskContainer').effect('highlight', {}, 3000);    
}

function grantBonus() {
    if (isPreview()) {
        return; // don't grant a bonus for a preview!
    }
    
    var theURL = 'rts/bonus?workerId=' + workerid + '&assignmentId=' + assignmentid + '&hitId=' + hitid;

    $.get(theURL, function(data) {
        console.log("bonus logged");
    });
}

function playSound() {
    try {
        var s = soundManager.getSoundById('alert-sound');
        s.play();
    } catch(e) {
        console.log("sound file not loaded yet, do nothing");
    }
}