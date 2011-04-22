var colorMap = new Array();        

$(document).ready(function() {
    $('#taskContainer').append("<button id='replayBtn'>Replay</button>");
    $('#replayBtn').click(replayLog);
});

var assignmentPhases = new Object();

var HYSTERESIS = 2500;
var queryResults;
function replayLog() {
    //$('#replayBtn').attr("disabled", "true");
    
    $('#slider').after('<div id="replayLocations" style="width: ' + $('#slider').css('width') + '; height: 10px;"></div>');
    
    $.getJSON('rts/video/replay?videoid=' + videoid,
        function(data) {
            console.log(data);
            queryResults = data;
            var functionGenerator = function(location) { return function() {
                drawLocation(location);
            }};
            
            var phaseGenerator = function(callbackPhase, is_advance_notice) { return function() {
                if (!is_advance_notice) {
                    phase = callbackPhase;
                    updateSliderBackgroundRange();
                    console.log("New phase! " + phase['phase'] + " [" + phase['min'] + ", " + phase['max'] + ")")
                } else {
                    warnPhase(callbackPhase);
                }
            }};
            
            var startTime = data[0]['start']
            
            for (var i=0; i<data.length; i++) {
                var curPhase = data[i];
                var phaseWait = (curPhase['start'] - startTime) * 1000;

                window.setTimeout(phaseGenerator(curPhase, true), phaseWait - HYSTERESIS);  // hysteresis
                window.setTimeout(phaseGenerator(curPhase, false), phaseWait);
                
                var locations = curPhase['locations'];
                for(var j=0; j<locations.length; j++) {
                    var location = locations[j];
                    var waitTime = (location['servertime'] - startTime) * 1000;
                    
                    window.setTimeout(functionGenerator(location), waitTime - ANIMATION_TIME);
                }
            }
        });
}


function getColor(assignmentid) {
    if (colorMap[assignmentid] == null) {
        colorMap[assignmentid] = getRandomColor();
    }
    return colorMap[assignmentid];
}


function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.round(Math.random() * 15)];
    }
    return color;
}

var MARK_WIDTH = 1.0;
var ANIMATION_TIME = 500;
function drawLocation(location) {
    color = getColor(location['assignmentid']);
    
    
    if ($('#' + location['assignmentid']).length == 0) {
        $('#replayLocations').append('<div id="' + location['assignmentid'] + '" class="replayMark" style="background-color: ' + color + '; width: ' + MARK_WIDTH + '%;" />');
        assignmentPhases[location['assignmentid']] = location['phase'];
    }
    
    var left = (location['location'] * 100) - MARK_WIDTH/2;
    $('#' + location['assignmentid']).animate( { "left": left + "%" }, ANIMATION_TIME, 'linear', function() { console.log(location['location'] + " " + location['assignmentid'] + " " + location['servertime']); });//.effect('pulsate', {times: 1}, 100);
    
    if (location['phase'] != assignmentPhases[location['assignmentid']]) {
        $('#' + location['assignmentid']).effect("highlight", {times: 1}, ANIMATION_TIME);
        assignmentPhases[location['assignmentid']] = location['phase'];
    }
    
    //$('#slider').slider("value", location * 100);    
    //seekVideoToPercent(location);
}


var startCountdown;
function warnPhase(phase) {
    console.log('phase warning: ' + (phase['start'] - (HYSTERESIS / 1000.0)) );
    var width = (phase['max'] - phase['min']) * 100; // percent
    
    $('#replayLocations').append("<div id='replayWarning' class='replayMark' style='background-color: yellow; width: " + width + "%; left: " + phase['min'] * 100 + "%;'>2500</div>");
    window.setTimeout(function() { $('#replayWarning').remove(); }, HYSTERESIS);
    
    startCountdown = new Date();
    updateCountdown();
}

function updateCountdown() {
    var diff = HYSTERESIS - ((new Date()) - startCountdown);;
    $('#replayWarning').html(diff);
    
    if (diff > 0) {
        window.setTimeout(updateCountdown, 100);
    }
}