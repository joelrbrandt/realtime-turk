from MySQLdb import *
import MySQLdb.cursors

import settings

import logging

class DBConnection():
    def __init__(self):
        self._db = None
        self.check_connection()

    def check_connection(self):
        logging.debug('checking connection to db')
        result = False
        try:
            if self._db != None:
                try:
                     self._db.ping()
                     result = True
                except: 
                    logging.exception('pinging db failed with exception')
                    self._db = None

            if self._db == None:
                logging.debug("(re)connecting to the database")
                self._db = connect(host=settings.DB_HOST,
                                   user=settings.DB_USER,
                                   passwd=settings.DB_PASSWORD,
                                   db=settings.DB_DATABASE,
                                   cursorclass=MySQLdb.cursors.DictCursor,
                                   use_unicode=True)
                self._db.set_character_set('utf8')
                result = True
        except:
            logging.exception("exception connecting to the database")

        return result

    def query_and_return_cursor(self, query, parameters=tuple()):
        self.check_connection()
        cursor = self._db.cursor()
        cursor.execute(query, parameters)
        return cursor

    def query_and_return_array(self, query, parameters=tuple()):
        cursor = self.query_and_return_cursor(query, parameters)
        rs = cursor.fetchall()
        cursor.close()
        return rs