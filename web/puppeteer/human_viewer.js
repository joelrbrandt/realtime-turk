function loadPoints(str) {
    points_new = eval(str);
    for (var i = 0; i < points_new.length; i++) {
	for (p in points_new[i]) {
	    points[i][p].x =  points_new[i][p].x
	    points[i][p].y =  points_new[i][p].y
	}
	vis[i].render();
    }


}

