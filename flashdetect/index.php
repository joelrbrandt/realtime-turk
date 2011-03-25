<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Click the button</title>
<link href="flashdetect.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>    
<script type="text/javascript" src="flash_detect_min.js"></script>
<script type="text/javascript">
var assignmentId = 0;
<?php
if(isset($_GET["assignmentId"]) && ($_GET["assignmentId"] != "ASSIGNMENT_ID_NOT_AVAILABLE")) {
  echo "assignmentId=\"" . $_GET["assignmentId"] . "\";";
}
?>

$(function() {
  $("#flash_major_version").val(FlashDetect.major);
  $("#flash_minor_version").val(FlashDetect.minor);
  var b = $("#form_submit");
  if (assignmentId != 0) {
    b.val("Click Me!");
    b.removeAttr("disabled");
    $("#assignmentId").val(assignmentId);
  }
});


</script>
</head>
<body>
<h1>Please click the button below</h1>
<p>Yes, that's the entire task. Thanks!</p>
<div id="task-paragraph">
<form id="mturk_form" method="POST" action="http://www.mturk.com/mturk/externalSubmit">
<input type="hidden" id="assignmentId" name="assignmentId" value="">
<input type="hidden" id="user_agent" name="user_agent" value="<?=$_SERVER['HTTP_USER_AGENT']?>"/></p>
<input type="hidden" id="ip_address" name="ip_address" value="<?=$_SERVER['REMOTE_ADDR']?>"/></p>
<input type="hidden" id="flash_major_version" name="flash_major_version" value=""/></p>
<input type="hidden" id="flash_minor_version" name="flash_minor_version" value=""/></p>
<p><input type="submit" value="Click Me! [Will be enabled in actual HIT]" id="form_submit" name="form_submit" disabled="true"></p>
</form>
</div>
</body>
</html>
