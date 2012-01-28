var ENDPOINT_NUM_ON_RETAINER = 	'rts/numretainer'
var ENDPOINT_GET_VIDEOS = 'rts/video/getvideos'
var ENDPOINT_ENABLE_VIDEO = 'rts/video/enable'
var ENDPOINT_DISABLE_VIDEO = 'rts/video/disable'
var ENDPOINT_CURRENT_LOCATIONS = 'rts/video/currentposition'

$(document).ready(function() {
    getVideos();
    updateRetainerCount();
    $('button').button( { 'disabled': true } );
    $('#showreset').click(function() { $('#resetlist').show() } )
});

function getVideos() {
    $.get(ENDPOINT_GET_VIDEOS, function(data) {
	for (var i=0; i<data.length; i++) {
	    var newVideo = $("<div><a href='#'>" + data[i]['filename'] + "</a></div>");
	    newVideo.data('info', data[i]);

	    if (data[i]['enabled'] || data[i]['hasphotos']) {
		$(newVideo).click(function() { 
		    disableVideo($(this).data('info')['videoid']);
		});
		$('#resetlist').append(newVideo);
	    }
	    else {
		$(newVideo).click(function() { 
		    loadVideo($(this).data('info'));
		});
		$('#videolist').append(newVideo);
	    }
	}
    });
}

function updateRetainerCount()
{
    var numOnRetainer = getNumOnRetainer();
    window.setTimeout(updateRetainerCount, 3000);
}

function getNumOnRetainer()
{
    $.get(ENDPOINT_NUM_ON_RETAINER, function(data) {
	var numWaiting = data['num_waiting'];
	var toWrite = numWaiting + " worker";
	if (numWaiting > 1 || numWaiting == 0) {
	    toWrite = toWrite + "s";
	}
	toWrite = toWrite + " on retainer.";

	$('#retainerCount').text(toWrite);
    });
}

function loadVideo(videoData) {
    console.log(videoData)
    videoDataCallback(videoData);
    $('button').button('enable').click(function(e) {
	enableVideo(videoid);
    });
}

function disableVideo(videoid) {
    $.get(ENDPOINT_DISABLE_VIDEO + "?videoid=" + videoid, function(data) {
	console.log("disabled");
	location.reload(true)

    });
}

function enableVideo(videoid) {
    $.get(ENDPOINT_ENABLE_VIDEO + "?videoid=" + videoid, function(data) {
	console.log("Video enabled");
	$('#slider').after('<div id="replayLocations" style="width: ' + $('#slider').css('width') + '; height: 10px;"></div>');
    	getLocations();
    });
}

var LOCATION_REQUEST_TIME = 100;
function getLocations() {
    $.get(ENDPOINT_CURRENT_LOCATIONS + "?videoid=" + videoid, function(data) {
	drawLocations(data);
    });
    window.setTimeout(getLocations, LOCATION_REQUEST_TIME);
}

var colorMap = new Array();        
var currentPositions = new Array();
var assignmentPhases = new Object();

var curPhase = null;
function drawLocations(data) {
    
    if (phase['phase'] != data['phase']) {
	phase = data;
        updateSliderBackgroundRange(phase);
        console.log("New phase! " + phase['phase'] + " [" + phase['min'] + ", " + phase['max'] + ")")
    }
    
    for (var i=0; i<data['locations'].length; i++) {
        var location = data['locations'][i];
	if (currentPositions[location['assignmentid']] != location['location']) {
	    currentPositions[location['assignmentid']] = location['location'];
	    drawLocation(location['location'], location['assignmentid'])
	}
    }
}

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.round(Math.random() * 15)];
    }
    return color;
}

function getColor(assignmentid) {
    if (colorMap[assignmentid] == null) {
        colorMap[assignmentid] = getRandomColor();
    }
    return colorMap[assignmentid];
}

var MARK_WIDTH = 3.0;
var ANIMATION_TIME = LOCATION_REQUEST_TIME;
function drawLocation(location, assignmentid) {
    color = getColor(assignmentid);

    if ($('#' + assignmentid).length == 0) {
        $('#replayLocations').append('<div id="' + assignmentid + '" class="replayMark" style="background-color: ' + color + '; width: ' + MARK_WIDTH + '%;" />');
    }
    
    var left = (location * 100) - MARK_WIDTH/2;
    $('#' + assignmentid).stop().animate( { "left": left + "%" }, ANIMATION_TIME, 'linear');
}

/**
 * Colors the slider and prevents it from 
 * moving outside the given range
 */
function updateSliderBackgroundRange(updatePhase) {
   if (!updatePhase) {
        updatePhase = phase;    // use current phase
    }

    var left = updatePhase['min'] * 100;
    var width = (updatePhase['max'] - updatePhase['min']) * 100; // percent
    $(".range").css( { "left": left + "%", 
                        "width": width + "%" } )
    
    if (width < 5) {
        $(".range.below").text("");
    }    
    else if (width < 10) {
        $(".range.below").text("clip");
    }    
    else if (width < 20) {
        $(".range.below").text("In this clip");
    }

    // make sure the slider's current position is in range
    var slider = $('#slider');
    var currentValue = slider.slider('value');
    var minSlider = (updatePhase['min'] * SLIDER_MAX);
    var maxSlider = (updatePhase['max'] * SLIDER_MAX);
    if (currentValue < minSlider || currentValue > maxSlider) {
        setRandomFrame();
    }
}

/**
 * Sets the video to a random frame when it finishes loading
 */
function setRandomFrame() {
    var duration = $f().getClip().fullDuration;    
    var rand = getRandomArbitrary(phase['min'], phase['max']);
    
    $('#slider').slider("value", rand * 100);
    $f().seek(duration * rand).getPlugin("play").hide();
}