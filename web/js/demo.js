var ENDPOINT_NUM_ON_RETAINER = 	'rts/numretainer'
var ENDPOINT_GET_VIDEOS = 'rts/video/getvideos'

$(document).ready(function() {
    getVideos();
    updateRetainerCount();
});

function getVideos() {
    $.get(ENDPOINT_GET_VIDEOS, function(data) {
	for (var i=0; i<data['videos'].length; i++) {
	    console.log("write video out with link to enable")
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