/*
 * Retainer Library for Mechanical Turk
 * http://people.csail.mit.edu/msbernst/
 *
 * 2011-2012, Michael Bernstein, Joel Brandt, David Karger, Rob Miller
 * MIT Licensed: http://realtime-turk.googlecode.com
 *
 * depends:
 * jquery.countdown.js
 */
 
(function( $ ) {
    $.fn.retainer = function( options ) {
    
        // check for console.log; create an empty function if needed
        try { console.log('Javascript console found.'); } catch(e) { console = { log: function() {} }; }
        // don't cache AJAX: these pings need to all happen
        $.ajaxSetup({ cache: false });

        // Create some defaults, extending them with any options that were provided
        settings = $.extend( {
            'assignmentId':     0, // the HIT assignment id, or 0 if unknown
            'workerId':         0, // the MTurk worker id, or 0 if unknown
            'hitId':            0, // the HIT id, or 0 if unknown
        	'requestURL':       'http://www.foo.com', // the base url to call for requests
	        'taskCallback':     null, // callback function to call when a task is ready: takes a single param (server data)
	        'noTaskCallback':   null, // callback function to call when no task is ready within the allotted wait time
	        'noTaskTimeout':    60 * 5 * 1000 // how many millis to wait for a task to be ready before we give up
        }, options);
        if (settings["assignmentId"] == "ASSIGNMENT_ID_NOT_AVAILABLE") {
            settings["assignmentId"] = 0;
        }       
        
        PING_INTERVAL = 5000;   // how often to tell the server that we're waiting or working
        CHECK_FOR_TASK_INTERVAL = 1000; // how often we ask the server whether there is work
        
        // Maintain state for timing information and timeouts
        this.data('retainer', {
            "times": {           // log of when each action was taken
                "accept": null,       // retainer process starts
                "show": null,         // alert appears
                "go": null            // alert dismissed
            },
            "showTimeout": null, // timer for when we give up and just show a task
            "checkInterval": null, // timer for how often to ping the task server
            "$this": null,    // maintain a pointer to $(this) since we lose its scope once we call a function
        });
        state = this.data('retainer');
        
        // make sure this was only invoked on one object
        if (this.length > 1) {
            console.log("retainer() can only be called on a single object. Check the jQuery selector to make sure it\'s only one object.");
            return;
        }
        
        return this.each(function() {
            state["$this"] = $(this);
            scheduleRetainer();
        });
    };
    
    /* private function declarations for plug-in */
   
    /*
     * Returns true if this HIT is in preview mode
     */
    function isPreview() {
        var assignmentid = settings["assignmentId"];
        return (assignmentid == null || assignmentid == 0 || assignmentid == "ASSIGNMENT_ID_NOT_AVAILABLE");
    }
    
    
    /*
     * Starts testing to see if we have tasks, and starts the timer countdown
     */
    function scheduleRetainer() {
        if (isPreview()) {
            // don't do this in preview mode
            console.log("HIT preview: no retainer scheduled.");
            return;
        }
        state["times"]["accept"] = new Date();
        
        pingStatus();        // let the server know we're waiting
        setTimeoutCallback();   // set a timeout: need a task at least this quickly
        showCountdown();        // populate the wait DIV
        pollDataReady();    // start asking the server if a task is ready    
    }
    
    /*
     * Sets a callback to fire and show the text to the user
     * TODO: update this
     */
    function setTimeoutCallback() {    
        state["showTimeout"] = window.setTimeout(function() {
            // if we haven't already shown work, do it now
            if (times.show == null) {
                console.log("No work within allotted retainer timeout. Canceling retainer.")
                window.clearTimeout(state["checkInterval"]);
                window.clearTimeout(state["showTimeout"]);
                noTaskCallback();
            }
        }, settings["noTaskTimeout"]);
    }
    
    /* 
     * Tells the server that the window is still open, and we are either
     * waiting for a task, working on a task, or waiting to click on the alert
     */
    function pingStatus() {
        // different pings depending on which phase they are in
        if (state["times"]["go"] != null) {
            logEvent("working");
        } else if (state["times"]["show"] != null) {
            logEvent("alerting");    
        } else if (state["times"]["accept"] != null) {
            logEvent("waiting");    
        }
        window.setTimeout(pingStatus, PING_INTERVAL);
    }
    
    /*
     * Starts polling the retainer server to see if there is work, and calls
     * callback when the work is ready
     */
    function pollDataReady() {
        var beginPolling = generatePoll();
        beginPolling();
    } 
     
    /*
     * Returns a function that can be called to start the task polling process
     * TODO: update 
     */
    function generatePoll() {
        var theFunction = function() {
            var theURL = settings["requestURL"] + '/gettask/assignment/' + settings["assignmentId"] + '/';
        
            $.get(theURL, function(returnData) {	
                if (retaurnData['is_ready']) {
                    taskReady(returnData);
                } else {
                    checkInterval = window.setTimeout(generatePoll(), CHECK_FOR_TASK_INTERVAL);
                }
            });
        }
    
        return theFunction;
    }
    
    /*
     * Shows the alert when the task is ready
     */
    function taskReady(returnData) {
        console.log("Task is ready");
        window.clearTimeout(state["checkInterval"]);
        window.clearTimeout(state["showTimeout"]);
        
        state["times"]["show"] = new Date();
        logEvent("alerting");
        
        taskCallback(returnData);    
        playSound();
        alert('Start now!');
        showWork();
    }
    
    /*
     * Called when the user dismisses the alert.
     * Logs timing information.
     */
    function showWork() {
        state["times"]["go"] = new Date();
        logEvent("working");     // log that they're starting the task
        
        state["$this"].html("");    
        
        stopSound();    // stop any alert sound that's playing
        
        // TODO: enable rewards
        /*
        if (isReward) {
            var timeDiff = times.go - times.show;
            
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
            }
            waitDOMElement.html(timeString);
        }
        */
    }
    
    /*
     * Plays the alert sound
     */
    function playSound() {
        try {
            var s = soundManager.getSoundById('alert-sound');
            s.play();
        } catch(e) {
            console.log("sound file not loaded yet, do nothing");
        }
    }
    
    /*
     * Stops the alert sound
     */
    function stopSound() {
        try {
            var s = soundManager.getSoundById('alert-sound');
            s.stop();
        } catch (e) {
            // it's fine, there probably was no sound playing
        }
    }
    
    /*
     * Displays a countdown timer limiting how long it will take the task to appear
     * IT'S THE FINAL COUNTDOWN! (DA NA NA NAAAAH, DA NA NA NA NAAAAAH!)
     */
    function showCountdown() {
        state["$this"].html("<div>Task will arrive at the latest in:</div><div id='retainerCountdown'></div>");
        var waitUntil = new Date();
        waitUntil.setMilliseconds(waitUntil.getMilliseconds() + settings["noTaskTimeout"]);
        $('#retainerCountdown').countdown({until: waitUntil, format: 'MS'});      
    }
    
    
    /*
     * Lets the server know our status
     * eventName: "waiting", "working", "alerting", etc.
     * data: any context-specific JSON to send to the server
     * finishedCallback: any function to call when done logging
     */
    function logEvent(eventName) {
        logEvent(eventName, {}, null);
    }
    
    function logEvent(eventName, detail, finishedCallback) {
        if (detail == null) {
            detail = {};
        }
        
        var logData = {
            event: eventName,
            detail: JSON.stringify(detail), 
            assignmentid: settings["assignmentId"],
            workerid: settings["workerId"],
            hitid: settings["hitId"]
        }
        
        $.post(settings["requestURL"] + "/ping/worker/" + settings["workerId"] + "/assignment/" + settings["assignmentId"] + "/hit/" + settings["hitId"] + "/event/" + eventName + "/", logData,
            function(reply) {
                if (finishedCallback != null) {
                    finishedCallback(reply);
                }
            }
        );
    }
    
})( jQuery );