import subprocess, shlex

FILENAME = "../../web/media/videos/charlie-short.mp4"
TIMESTAMPS = [
    1.58610999584198,
    1.647130012512207,
    10.425999641418457,
    4.0449538230896,
    4.586206912994385,
    4.6102800369262695,
    4.618113040924072,
    7.157309055328369,
    7.20182991027832,
    8.015119552612305
]
OUTPUT = "output/"

def exportPhotos(filename, timestamps):
    for timestamp in timestamps:
        cmd = "ffmpeg"
        cmd += " -i " + FILENAME # filename 
        cmd += " -ss " + str(timestamp) # timestamp to capture
        cmd += " -y -vframes 1 -f image2 -an -sameq"
        cmd += " " + OUTPUT + str(timestamp) + ".jpg" # output file

        args = shlex.split(cmd)
        p = subprocess.call(args) #could use Popen to parallelize, but messes up command line consequently
    print("Finished splitting")
        

if __name__=="__main__":
    exportPhotos(FILENAME, TIMESTAMPS)
