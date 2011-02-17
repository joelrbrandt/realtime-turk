var colorMap = new Array();        

function replayLog(textid) {
    $.get('http://needle.csail.mit.edu/realtime/log-replay.cgi?textid=' + textid + '&trial=' + trial,
        function(data) {
            data.sort(function(a, b) { return a.time - b.time });
            
            // first figure out colors
            $.map(data, function(elem, index) {
                if (colorMap[elem.assignmentid] == null) {
                    colorMap[elem.assignmentid] = getRandomColor();
                }
            });
            
            var functionGenerator = function(click) { return function() {
                drawClick(click.wordid, click.highlighted == "1", colorMap[click.assignmentid]);
            }};                    
            
            for(var i=0; i<data.length; i++) {
                var click = data[i];
                var waitTime = (click.time - data[0].time) * 1000;
                waitTime = waitTime / 10;
                
                window.setTimeout(functionGenerator(click), waitTime);
            }
        });
}

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.round(Math.random() * 15)];
    }
    return color;
}

function drawClick(wordId, isHighlighted, color, assignmentid) {
    console.log(wordId + " " + isHighlighted + " " + color);
    $('#word' + wordId).effect("highlight", { color: color }, 3000);
}