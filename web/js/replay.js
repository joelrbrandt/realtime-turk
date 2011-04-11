var colorMap = new Array();        

$(document).ready(function() {
    $('#taskContainer').append("<button id='replayBtn'>Replay</button>");
    $('#replayBtn').click(replayLog);
});

function replayLog() {
    $('#replayBtn').attr("disabled", "true");
    
    $('#slider').after('<div id="replayLocations" style="width: ' + $('#slider').css('width') + '; height: 10px;"></div>');
    
    $.getJSON('rts/video/replay?videoid= ' + videoid,
        function(data) {
            console.log(data);
            var functionGenerator = function(location) { return function() {
                drawLocation(location['location'], location['assignmentid']);
            }};
            
            var phaseGenerator = function(callbackPhase) { return function() {
                phase = callbackPhase;
                updateSliderBackgroundRange();
            }};
            
            var startTime = data[0]['start']
            
            for (var i=0; i<data.length; i++) {
                var curPhase = data[i];
                var phaseWait = (curPhase['start'] - startTime) * 1000;
                
                window.setTimeout(phaseGenerator(curPhase), phaseWait);
                
                var locations = curPhase['locations'];
                for(var j=0; j<locations.length; j++) {
                    var location = locations[j];
                    var waitTime = (location['servertime'] - startTime) * 1000;
                    
                    window.setTimeout(functionGenerator(location), waitTime);
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
function drawLocation(location, assignmentid) {
    color = getColor(assignmentid);
    console.log(location + " " + color);
    
    if ($('#' + assignmentid).length == 0) {
        $('#replayLocations').append('<div id="' + assignmentid + '" class="replayMark" style="background-color: ' + color + '; width: ' + MARK_WIDTH + '%;" />');
    }
    
    var left = (location * 100) - MARK_WIDTH/2;
    $('#' + assignmentid).css( { "left": left + "%" } )
    
    //$('#slider').slider("value", location * 100);    
    //seekVideoToPercent(location);
}