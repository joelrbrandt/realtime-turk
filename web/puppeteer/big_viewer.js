function drawPuppet(thepoints) {
    var w = 300;
    var h = 475;

    function addPoint(p, vis) {
	vis.add(pv.Dot)
	.data([p])
	.left(function(d) { return d.x } )
	.top( function(d) { return d.y } ) 
	.radius(10)
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

    return vis;

}
