<?php

date_default_timezone_set('America/New_York');
$datestring = date(c);

$json = "{ \"date\": \"" . $datestring . "\" }";
header('Content-type: application/json');
echo $json;

?>