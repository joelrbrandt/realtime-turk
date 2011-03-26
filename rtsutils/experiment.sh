#!/bin/bash

# START of experimental variables

EXPERIMENT_NUMBER=51  # what we put in the DB as the experiment number
HITS_PER_ITERATION=10
BUCKETS_IN_SECONDS=(1800 60 120 600 300 30) #(30 60 120 300 600 1800)
BUCKET_PRICES_IN_CENTS=(32 3 4 12 7 2) #(2 3 4 7 12 32)
MAX_HIT_EXPIRATION_IN_MINUTES=10
DELAY_BETWEEN_POSTS_IN_MINUTES=1
ITERATIONS_PER_EXPERIMENT=27
EXPERIMENT_LENGTH_IN_MINUTES=60  # posting + waiting

# NOTE: EXPERIMENT_LENGTH_IN_MINUTES MUST be greater than:
#    (iterations*delay) + 1 minute expiration of last HITs + assignment duration


# END of experimental variables


#
# This function runs an experiment
#
# arguments:
#   $1 experiment number
#   $2 number of hits to post each iteration
#   $3 bucket size in seconds
#   $4 price in cents (e.g. 2, 3, 4, 7, 12)
#   $5 max hit expiration time in MINUTES (will back off at end)
#   $6 delay between posts in MINUTES
#   $7 total iterations (will back off at end so all hits expire at same time) 
#   $8 total experiment length in MINUTES
function experiment {
    echo "== STARTING $3 SECOND BUCKET =="
    echo "== ITERATIONS = $7 =="
    let waittime=$6*60    

    for (( i=1; i<=$7; i++ ))
    do
        let iteration_time_left=($7-i)*$waittime+60 # extra +60 is because we always give hits 60 seconds of life
        let expiration_time_in_seconds=$5*60
        if [ $iteration_time_left -le $expiration_time_in_seconds ] ; then
            expiration_time_in_seconds=$iteration_time_left
        fi
        echo "== ITERATION $i OF $7 -- $3 SECOND BUCKET =="
        python word_clicker_poster.py -e $1 -n $2 -b $3 -p $4 -x $expiration_time_in_seconds
        sleep $waittime
    done
    let time_spent_so_far=$6*60*$7
    let end_of_experiment_sleep=$8*60-time_spent_so_far
    sleep $end_of_experiment_sleep
}


#
# Run all the experiments
#

number_of_buckets=${#BUCKETS_IN_SECONDS[*]}
for (( b=0; b<$number_of_buckets; b++ ))
do
    experiment $EXPERIMENT_NUMBER \
        $HITS_PER_ITERATION \
        ${BUCKETS_IN_SECONDS[$b]} \
        ${BUCKET_PRICES_IN_CENTS[$b]} \
        $MAX_HIT_EXPIRATION_IN_MINUTES \
        $DELAY_BETWEEN_POSTS_IN_MINUTES \
        $ITERATIONS_PER_EXPERIMENT \
        $EXPERIMENT_LENGTH_IN_MINUTES
done