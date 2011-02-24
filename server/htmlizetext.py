import nltk
import MySQLdb

def fixTexts():
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("""SELECT pk, text from texts""")
    for row in cur.fetchall():
        html = htmlizeText(row['text'])
        cur.execute("""UPDATE texts SET html = %s WHERE pk=%s""", (html, row['pk']) )
        
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
    
fixTexts()