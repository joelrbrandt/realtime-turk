var w = 100;
var h = 100;

var points = {
    pointA : {x: 20, y: 20},
    pointB : {x: 80, y: 70}
};

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


addLine(points.pointA, points.pointB);

for (p in points) {
    addPoint(points[p]);
}


vis.render();
