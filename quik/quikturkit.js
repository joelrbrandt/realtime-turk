print("___________________________________");


// URL containing the page you want turkers to work on.
var experimentNum = 29;
var server = 'flock.csail.mit.edu';
var userDir = 'msbernst';
var url = "http://" + server + "/" + userDir + "/word_clicker.mpy?experiment=" + experimentNum + "&retainer=1";

var status_url = "http://" + server + "/" + userDir + "/rts/status?experiment=" + experimentNum;

var title = "Find verbs in a paragraph";
var title2 = "Quick help needed identifying verbs";
var description = "Click to highlight all the verbs in a paragraph";

// Try to keep under this rate per hour.
var maxPerHour = 3.00;

// From 0 to 1.
var aggressiveNess = 0.80;

// Maximum number of seconds until retiring the HIT (seconds).
var maxTimeTillDeath = 60*6;

// How long before we start refreshing HITs.
var maxChurn = 60*8;

// Maximum time to complete one task in a HIT (seconds).
var maxTimePerTask = 90;

// Number of answers really desired for each question.
// Actual number be this much or
var numAnswersDesired = 5;

// Number of workers desired.
var desiredWorkers = 15;

// Number of HITs that should always be posted.
var steadyStateNum = 36;

// Minimum time between adding HITs.
// Number of seconds between deleting and readding HITs -
// setting this too low can cause thrashing, where turkers
// try to accept a HIT but quikturkit has already deleted it.
var minTimeBetweenHITs = 10;

// Number of HITs added at once.
// Maximum number of HITs to add a one time.
var numHITsAtOnce = 4;


// The reward for each HIT.
var reward = 0.03;

// Number of assignments offered in each HIT posted.
var assignments = 4;

//
var numhits = 3;


// Keeps track of new hits for sending to the server.
var newhits = "";


// Array of HIT ids.
var currentHITs = database.query("return currentHITs;");
if(!currentHITs) currentHITs = [];

//
// Start things over before we get going by resetting all HITs.
//
for(var j=0; j<currentHITs.length; j++) {
  var qth = currentHITs[j];
  // try {
  var hit = mturk.getHIT(qth.hitID);
  retireHIT(hit);
  //} catch(e) {
  // print("Failed in getting/retiring HITs initially: " + e);
  //}
}
currentHITs = [];
database.query("currentHITs = " + json(currentHITs));
print("DONE RETIRING: three seconds to quit\n");
Packages.java.lang.Thread.currentThread().sleep(3000);


// Current number of active assignments.
var activeAssignments = 0;


lastLowAnswer = 0;

num_diffs = 0;

//
// The main (infinite) loop.
// Be careful, the only thing stopping you from losing a bundle is the
// global safety values (money spent, number of HITs)
//
for(var i=0; true; i++) {
  print("\n\nITERATION " + i + " (" + currentHITs.length + " hits):");

  // Fetch the number of answers provided for the least-answered item in the database.
  var curr = answersForLowest();
  
  var lowAnswer = curr[0];
  var diff = curr[1];
  var numworkers = curr[2];
  var numlooking = curr[3];


  // Some boosts for when we don't have any answers at all.
  if(lowAnswer == 0) {
    //numHITsAtOnce = 4;
  } else {
    //numHITsAtOnce = 2;
  }

  // Multiplier on extra HITs.
  // At most you should expect to receive (and pay for)
  // overShootMultipler * numAnswersDesired answers.
  var overShootMultiplier = Math.ceil(maxChurn / (6*minTimeBetweenHITs)) * numHITsAtOnce * 2;
  if(lowAnswer >= numAnswersDesired) {
    //overShootMultiplier /= 2;
  }
  /*if(numworkers >= 4) {
    overShootMultiplier -= numHITsAtOnce*numworkers;
    if(overShootMultiplier < 0) overShootMultiplier = 0;
    }*/
  print("OVERSHOOT:  " + overShootMultiplier);



  print("reported low answer: " + lowAnswer);
	
  // If we already have enough answers, then don't worry about creating more.
  /*if(lowAnswer > numAnswersDesired - steadyStateNum) {
    lowAnswer = numAnswersDesired - steadyStateNum;
  }*/

  if(lowAnswer < numAnswersDesired) {
    num_diffs = 0;
  }

  // If someone's interacting with the application and we don't
  // already have some active HITs, seek 1 answer optimistically.
  if(num_diffs < 25 && diff < 40 && lowAnswer > (numAnswersDesired / 2)) {
    lowAnswer = Math.floor(numAnswersDesired / 2);
    num_diffs++;
  }

  if(numworkers < desiredWorkers && lowAnswer > (numAnswersDesired / 2)) {
    lowAnswer = Math.floor(numAnswersDesired / 2);
  }

  // Track the youngest HIT.
  var youngestHIT = 0;

  // Refresh the number of current HITs periodically unless there's
  // been activity on the phone.
  if(lowAnswer < numAnswersDesired || lowAnswer != lastLowAnswer || (i%10==0 && activeAssignments>0)) {
      // Reset activeAssignments for counting next.
      activeAssignments = 0;

      //
      // Review the current HITs to see how many have completed.
      //
      for(var j=currentHITs.length-1; j>=0; j--) {
	//try {
	  var hit = mturk.getHIT(currentHITs[j].hitID);

	  var secs = (time() - hit.creationTime) / 1000;

	  if(hit.creationTime > youngestHIT || youngestHIT == 0) {
	      youngestHIT = hit.creationTime;
	  }

	  // Count active assignments, delete finished HITs.
	  if(hit.done || secs > maxChurn) {
	      // Remove this HIT from our list.
	    var qth = currentHITs.splice(j, 1)
	    retireHIT(hit);
	  } else {
	    //print("Adding: " + (hit.maxAssignments - hit.assignments.length));
	      activeAssignments += (hit.maxAssignments - hit.assignments.length);
	  }
	  //} catch(e) {
	  // print("Error in counting HITs: " + e);
	  //}
      }
  }
  lastLowAnswer = lowAnswer;


  var answersNeeded = numAnswersDesired - lowAnswer;
  if(answersNeeded < 0) {
    if(numAnswersDesired > lowAnswer) {
      answersNeeded = 1;
    } else {
      answersNeeded = 0;
    }
  }

  var multiplier = overShootMultiplier-(numworkers*numHITsAtOnce);
  if(multiplier < 0) {
    multiplier = 0;
  }


  //
  // Add or delete HITs as needed.
  //
  var hitsToAdd = multiplier*answersNeeded - activeAssignments;

  if(hitsToAdd > 0 && activeAssignments == 0) {
    hitsToAdd += numHITsAtOnce;
  } else if(hitsToAdd + activeAssignments <= 0) {
    
  } else if(hitsToAdd < 0 && hitsToAdd < -6) {
    // Only delete a maximum of 6 HITs at a time.
    hitsToAdd = -6;
  }

  print("active: " + activeAssignments + ", toAdd: " + hitsToAdd + ", low: " + lowAnswer + "->" + numAnswersDesired + ", steady@: " + steadyStateNum + ", workers=" + numworkers +":"+numlooking + ",diff=" + diff);



  // How many tasks should new HITs have?
  // The default is 12, but this goes down to 5 or 2 based on how long until we expect to what answers.
  var tasksForNewHits = 3;
  if(lowAnswer < numAnswersDesired) {
    tasksForNewHits = 3;
  } else if(diff < 4*60) {
    tasksForNewHits = 4;
  } else {
    tasksForNewHits = 5;
  }

  // Adjust for HIT creation rate.
  if(time() - youngestHIT < minTimeBetweenHITs*1000) {
    hitsToAdd = 0;
  } else if(hitsToAdd > numHITsAtOnce) {
    hitsToAdd = numHITsAtOnce;
  }


  // 
  if(hitsToAdd > 0) {
    for(var j=0; j<hitsToAdd;) {
      var hits = createNewHIT(reward, assignments, numhits, tasksForNewHits);
      currentHITs = currentHITs.concat(hits);

      // Final number of jobs actually created.
      j+=numhits*assignments;

      print(currentHITs.length + " current HITs, " + hits.length + " new ones created.");
    }
    activeAssignments+=hitsToAdd;
  } else if(hitsToAdd < 0 && currentHITs.length > 0) {
    for(var j=hitsToAdd; j<0; j++) {
      if(currentHITs.length > 0) {
	print("retiring here");
	var qth = currentHITs.shift();
	//try {
	  var hit = mturk.getHIT(qth.hitID);
	  var secs = (time() - hit.creationTime) / 1000;
	  if(secs > 60*10) {
	    retireHIT(hit);
	  }
	  //} catch(e) {
	  // print("Error in retiring HITs due to retire: " + e);
	  //	}
      }
    }
  } else {
    if(activeAssignments==0 && i%10==0) {
      // We're already in a good state, so do nothing.
      // Wait for a little bit before polling again.
      print("deleting all HITs");
      mturk.deleteHITsRaw(mturk.getHITs());
    }
    Packages.java.lang.Thread.currentThread().sleep(1000);
  }

  // Store current currentHITs.
  database.query("currentHITs = " + json(currentHITs));

  // Wait for a little bit before polling again.
  Packages.java.lang.Thread.currentThread().sleep(5000);
}


/**
 * Creates a new HIT with the specified parameters.
 *
 * Returns array of qtHITs created.
 **/
function createNewHIT(reward, assignments, numhits, tasks) {
  var hitsCreated = [];

  // Generate a random number 0-1000;
  salt = Math.floor(Math.random()*4);

  if(typeof tasks == 'undefined') {
    tasks = 2;
  }

  var mytitle = title.replace(/%%n%%/g, tasks);
  if(salt < 2) {
    mytitle = title2.replace(/%%n%%/g, tasks);
  }

  var mydescription = description.replace(/%%n%%/g, tasks);
  var myurl = url.replace(/%%n%%/g, tasks);

  //try {
    for(var i=0; i<numhits; i++) {
      var thisreward = reward + (salt<2 ? 0.01 : 0.00);

      // create a HIT on MTurk using the webpage
      var hitId = mturk.createHITRaw({
	        title : mytitle,
	        desc : mydescription,
    	    keywords: "text verbs reading quick",
            url : myurl,
                height : 1200,
                reward : thisreward,
                assignmentDurationInSeconds: maxTimeTillDeath,
                maxAssignments: assignments,
                autoApprovalDelayInSeconds: 60 * 5,
              });

      var qth = qtHIT(hitId, assignments, thisreward, tasks);
      newhits += "|" + qth.hitID + ":" + qth.assignments + ":" + qth.reward + ":" + tasks;
      hitsCreated.push(qth);


    }
    // } catch(e) {
    // print("Error in createNewHIT: " + e);
    // }

  return hitsCreated;
}

function returnSpaces(num) {
  var str="";
  for(var i=0; i<num; i++) {
    str += " ";
  }
  return str;
}

/**
 *
 * Assumes that there is a web location that we can poll to find out
 * cnt = # of answers provided for least-answered question
 * time = seconds since client last polled
 * numworkers = number of workers that are actively engaged (by some definition)
 *
 */
function answersForLowest() {  
  var ret = [0, 999, 0, 0];

  try {
    print("getting from: " + status_url);
    var content = eval("(" + slurp(status_url) + ")");
    print(content);

    ret = [content.waiting, 999, 0, 0];
  } catch(e) {
    print(e);
    ret = [999,999,0,0];
  }

  /*print("msbernst: changing returned values");
  Packages.java.lang.Thread.currentThread().sleep(1000);  // sleep to not move too fast, pretend network lag. Sometimes things throttle otherwise.
  var ret = [0,999,0,0];
  */
  return ret;
}


/**
 * Function for retiring a HIT.
 **/
function retireHIT(hit) {
  try {
    print("all assignments");
    print(hit.assignments);
    //mturk.approveAssignments(hit.assignments);
    mturk.deleteHITRaw(hit);
    print("Successfully deleted HIT.");
  } catch(e) {
    print("Failed to approve/delete HITs: " + e);
  }
}


function printHITs(hits) {
  foreach(hits, printHIT);
}

function printHIT(hit) {
  try {
    var h = mturk.getHIT(hit.hitID);
    var vals = [h.done, h.assignments.length];
    print(vals.join(','));
  } catch(e) {
    print("Failed to getHIT to printHIT: " + e);
  }
}

function qtHIT(hitID, assignments, reward, tasks) {
  return {hitID: hitID, assignments: assignments, reward: reward, tasks: tasks};
}
