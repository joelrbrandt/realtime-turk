var w = 300;
var h = 475;

var points = {
    head : {x: 20, y: 10},
    neck : {x: 20, y: 20},
    lshoulder : {x: 5, y: 20},
    rshoulder : {x: 35, y: 20},
    lelbow : {x: 5, y: 30},
    relbow : {x: 35, y: 30},
    lhand : {x: 5, y: 40},
    rhand : {x: 35, y: 40},
    waist : {x: 20, y: 37},
    lhip : {x: 10, y: 45},
    rhip : {x: 30, y: 45},
    lknee : {x: 10, y: 60},
    rknee : {x: 30, y: 60},
    lfoot : {x: 10, y: 75},
    rfoot : {x: 30, y: 75}
};

for (p in points) {
    points[p].x = points[p].x * 5 + 50;
    points[p].y = points[p].y * 5 + 25;
}


points_orig = {}

for (p in points) {
    points_orig[p] = { x : points[p].x, y : points[p].y };
}

function resetPuppet() {
    for (p in points) {
	points[p].x = points_orig[p].x;
	points[p].y = points_orig[p].y;
    }
    vis.render()
}

function jsonifyPuppet() {
    return JSON.stringify(points);
}

function addPoint(p) {
    vis.add(pv.Dot)
	.data([p])
	.left(function(d) { return d.x } )
	.top( function(d) { return d.y } ) 
	.radius(10)
	.cursor("move")
	.strokeStyle("#1f77b4")
	.fillStyle(function() { return this.strokeStyle().alpha(.2) })
	.event("mousedown", pv.Behavior.drag())
	.event("drag", vis);

}

function addLine(start, end) {
    vis.add(pv.Line)
	.data([ start, end ] )
	.left(function(d) { return d.x })
	.top(function(d) { return d.y })
	.interpolate("linear")
	.segmented(false)
	.strokeStyle("#1f77b4")
	.lineWidth(2);

}


var vis = new pv.Panel()
    .width(w)
    .height(h)
    .fillStyle("#fff")
    .strokeStyle("#ccc")
    .lineWidth(4)
    .antialias(false)
    .margin(2);


addLine(points.head, points.neck);

addLine(points.neck, points.lshoulder);
addLine(points.lshoulder, points.lelbow);
addLine(points.lelbow, points.lhand);

addLine(points.neck, points.rshoulder);
addLine(points.rshoulder, points.relbow);
addLine(points.relbow, points.rhand);

addLine(points.neck, points.waist);

addLine(points.waist, points.lhip);
addLine(points.lhip, points.lknee);
addLine(points.lknee, points.lfoot);

addLine(points.waist, points.rhip);
addLine(points.rhip, points.rknee);
addLine(points.rknee, points.rfoot);

for (p in points) {
    addPoint(points[p]);
}


vis.render();
