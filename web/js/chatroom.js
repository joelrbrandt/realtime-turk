function initChatroom() {
    if (!isChatroom) {
        return;
    }
    
    //addChatroom();
}

function addChatroom() {
    $('#chatContainer').html('<div>Here is a chatroom with other Turkers working on or waiting for this task.</div><div style="width:550px"><style>.mcrmeebo { display: block; background:url("http://widget.meebo.com/r.gif") no-repeat top right; } .mcrmeebo:hover { background:url("http://widget.meebo.com/ro.gif") no-repeat top right; } </style><object width="550" height="415"><param name="movie" value="http://widget.meebo.com/mcr.swf?id=uzDRxbSerk"></param><embed src="http://widget.meebo.com/mcr.swf?id=uzDRxbSerk" type="application/x-shockwave-flash" width="550" height="415" /></object><a target="_blank" href="http://www.meebo.com/rooms/" class="mcrmeebo"><img alt="Create a Meebo Chat Room" src="http://widget.meebo.com/b.gif" width="550" height="45" style="border:0px"/></a></div>');
}