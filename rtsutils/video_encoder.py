from db_connection import DBConnection

import subprocess, shlex
from optparse import OptionParser
import os
import re
from datetime import datetime, timedelta
from timeutils import unixtime, total_seconds

def encodeVideo(head, name, extension):
    """Encodes the video into a FLV and returns the filename"""

    generateStills(head, name, extension)
    #generateMovie(head, name, extension)

def generateStills(head, name, extension):
    """Generates ~100 still JPEGs from the 3gp video"""
    # ffmpeg -r 25 -i filename.3gp -r {outputframerate} filename%3d.jpg
    
    output_frame_rate = int(100.0 / total_seconds(getVideoLength(generateFilename(head, name, extension)))) + 1

    cmd = "ffmpeg"
    cmd += " -r 25"
    cmd += " -i " + generateFilename(head, name, extension) # filename 
    cmd += " -y " # -y: force overwrite output files
    cmd += " -r " + str(output_frame_rate)
    cmd += " " + generateFilename(head, name, "%3d.jpg") # output file
    print("Stills command: %s" % cmd)
    
    args = shlex.split(cmd)
    process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.communicate()[1]
    print("Finished encoding")
     

def generateMovie(head, name, extension):
    """ Generates the FLV from the JPEGs. JPEGs must exist before calling this function or ffmpeg will make fun of you."""
    # ffmpeg -i filename.3gp -an -g 1 filename.flv                                                                                                                
    cmd = "ffmpeg"
    cmd += " -i " + generateFilename(head, name, extension) # filename                                                                                               cmd += " -an -g 1 -y " # an: no audio; -g 1: keyframe every frame; -y: force overwrite output files                                                              cmd += " " + generateFilename(head, name, ".flv") # output file                                                                                              
    args = shlex.split(cmd)
    process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.communicate()[1]
    print("Finished encoding")

    # get width and height from the output                                                                                                                        
    pattern = re.compile('Output.*Stream #0.*\ (?P<width>\d+)x(?P<height>\d+) \[')
    groups = re.search(pattern, output.replace('\n', ''))
    width = int(groups.group('width'))
    height = int(groups.group('height'))
    return (width, height)

    
def uploadVideo(name, width, height):
    db = DBConnection()
    try:
        sql = """INSERT INTO videos (filename, width, height, creationtime) VALUES (%s, %s, %s, %s)"""
        db.query_and_return_array(sql, (name, width, height, unixtime(datetime.now())))
    except Exception, e:
        print("Error writing video to database:")
        print(e)

def generateFilename(head, name, extension):
    return head+os.sep+name+extension
    
def getVideoLength(filename):
    """ Returns a timedelta specifying the length of the video """
    cmd = "ffmpeg"
    cmd += " -i " + filename

    # how long is this video?
    args = shlex.split(cmd)
    process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.communicate()[1]

    pattern = re.compile('Duration: (?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2}).(?P<millis>[0-9]{2}),')
    groups = re.search(pattern, output.replace('\n', ''))
    hours = int(groups.group('hours'))
    minutes = int(groups.group('minutes'))
    seconds = int(groups.group('seconds'))
    millis = int(groups.group('millis'))    
    
    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds = millis)
    return duration

def splitPath(full_filename):
    """ Returns (head, name, extension) for a fully-specified path """
    filename = full_filename
    (head, tail) = os.path.split(filename) # ('/foo/bar/baz/', 'quux.txt')
    (name, extension) = os.path.splitext(tail) # ('quux', 'txt')
    return (head, name, extension)
    

if __name__ == "__main__":
    parser = OptionParser() #no options now, the only thing is the 
    parser.add_option("-f", "--file", dest="filename",
                      help="3gp video input FILE", metavar="FILE")
    (options, args) = parser.parse_args()
    
    (head, name, extension) = splitPath(options.filename)
    (width, height) = encodeVideo(head, name, extension)
    uploadVideo(name, width, height)
