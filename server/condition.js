/**
 * Determines which condition this worker sees.
 */
 
var isAlert;
var alertURL = $(document).getUrlParam("alert");
if (alertURL == null || alertURL == "") {
    isAlert = ${str(workerid_is_alert).lower()};
} else {
    isAlert = (alertURL === '1');
}

var isReward;
var rewardURL = $(document).getUrlParam("reward");
if (rewardURL == null || rewardURL == "") {
    isReward = ${str(workerid_is_reward).lower()};
}
else {
    isReward = (rewardURL === '1');    
}
