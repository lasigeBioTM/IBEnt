import ast

import MySQLdb
import logging

from config import config
from text.corpus import Corpus
from text.document import Document
from text.sentence import Sentence


class IBENTDatabase(object):

    def __init__(self):
        self.db_conn = None
        self.connect_to_db()


    def connect_to_db(self):
        self.db_conn = MySQLdb.connect(host=config.doc_host,
                                       user=config.doc_user,
                                       passwd=config.doc_pw,
                                       db=config.doc_db,
                                       use_unicode=True)

    def add_corpus(self, corpus, **kwargs):
        # Insert corpus into the database
        # If the corpus file contains documents, those will be added to the database
        # otherwise it will just add an entry to the corpus table
        cur = self.db_conn.cursor()
        query = """INSERT INTO corpus(corpustag, version, description) VALUES (%s, %s, %s);"""
        # print "QUERY", query
        try:
            cur.execute(query, (corpus.tag, corpus.version, corpus.description))
            self.db_conn.commit()
            for did in corpus.documents:
                self.add_document(corpus.documents[did])
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            print "error adding corpus"
            logging.debug(e)

    def add_document(self, document):
        # Insert a document into the database
        cur = self.db_conn.cursor()
        query = """INSERT INTO document(doctag, corpustag, title, doctext) VALUES (%s, %s, %s, %s);"""
        # print "QUERY", query
        try:
            cur.execute(query, (document.did, document.corpus, document.title.encode("utf8"), document.text.encode("utf8")))
            self.db_conn.commit()
            # self.create_sentences(document., text)
            for s in document.sentences:
                self.add_sentence(s)
            logging.info("added document {}".format(document.did))
            #return str(inserted_id)
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            logging.debug(e)
            print "error adding document"

    def add_sentence(self, sentence):
        # corenlpres = sentence.process_sentence(self.corenlp)
        cur = self.db_conn.cursor()
        query = """INSERT INTO sentence(senttag, doctag, senttext, sentoffset, corenlp) VALUES (%s, %s, %s, %s, %s);"""
        try:
            cur.execute(query, (sentence.sid, sentence.did, sentence.text.encode("utf8"), sentence.offset,
                                sentence.corenlpres.encode("utf8")))
            self.db_conn.commit()
            # inserted_id = cur.lastrowid
            # return str(inserted_id)
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            logging.debug(e)

    def get_corpus(self, corpustag):
        corpus = Corpus()
        cur = self.db_conn.cursor()
        query = """SELECT distinct id, doctag
                               FROM document
                               WHERE corpustag =%s;"""
        cur.execute(query, (corpustag,))
        docs = cur.fetchall()
        for d in docs:
            document = self.get_document(d[1])
            corpus.documents[d[1]] = document
        return corpus

    def get_document(self, doctag):
        # return document entry with doctag
        cur = self.db_conn.cursor()
        query = """SELECT distinct id, doctag, title, doctext
                       FROM document
                       WHERE doctag =%s;"""
        # print "QUERY", query
        cur.execute(query, (doctag,))
        res = cur.fetchone()
        if res is not None:
            document = Document(res[3])
            # result = {'docID': res[1], 'title': res[2], 'docText': res[3], 'abstract':{'sentences':[]}}
            sentences = self.get_sentences(doctag)
            for s in sentences:
                sentence = Sentence(s[2], offset=s[3], sid=s[1], did=doctag)
                sentence.process_corenlp_output(ast.literal_eval(s[4]))
                sentence = self.get_entities(sentence)
                document.sentences.append(sentence)
            return document
        else:
            print 'error: could not find document {}'.format(doctag)

    def get_sentences(self, doctag):
        # Retrieve stored sentences associated with this doctag
        cur = self.db_conn.cursor()
        query = """SELECT distinct id, senttag, senttext, sentoffset, corenlp
                               FROM sentence
                               WHERE doctag =%s;"""
        # print "QUERY", query
        cur.execute(query, (doctag,))
        return cur.fetchall()

    def get_sentence(self):
        pass