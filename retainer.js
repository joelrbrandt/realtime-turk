var showTime = null;

function retainerHide() {
    console.log("hiding");
    $('#task-paragraph').hide()
    .after("<div id='retainer' class='task'>In thirty seconds or less, a paragraph will appear here. Act as quickly as you can when it appears to select all the verbs.<br/><br/><img src='media/preview.png' /></div>");
    $('#donebtn').attr("disabled", "true").html("HIT will be submittable after job appears");
}

function setShowCallback() {
    var waitTime = Math.floor(Math.random()*30) * 1000;
    console.log("wait time: " + waitTime);
    window.setTimeout( function() {
        $('#donebtn').attr("disabled", "").html("Done");    
        $('#retainer').hide();
        $('#task-paragraph').show().effect('highlight', {}, 3000);
        showTime = getServerTime();
    }, waitTime);
    
    window.setTimeout( function() {
        $('#retainer').html('<div style="font-size: 30pt; color:red;">5 seconds left</div>').effect('shake', { times: 5 }, 300);
    }, waitTime - 5000);
}