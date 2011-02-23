#!/usr/bin/env python
import cgitb, cgi
import MySQLdb
import os
import json
import nltk
cgitb.enable()    

def getText():
    print "Content-Type: application/json"     # HTML is following
    print                               # blank line, end of headers
    
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    form = cgi.FieldStorage()
    id = int(form['textid'].value)
    #print id
        
    cur.execute("""SELECT text FROM texts WHERE pk = %s""", (id,))
    
    text = cur.fetchone()
    paragraph = htmlizeText(text['text'])
    
    result = dict()
    result['pk'] = id
    result['text'] = paragraph
    
    print(json.dumps(result))
        
    cur.close()
    db.close()

def htmlizeText(text):
    #print text.encode('ascii', 'replace')
    tokenized = nltk.tokenize.word_tokenize(text)
    
    spanned = []
    for index, token in enumerate(tokenized):
    #    print token.encode('ascii', 'replace') + " " + str(type(token))
        span = u"<span id='word" + unicode(index) +  u"' class='word'>" + token + u"</span>"
        spanned.append(span)
    
    paragraph = u"<p>" + u" ".join(spanned) + u"</p>"
    #print paragraph.encode('ascii', 'replace')
    return paragraph
    
getText()