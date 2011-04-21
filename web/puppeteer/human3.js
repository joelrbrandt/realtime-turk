var w = 300;
var h = 475;
var TOTAL_HUMANS = 3;
var POINTS_THAT_MUST_BE_MOVED = 4;

var ALERT_AFTER_DONE = 4; // setting greater than TOTAL_HUMANS turns off alert
var hasAlerted = false;


var points_orig = {
    head : {x: 20, y: 10},
    neck : {x: 20, y: 20},
    lshoulder : {x: 5, y: 20},
    rshoulder : {x: 35, y: 20},
    lelbow : {x: 5, y: 30},
    relbow : {x: 35, y: 30},
    lhand : {x: 5, y: 40},
    rhand : {x: 35, y: 40},
    waist : {x: 20, y: 37},
    lhip : {x: 13, y: 45},
    rhip : {x: 27, y: 45},
    lknee : {x: 13, y: 60},
    rknee : {x: 27, y: 60},
    lfoot : {x: 13, y: 75},
    rfoot : {x: 27, y: 75}
};

// embiggen the points
for (p in points_orig) {
    points_orig[p].x = points_orig[p].x * 5 + 50;
    points_orig[p].y = points_orig[p].y * 5 + 25;
}


var points = []

for (var i = 0; i < TOTAL_HUMANS; i++) {
    points[i] = {}
    for (p in points_orig) {
	points[i][p] = { x : points_orig[p].x, y : points_orig[p].y };    
    }
}


var vis = []

function resetPuppet(n) {
    for (p in points_orig) {
	points[n][p].x = points_orig[p].x;
	points[n][p].y = points_orig[p].y;
    }
    vis[n].render();
    checkDone();
}

function jsonifyPuppets() {
    return JSON.stringify(points);
}

function addPoint(p, n) {
    vis[n].add(pv.Dot)
    .data([p])
    .left(function(d) { return d.x } )
    .top( function(d) { return d.y } ) 
    .radius(10)
    .cursor("move")
    .strokeStyle("#1f77b4")
    .fillStyle(function() { return this.strokeStyle().alpha(.2) })
    .event("mousedown", pv.Behavior.drag())
    .event("mouseup", checkDone)
    .event("drag", vis[n]);

}

function addLine(start, end, n) {
    vis[n].add(pv.Line)
    .data([ start, end ] )
    .left(function(d) { return d.x })
    .top(function(d) { return d.y })
    .interpolate("linear")
    .segmented(false)
    .strokeStyle("#1f77b4")
    .lineWidth(2);

}

function alertWithNewInstructions() {
    var n = new Date();
    
    var alertMessage = "Message from the requestor:\n\n<" + n.toLocaleTimeString() + "> Looking great so far! Could you please make the last one look like he is jumping? Thanks!"

    alert(alertMessage);
    hasAlerted = true;

}

function checkDone() {
    console.log("checking done");
    logEvent("points", points)
    result = false;

    var n_done = 0;

    for (var i = 0; i < TOTAL_HUMANS; i++) {
	var count = 0;
	for (p in points_orig) {
	    if (points_orig[p].x != points[i][p].x || points_orig[p].y != points[i][p].y) {
		count++;
	    }
	}
	if (count >= POINTS_THAT_MUST_BE_MOVED) {
	    n_done++
	}
    }

    result = (n_done == TOTAL_HUMANS);

    if (result) {
	$("#donepuppeting").attr("disabled", "");
	$("#donewarning").hide()
    } else {
	$("#donepuppeting").attr("disabled", "disabled");
	$("#donewarning").show()
    }

    if (n_done >= ALERT_AFTER_DONE && !hasAlerted) {
	alertWithNewInstructions();
    }

    return result;

}

function createHuman(n) {
    vis[n] = new pv.Panel()
    .width(w)
    .height(h)
    .fillStyle("#fff")
    .strokeStyle("#ccc")
    .lineWidth(4)
    .antialias(false)
    .margin(2);

    var thepoints = points[n]


    addLine(thepoints.head, thepoints.neck, n);

    addLine(thepoints.neck, thepoints.lshoulder, n);
    addLine(thepoints.lshoulder, thepoints.lelbow, n);
    addLine(thepoints.lelbow, thepoints.lhand, n);

    addLine(thepoints.neck, thepoints.rshoulder, n);
    addLine(thepoints.rshoulder, thepoints.relbow, n);
    addLine(thepoints.relbow, thepoints.rhand, n);

    addLine(thepoints.neck, thepoints.waist, n);

    addLine(thepoints.waist, thepoints.lhip, n);
    addLine(thepoints.lhip, thepoints.lknee, n);
    addLine(thepoints.lknee, thepoints.lfoot, n);

    addLine(thepoints.waist, thepoints.rhip, n);
    addLine(thepoints.rhip, thepoints.rknee, n);
    addLine(thepoints.rknee, thepoints.rfoot, n);

    for (p in thepoints) {
	addPoint(thepoints[p], n);
    }


    vis[n].render();

}
