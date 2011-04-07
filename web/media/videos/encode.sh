#!/bin/bash
# This script encodes the 3GP file into the various HTML5 video formats

echo "Filename $1"
#echo "Width $2"
#echo "Height $3"
#echo "Aspect $4"

# WebM

# first pass
#ffmpeg -pass 1 -i $1.3gp -passlogfile $1 -threads 16 -keyint_min 0 -g 250 -skip_threshold 0 -qmin 1 -qmax 51 -vcodec libvpx -b 614400 -s $2x$3 -aspect $4 -f webm -an -y /dev/null
# second pass
#ffmpeg -pass 2 -passlogfile $1 -threads 16  -keyint_min 0 -g 250 -skip_threshold 0 -qmin 1 -qmax 51 -i $1.3gp -vcodec libvpx -b 614400 -s $2x$3 -aspect $4 -acodec libvorbis -y $1.webm

# Mp4
#HandBrakeCLI --preset "iPhone & iPod Touch" --two-pass --turbo -i $.3gp -o $.mp4

# Theora



# Flash -- note that we intentionally get rid of audio here with the -an flag; otherwise we need -ar 44100 or something like that
ffmpeg -i $1.3gp -an -g 1 $1.flv