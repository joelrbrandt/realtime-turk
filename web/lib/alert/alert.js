soundManager.url = 'lib/alert/swf/'; // directory where SM2 .SWFs live

// Beta-ish HTML5 audio support (force-enabled for iPad), flash-free sound for Safari + Chrome. Enable if you want to try it!
// soundManager.useHTML5Audio = true;

// do this to skip flash block handling for now. See the flashblock demo when you want to start getting fancy.
soundManager.useFlashBlock = false;

// disable debug mode after development/testing..
// soundManager.debugMode = false;

soundManager.onready(function() {

  // SM2 has loaded - now you can create and play sounds!
    var mySound = soundManager.createSound({
	id: 'alert-sound',
	url: 'media/alert.mp3',
	loops: 3,
	autoLoad: true
	// onload: [ event handler function object ],
    // other options here..
    });
    

});

soundManager.ontimeout(function() {

    // (Optional) Hrmm, SM2 could not start. Show an error, etc.?

});