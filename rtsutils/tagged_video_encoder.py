import subprocess, shlex
from optparse import OptionParser
import os
import re

INPUT_DIRECTORY = "web/media/videos/jpg"
WORK_DIRECTORY = "web/media/videos/jpgtagged" 
OUTPUT_DIRECTORY = "web/media/videos/flvtagged"

RE_FILENAME_PARSER = re.compile("(\d+-VID_\d+_\d{6})(\d{3})\.jpg")

def main():
    files = os.listdir(INPUT_DIRECTORY)
    filtered_files = filter(lambda x: RE_FILENAME_PARSER.match(x), files)
    
    # make annotated jpeg

    file_groups = set()

    for f in filtered_files:
        print f
        m = RE_FILENAME_PARSER.match(f)
        g = m.groups()
        file_groups.add(g[0])
        n = g[1]
        cmd = "convert " + os.path.join(INPUT_DIRECTORY, f)
        cmd += " -fill white -undercolor '#00000080' -gravity South -pointsize 72 -font Nimbus-Sans-Bold -annotate +0+5 ' "
        cmd += n + " ' " + os.path.join(WORK_DIRECTORY, f)
        print cmd
        args = shlex.split(cmd)
        process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()[1]



    print str(len(file_groups)) + ": " + str(file_groups)

    for g in file_groups:
        print g

        cmd = "ffmpeg"
        cmd += " -r 10 " # input "framerate" is 10 -- needs to match the second -r
        cmd += " -i " + os.path.join(WORK_DIRECTORY, g) + "%3d.jpg" # filename
        cmd += " -an -g 1 -y " # an: no audio; -g 1: keyframe every frame; -y: force overwrite output files
        cmd += " -vframes 100 " # we want 100 frames in the video
        cmd += " -r 10 " # output framerate is 10 -- needs to match the first -r
        cmd += " " + os.path.join(OUTPUT_DIRECTORY, g) + ".flv" # output file
        
        print cmd
        args = shlex.split(cmd)
        process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()[1]



if __name__ == "__main__":
    main()
