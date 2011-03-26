#
# Mechanical Turk settings
#

aws_id="[your aws id]"
aws_secret="[your aws secret]"

SANDBOX = True

#
# Database settings
#

DB_USER = 'username'
DB_PASSWORD = 'password'
DB_HOST = 'localhost'
DB_DATABASE = 'dbname'

# Elevated user has all db priviledges -- DO NOT use for web code
DB_ELEVATED_USER = 'username-elev'
DB_ELEVATED_PASSWORD = 'password-elev'

#
# External HIT server info
#

HIT_SERVER = "flock.csail.mit.edu"
HIT_SERVER_USER_DIR = '[your username]'

#
# GeoIP settings
#
# Data file available from: http://www.maxmind.com/app/geolitecity
#

GEOIP_DATA_FILE_LOCATION = "/var/local/geoip/GeoLiteCity.dat"
