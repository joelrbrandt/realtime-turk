var showTime = null;
var showTimeout;
var checkInterval;
var bucket = null;

var MAX_WAIT_SECONDS = 180;

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
    console.log("hiding");
    $('#task-paragraph').hide()
    .after("<div id='retainer' class='task'>In " + MAX_WAIT_SECONDS + " seconds or less, a paragraph will appear here. Act as quickly as you can when it appears to select all the verbs.<br/><br/><img src='media/preview.png' /></div>");
    
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
            showText();
        }
    }, waitTime);
    
    /*
    window.setTimeout( function() {
        $('#retainer').html('<div style="font-size: 30pt; color:red;">5 seconds left</div>').effect('shake', { times: 5 }, 300);
    }, waitTime - 5000);
    */
}

function checkForTest() {
    $.get('http://flock.csail.mit.edu/rts/msbernst/testtimer?workerid=' + workerid + '&experimentid=' + experiment + '&textid=' + TEST_TEXT_ID, function(data) {
        if (data['test']) {
            window.clearTimeout(checkInterval);
            window.clearTimeout(showTimeout);
            textid = TEST_TEXT_ID;
            bucket = parseDate(data['bucket'])
            insertText(data);
            console.log("showing test text")
            showText();
        } else {
            checkInterval = window.setTimeout(checkForTest, 1000);
        }
    });
}

// Shows the text to the user
function showText() {
    if (assignmentid != 0) {
        $('#donebtn').attr("disabled", "").html("Done");    
    }
    $('#retainer').hide();
    $('#task-paragraph').show().effect('highlight', {}, 3000);
    showTime = getServerTime();
    logEvent("display", { 'showTime': showTime }, null);    
    
    alert('Start now!');
    // log immediately after they click the OK button
    logEvent("clickalert");
    
}