var showTime = null;
var showTimeout;
var checkInterval;
var bucket = null;

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
}

// Sets a callback to fire and show the text to the user
function setRetainerCallback() {
    if (showTime == null) { 
        var waitTime = Math.random() * maxWaitTime * 1000; 
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
    
    if (isTetris) {
        simulatePause();
    }

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
    
    stopSound();    // stop any alert sound that's playing
    
    if (isReward) {
        var timeDiff = goTime - showTime;
        
        var timeString = "You "
        if (isAlert) {
            timeString = timeString + " dismissed the alert "
        } else {
            timeString = timeString + " clicked the Go! button "
        }        
        
        timeString = timeString +  "in " + (timeDiff / 1000) + " seconds.";
        if (timeDiff < maxRewardTime * 1000) {
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

function stopSound() {
    try {
        var s = soundManager.getSoundById('alert-sound');
        s.stop();
    } catch (e) {
        // it's fine, there probably was no sound playing
    }
}