SHRINK_FACTOR = 3.0;
SPEEDFACTOR = 1;
START_TIME_OFFSET = 3000;

function addPoint(p, vis) {
    vis.add(pv.Dot)
    .data([p])
    .left(function(d) { return d.x } )
    .top( function(d) { return d.y } ) 
    .radius(3)
    .cursor("move")
    .strokeStyle("#1f77b4")
    .fillStyle(function() { return this.strokeStyle().alpha(.2) })
}

function addLine(start, end, vis) {
    vis.add(pv.Line)
    .data([ start, end ] )
    .left(function(d) { return d.x })
    .top(function(d) { return d.y })
    .interpolate("linear")
    .segmented(false)
    .strokeStyle("#1f77b4")
    .lineWidth(1);

}

function shrinkPoints(points) {
    for (p in points) {
	points[p].x = points[p].x / SHRINK_FACTOR
	points[p].y = points[p].y / SHRINK_FACTOR
    }
}


function drawPuppet(thepoints, theid) {
    var w = Math.ceil(300 / SHRINK_FACTOR);
    var h = Math.ceil(475 / SHRINK_FACTOR);


    var vis = new pv.Panel()
    .width(w)
    .height(h)
    .fillStyle("#fff")
    .strokeStyle("#c00")
    .lineWidth(2)
    .antialias(false)
    .margin(2)
    .canvas(theid);
    
    addLine(thepoints.head, thepoints.neck, vis);

    addLine(thepoints.neck, thepoints.lshoulder, vis);
    addLine(thepoints.lshoulder, thepoints.lelbow, vis);
    addLine(thepoints.lelbow, thepoints.lhand, vis);

    addLine(thepoints.neck, thepoints.rshoulder, vis);
    addLine(thepoints.rshoulder, thepoints.relbow, vis);
    addLine(thepoints.relbow, thepoints.rhand, vis);

    addLine(thepoints.neck, thepoints.waist, vis);

    addLine(thepoints.waist, thepoints.lhip, vis);
    addLine(thepoints.lhip, thepoints.lknee, vis);
    addLine(thepoints.lknee, thepoints.lfoot, vis);

    addLine(thepoints.waist, thepoints.rhip, vis);
    addLine(thepoints.rhip, thepoints.rknee, vis);
    addLine(thepoints.rknee, thepoints.rfoot, vis);

    for (p in thepoints) {
	addPoint(thepoints[p], vis);
    }


    vis.render();

    return {vis: vis, points:thepoints};

}

function logMessage(s) {
    $("#msg").append(s + "<br/>"); 
    $("#msg").attr({ scrollTop: $("#msg").attr("scrollHeight") });
}



/// everything below this line operates on globals

var animationStruct = {};
var vises = {};
var animationTimes = [];

$(function() {
    logMessage("rescaling all points...");
    setTimeout(rescaleAllPoints, 100);

});


function rescaleAllPoints() {

    for (var i = 0; i < thepoints.length; ++i) {
	for (var j = 0; j < thepoints[i].points.length; ++j) {
	    shrinkPoints(thepoints[i].points[j]);
	}
    }

    logMessage("...done");
    logMessage("Making animation struct...");

    setTimeout(makeAnimationStruct, 100);

}


function makeAnimationStruct() {

    timeOffset = thepoints[0].servertime

    logMessage("timeOffset: " + timeOffset) 

    for (var i = 0; i < thepoints.length; ++i) {
	var t = Math.floor((thepoints[i].servertime - timeOffset) * (1000/SPEEDFACTOR))
	while (animationStruct[t] !== undefined)
	    t++;
	animationStruct[t] = makeAddOrUpdateFunction(thepoints[i].assignmentid, thepoints[i].points)
    }

    for (var i = 0; i < thesubmissions.length; ++i) {
	var t = Math.floor((thesubmissions[i].submit - timeOffset) * (1000/SPEEDFACTOR))
	while (animationStruct[t] !== undefined)
	    t++;
	animationStruct[t] = makeCompleteFunction(thesubmissions[i].assignmentid);
    }

    logMessage("...done");
    logMessage("scheduiling Animation...");

    setTimeout(scheduleAnimation, 100);

}


function scheduleAnimation() {
    
    for (t in animationStruct) {
	animationTimes.push(parseInt(t))
    }
    
    animationTimes.sort(function(a,b){return b-a})  // sorts in reverse numerical order so we can pop off the times

   logMessage("...done. Starting animation in " + START_TIME_OFFSET + " millis");



}

function makeCompleteFunction(assignmentid) {
    var lassignmentid = assignmentid;

    return function() {
	if (vises[lassignmentid] !== undefined) {
	    for (var i = 0; i < vises[lassignmentid].length; ++i) {
		vises[lassignmentid][i].vis.strokeStyle("#ccc");
		vises[lassignmentid][i].vis.render();
	    }
	}
    }
}

function makeAddOrUpdateFunction(assignmentid, points) {
    var lassignmentid = assignmentid;
    var lpoints = points
    
    console.log("the lassignmentid is: " + lassignmentid)

    if (vises[lassignmentid] === undefined) {

	return function() {
	    vises[lassignmentid] = [];

	    theid = lassignmentid + "_0";
	    $("#allfigs").append("<div class='fig' id='" + theid + "'></div>");
	    vises[lassignmentid].push(drawPuppet(lpoints[0], theid));
	    
	    theid = lassignmentid + "_1";
	    $("#allfigs").append("<div class='fig' id='" + theid + "'></div>");
	    vises[lassignmentid].push(drawPuppet(lpoints[1], theid));
	    
	    theid = lassignmentid + "_2";
	    $("#allfigs").append("<div class='fig' id='" + theid + "'></div>");
	    vises[lassignmentid].push(drawPuppet(lpoints[2], theid));

	    $("#allfigs").attr({ scrollTop: $("#allfigs").attr("scrollHeight") });

	}
    }
    else { // already defined
	return function() {
	    for (var i = 0; i < lpoints.length; ++i) {
		for (p in lpoints[i]) {
		    vises[lassignmentid][i].points[p].x = lpoints[i][p].x
		    vises[lassignmentid][i].points[p].y = lpoints[i][p].y
		}
	    }
	    vises[lassignmentid].vis.render();
	}
    }
}

function takeStep() {
    var thetime = animationTimes.pop();
    logMessage("Animating: " + thetime);
    animationStruct[thetime].call();
}

function takeOneHundredSteps() {
    for (var i = 0; i < 100; ++i) {
	takeStep();
    }
}