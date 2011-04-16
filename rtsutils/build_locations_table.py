from db_connection import *
import pygeoip

import settings

"""
NOTE: Every time this code runs, it _completely rebuilds_ the locations table

This code expects the following table to exist in the DB:

CREATE TABLE `locations` (
 `pk` int(10) unsigned NOT NULL AUTO_INCREMENT,
 `assignmentid` varchar(128) NOT NULL,
 `ip` varchar(128) DEFAULT NULL,
 `useragent` varchar(200) DEFAULT NULL,
 `city` varchar(128) DEFAULT NULL,
 `region_name` varchar(128) DEFAULT NULL,
 `country_code` varchar(5) DEFAULT NULL,
 `country_name` varchar(128) DEFAULT NULL,
 `latitude` double DEFAULT NULL,
 `longitude` double DEFAULT NULL,
 PRIMARY KEY (`pk`),
 UNIQUE KEY `assignmentid` (`assignmentid`),
 KEY `country_code` (`country_code`,`region_name`,`city`)
) ENGINE=MyISAM AUTO_INCREMENT=2143 DEFAULT CHARSET=utf8

"""


SQL_INTIALIZE_TABLE = """
TRUNCATE TABLE `locations`;

INSERT INTO `locations` (`assignmentid`, `ip`, `useragent`) 
  SELECT a.`assignmentid`, MAX(l.`ip`) `ip`, MAX(l.`useragent`) `useragent`
  FROM `assignments` as a, `logging` as l
  WHERE a.`assignmentid`=l.`assignmentid` AND l.`event`='accept'
  GROUP BY a.`assignmentid`
"""


def create_keys_if_not_exists(d, keys):
    for k in keys:
        if not d.has_key(k):
            d[k] = None



gi = pygeoip.GeoIP(settings.GEOIP_DATA_FILE_LOCATION)
db = DBConnection(elev=True)

db.query_and_return_cursor(SQL_INTIALIZE_TABLE)

rows = db.query_and_return_array("SELECT `pk`, `ip` FROM `locations`")

for r in rows:
    try:
        l = gi.record_by_addr(r['ip'])
        if l:
            create_keys_if_not_exists(l, ('city', 'region_name', 'country_code', 'country_name', 'latitude', 'longitude'))
            data = (l['city'], l['region_name'], l['country_code'], l['country_name'], l['latitude'], l['longitude'], r['pk'])
            db.query_and_return_array("UPDATE `locations` SET `city`=%s,`region_name`=%s, `country_code`=%s, `country_name`=%s, `latitude`=%s, `longitude`=%s WHERE `pk`=%s", data)
            print "%s %s: %s" % (str(r['pk']), str(r['ip']), str(data))
        else:
            print "%s %s: NO LOCATION FOUND" % (str(r['pk']), str(r['ip']))
    
    except Exception, e:
        print "%s %s: EXCEPTION:\n%s" % (str(r['pk']), str(r['ip']), str(e))
