var showTime = null;
var showTimeout;
var checkInterval;
var bucket = null;

// Hides the text from the user
function retainerHide() {
    console.log("hiding");
    $('#task-paragraph').hide()
    .after("<div id='retainer' class='task'>In thirty seconds or less, a paragraph will appear here. Act as quickly as you can when it appears to select all the verbs.<br/><br/><img src='media/preview.png' /></div>");
    
    $('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
}

// Sets a callback to fire and show the text to the user
function setRetainerCallback() {
    if (showTime == null) { 
        //var waitTime = Math.floor(Math.random()*30) * 1000;
        var waitTime = 30 * 1000; 
    } else {
        var waitTime = showTime - getServerTime();
        console.log("presetting wait time");
    }
    console.log("wait time: " + waitTime);
    window.setTimeout(function() {
        if (checkInterval != null) {
            window.clearInterval(checkInterval);
            showText();
        }
    }, waitTime);
    
    /*
    window.setTimeout( function() {
        $('#retainer').html('<div style="font-size: 30pt; color:red;">5 seconds left</div>').effect('shake', { times: 5 }, 300);
    }, waitTime - 5000);
    */
}

// Sets a specific textid if we are near the regular firing period,
// and sets the firing time to be exactly on the dot of the firing period
function scheduleRetainer() {
    if (assignmentid == 0) {
        // don't do this in preview mode
        return;
    }
    checkForTest();
    /*
    if (retainerType == "5min") {
        var minToFire = 1;
        
        var curTime = getServerTime();
        var modTime = curTime.getTime() % (60 * 1000 * minToFire);
        console.log("mod time is " + modTime);
        if (modTime < (30 * 1000)) {   // the random call can only go up to 29 secs
            showTime = curTime.add((30*1000) - modTime).milliseconds()
            console.log("fire at " + showTime);
        }
    }
    */
}

function checkForTest() {
    $.get('http://needle.csail.mit.edu/rts/msbernst/testtimer?workerid=' + workerid + '&experimentid=' + experiment + '&textid=' + TEST_TEXT_ID, function(data) {
        if (data['test']) {
            window.clearInterval(checkInterval);
            window.clearTimeout(showTimeout);
            textid = TEST_TEXT_ID;
            bucket = parseDate(data['bucket'])
            insertText(data);
            console.log("showing test text")
            showText();
        }
    });
    checkInterval = window.setTimeout(checkForTest, 1000);
}

// Shows the text to the user
function showText() {
    if (assignmentid != 0) {
        $('#donebtn').attr("disabled", "").html("Done");    
    }
    $('#retainer').hide();
    $('#task-paragraph').show().effect('highlight', {}, 3000);
    showTime = getServerTime();
}