#!/bin/bash

TWENTYTWOMINUTES=1320

# 30 second bucket
echo "== STARTING 30 SECOND =="
for i in {1..38}
  do
    echo "== ITERATION $i OF 30 SECOND =="
    python word_clicker_poster.py -e 43 -n 10 -b 30 -p 2
    sleep 60
 done

echo "== DONE WITH 30 SECOND =="
sleep $TWENTYTWOMINUTES

# 60 second bucket
echo "== STARTING 60 SECOND =="
for i in {1..38}
  do
    echo "== ITERATION $i OF 60 SECOND =="
    python word_clicker_poster.py -e 43 -n 10 -b 60 -p 3
    sleep 60
 done

echo "== DONE WITH 60 SECOND =="
sleep $TWENTYTWOMINUTES

# 120 second bucket
echo "== STARTING 120 SECOND =="
for i in {1..38}
  do
    echo "== ITERATION $i OF 120 SECOND =="
    python word_clicker_poster.py -e 43 -n 10 -b 120 -p 4
    sleep 60
 done

echo "== DONE WITH 120 SECOND =="
sleep $TWENTYTWOMINUTES

# 300 second bucket
echo "== STARTING 300 SECOND =="
for i in {1..38}
  do
    echo "== ITERATION $i OF 300 SECOND =="
    python word_clicker_poster.py -e 43 -n 10 -b 300 -p 7
    sleep 60
 done

echo "== DONE WITH 300 SECOND =="
sleep $TWENTYTWOMINUTES

# 600 second bucket
echo "== STARTING 600 SECOND =="
for i in {1..38}
  do
    echo "== ITERATION $i OF 600 SECOND =="
    python word_clicker_poster.py -e 43 -n 10 -b 600 -p 12
    sleep 60
 done

echo "== DONE WITH 600 SECOND =="
