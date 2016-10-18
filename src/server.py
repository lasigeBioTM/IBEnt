import argparse
import time
import ast
from classification.ner.crfsuitener import CrfSuiteModel
from classification.ner.stanfordner import StanfordNERModel
from text.sentence import Sentence

__author__ = 'Andre'
import bottle
from pycorenlp import StanfordCoreNLP
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging
import codecs
import cPickle as pickle
import random
import string
import MySQLdb
import json

from text.document import Document
from text.corpus import Corpus
from classification.ner.taggercollection import TaggerCollection
from classification.ner.simpletagger import SimpleTaggerModel, feature_extractors
from postprocessing.ensemble_ner import EnsembleNER
from reader import pubmed
from text.pair import Pair
from config import config
from postprocessing.chebi_resolution import add_chebi_mappings
from postprocessing.ssm import add_ssm_score



class IBENT(object):

    def __init__(self, entities, relations):
        self.baseport = 9181
        self.corenlp = None
        #self.basemodel = basemodel
        #self.ensemble_model = ensemble_model
        #self.subtypes = submodels
        #self.models = TaggerCollection(basepath=self.basemodel)
        #self.models.load_models()
        #self.ensemble = EnsembleNER(self.ensemble_model, None, self.basemodel + "_combined", types=self.subtypes,
        #                           features=[])
        #self.ensemble.load()
        self.db_conn = None
        self.entity_annotators = {}
        for e in entities:
            self.entity_annotators[e] = None # one classifier for each type of entity

        self.relation_annotators = {}
        for r in relations:
            self.relation_annotators[r] = {}
        self.setup()

    def setup(self):
        # Connect to DB
        self.db_conn = MySQLdb.connect(host=config.doc_host,
                                 user=config.doc_user,
                                 passwd=config.doc_pw,
                                 db=config.doc_db)
        # Connect to CoreNLP
        self.corenlp = StanfordCoreNLP('http://localhost:9000')

        #Load StanfordNER models stored in a specific directory
        self.load_models()

    def hello(self):
        return "OK!"

    def load_models(self):
        # Run load_tagger method of all models
        for i, a in enumerate(self.entity_annotators.keys()):
            self.create_annotationset(a[0])
            if a[1] == "stanfordner":
                model = StanfordNERModel("annotators/{}/{}".format(a[2], a[0]), a[2])
                model.load_tagger(self.baseport + i)
                self.entity_annotators[a] = model
            elif a[1] == "crfsuite":
                model = CrfSuiteModel("annotators/{}/{}".format(a[2], a[0]), a[2])
                model.load_tagger(self.baseport + i)
                self.entity_annotators[a] = model

    def create_annotationset(self, name):
        # Create DB entries for each annotations set
        cur = self.db_conn.cursor()
        query = """INSERT INTO annotationset(name) VALUES (%s);"""
        try:
            cur.execute(query, (name,))
            self.db_conn.commit()
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            logging.debug(e)

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
            return json.dumps({'docID': res[1], 'docTitle': res[2], 'docText': res[3]})
        else:
            return json.dumps({'error': 'could not find document {}'.format(doctag)})

    def new_document(self, doctag):
        # Insert a new document into the database
        data = bottle.request.json
        text = data["text"]
        title = data.get("title")
        format = data["format"]
        cur = self.db_conn.cursor()
        query = """INSERT INTO document(doctag, title, doctext) VALUES (%s, %s, %s);"""
        # print "QUERY", query
        try:
            cur.execute(query, (doctag, title, text))
            self.db_conn.commit()
            inserted_id = cur.lastrowid
            self.create_sentences(doctag, text)
            return json.dumps({"message": "added document {}".format(doctag)})
            #return str(inserted_id)
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            logging.debug(e)
            return json.dumps({"error": "error adding document"})

    def create_sentences(self, doctag, text):
        # Create sentence entries based on text from document doctag
        cur = self.db_conn.cursor()
        newdoc = Document(text, process=False,
                                  did=doctag)
        newdoc.sentence_tokenize("biomedical")
        for i, sentence in enumerate(newdoc.sentences):
            corenlpres = sentence.process_sentence(self.corenlp)
            query = """INSERT INTO sentence(senttag, doctag, senttext, sentoffset, corenlp) VALUES (%s, %s, %s, %s, %s);"""
            try:
                cur.execute(query, (sentence.sid, doctag, sentence.text, sentence.offset, str(corenlpres)))
                self.db_conn.commit()
                #inserted_id = cur.lastrowid
                #return str(inserted_id)
            except MySQLdb.MySQLError as e:
                self.db_conn.rollback()
                logging.debug(e)
                #return "error adding new sentence"

    def run_annotator(self, doctag, annotator):
        """
        Classify a document using an annotator and insert results into the database
        :param doctag: tag of the document
        :param annotator: annotator to classify
        :return:
        """
        sentences = self.get_sentences(doctag)
        data = bottle.request.json
        output = {}
        for a in self.entity_annotators:  # a in (annotator_name, annotator_engine, annotator_etype)
            if a[0] == annotator:
                for s in sentences:
                    sentence = Sentence(s[2], offset=s[3], sid=s[1], did=doctag)
                    #sentence.process_sentence(self.corenlp)
                    sentence.process_corenlp_output(ast.literal_eval(s[4]))
                    sentence_text = " ".join([t.text for t in sentence.tokens])
                    sentence_output = self.entity_annotators[a].annotate_sentence(sentence_text)
                    #print sentence_output

                    sentence_entities = self.entity_annotators[a].process_sentence(sentence_output, sentence)
                    for e in sentence_entities:
                        self.add_entity(sentence_entities[e], annotator)
                        output[e] = str(sentence_entities[e])
                        # print output
        return json.dumps(output)


    def add_entity(self, entity, annotator):
        #add offetset to database
        #retrieve offset ID
        #retrieve annotationset ID
        #add entity to database
        cur = self.db_conn.cursor()
        #query = """addoffset(%s, %s, %s, %s, %s, %s, %s);"""
        query = """SELECT annotationset.id FROM annotationset WHERE annotationset.name = %s"""
        cur.execute(query, (annotator,))
        annotatorid = cur.fetchone()[0]
        try:
            cur.callproc("addoffset", (entity.dstart, entity.dend, entity.start, entity.end, entity.did, entity.sid, entity.text, 0))
            cur.execute('SELECT @_addoffset_7;')
            offsetid = cur.fetchone()[0]
            # return str(inserted_id)
            query = """INSERT INTO entity(offsetid, annotationset, etype) VALUES (%s, %s, %s);"""
            cur.execute(query, (offsetid, annotatorid, entity.subtype))
            self.db_conn.commit()
        except MySQLdb.MySQLError as e:
            self.db_conn.rollback()
            logging.debug(e)

    def get_sentences(self, doctag):
        cur = self.db_conn.cursor()
        query = """SELECT distinct id, senttag, senttext, sentoffset, corenlp
                               FROM sentence
                               WHERE doctag =%s;"""
        # print "QUERY", query
        cur.execute(query, (doctag,))
        return cur.fetchall()

    def get_annotations(self, doctag, annotator):
        cur = self.db_conn.cursor()
        query = """SELECT o.offsettext, o.docstart, o.docend, e.etype
                   FROM entity e, offset o, annotationset a
                   WHERE doctag = %s AND e.offsetid = o.id AND e.annotationset = a.id AND a.name = %s;"""
        # print "QUERY", query
        cur.execute(query, (doctag, annotator))
        annotations = cur.fetchall()
        output = {"entities": []}
        for a in annotations:
            output["entities"].append({"text": a[0], "start": a[1], "end": a[2], "etype": a[3]})
        return output


    def process_pubmed(self, pmid):
        title, text = pubmed.get_pubmed_abs(pmid)

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def process_multiple(self):
        bottle.response.content_type = "application/json"
        data = bottle.request.json
        text = data["text"]
        format = data["format"]
        test_corpus = self.generate_corpus(text)
        multiple_results = self.models.test_types(test_corpus)
        final_results = multiple_results.combine_results()
        final_results = add_chebi_mappings(final_results, self.basemodel)
        final_results = add_ssm_score(final_results, self.basemodel)
        final_results.combine_results(self.basemodel, self.basemodel + "_combined")

        # self.ensemble.generate_data(final_results, supervisioned=False)
        #self.ensemble.test()
        # ensemble_results = ResultsNER(self.basemodel + "_combined_ensemble")
        # ensemble_results.get_ensemble_results(self.ensemble, final_results.corpus, self.basemodel + "_combined")
        #output = get_output(final_results, basemodel + "_combined")
        results_id = self.id_generator()
        #output = self.get_output(ensemble_results, self.basemodel + "_combined_ensemble", format, id=results_id)
        output = self.get_output(final_results, self.basemodel + "_combined", format=format, results_id=results_id)
        #self.models.load_models()
        self.clean_up()
        # save corpus to pickel and add ID to the output as corpusfile
        pickle.dump(final_results.corpus, open("temp/{}.pickle".format(results_id), 'w'))
        return output

    def clean_up(self):

        for m in self.models.models:
            self.models.models[m].reset()
        self.models.basemodel.reset()

    def process(self, text="", modeltype="all"):
        test_corpus = self.generate_corpus(text)
        model = SimpleTaggerModel("models/chemdner_train_f13_lbfgs_" + modeltype)
        model.load_tagger()
        # load data into the model format
        model.load_data(test_corpus, feature_extractors.keys())
        # run the classifier on the data
        results = model.test(stats=False)
        #results = ResultsNER("models/chemdner_train_f13_lbfgs_" + modeltype)
        # process the results
        #results.get_ner_results(test_corpus, model)
        output = self.get_output(results, "models/chemdner_train_f13_lbfgs_" + modeltype)
        return output

    def get_relations(self):
        """
        Process the results dictionary, identify relations
        :return: results dictionary with relations
        """
        data = bottle.request.json
        # logging.debug(str(data))
        if "corpusfile" in data:
            corpus = pickle.load(open("temp/{}.pickle".format(data["corpusfile"])))
            logging.info("loaded corpus {}".format(data["corpusfile"]))
        else:
            # create corpus
            corpus = None
            pass
        did = "d0"
        #for sentence in data["abstract"]["sentences"]:
        for sentence in corpus.documents["d0"].sentences[1:]:
            sentence_pairs = []
            sentence_entities = sentence.entities.elist[self.basemodel + "_combined"]
            # logging.info("sentence entities:" + str(sentence_entities))
            sid = sentence.sid
            for i1, e1 in enumerate(sentence_entities):
                logging.info("sentence entities:" + str(e1))
                if i1 < len(sentence_entities)-1:
                    for i2, e2 in enumerate(sentence_entities[i1+1:]):
                        logging.info("sentence entities:" + str(e2))
                        pid = sentence.sid + ".p{}".format(len(sentence_pairs))
                        newpair = Pair(entities=[e1, e2], sid=sid, pid=pid, did=did)
                        sentence_pairs.append(newpair)
                        sentence.pairs.pairs[pid] = newpair
            logging.info(str(sentence_pairs))
            if len(sentence_pairs) > 0:
                corpus.documents[did].get_sentence(sid).test_relations(sentence_pairs, self.basemodel + "_combined")


        return data

    def get_output(self, results, model_name, format="bioc", results_id=None):
        if format == "bioc":
            a = ET.Element('collection')
            bioc = results.corpus.documents["d0"].write_bioc_results(a, model_name)
            rough_string = ET.tostring(a, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            output = reparsed.toprettyxml(indent="\t")
        elif format == "chemdner":
             with codecs.open("/dev/null", 'w', 'utf-8') as outfile:
                lines = results.corpus.write_chemdner_results(model_name, outfile)
                output = ""
                for l in lines:
                    output += ' '.join(l) + " "
        else: # default should be json
            results_dic = results.corpus.documents["d0"].get_dic(model_name)
            results_dic["corpusfile"] = results_id
            output = json.dumps(results_dic)
        return output


def main():
    starttime = time.time()
    #parser = argparse.ArgumentParser(description='')
    #parser.add_argument("action", choices=["start", "stop"])
    #parser.add_argument("--basemodel", dest="model", help="base model path")
    #parser.add_argument("-t", "--test", action="store_true",
    #                help="run a test instead of the server")
    #parser.add_argument("--log", action="store", dest="loglevel", default="WARNING", help="Log level")
    #options = parser.parse_args()
    numeric_level = getattr(logging, "DEBUG", None)
    #if not isinstance(numeric_level, int):
    #    raise ValueError('Invalid log level: %s' % options.loglevel)

    #while len(logging.root.handlers) > 0:
    #    logging.root.removeHandler(logging.root.handlers[-1])
    logging_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)s:%(funcName)s %(message)s'
    logging.basicConfig(level=numeric_level, format=logging_format)
    logging.getLogger().setLevel(numeric_level)

    logging.debug("Initializing the server...")
    server = IBENT(entities=[("mirtex_train_mirna_sner", "stanfordner", "mirna"),
                             ("chemdner_train_all", "stanfordner", "chemical")], relations=[])
    logging.debug("done.")
    # Test server
    bottle.route("/ibent/status")(server.hello)

    # Fetch an existing document
    bottle.route("/ibent/<doctag>")(server.get_document)

    # Create a new document
    bottle.route("/ibent/<doctag>", method='POST')(server.new_document)

    # Get new miRNA entity annotations i.e. run a classifier again
    bottle.route("/ibent/entities/<doctag>/<annotator>", method='POST')(server.run_annotator)

    # Get miRNA entity annotations i.e. fetch from the database
    bottle.route("/ibent/entities/<doctag>/<annotator>")(server.get_annotations)

    #bottle.route("/iice/chemical/<text>/<modeltype>", method='POST')(server.process)
    #bottle.route("/ibent/interactions", method='POST')(server.get_relations)
    #daemon_run(host='10.10.4.63', port=8080, logfile="server.log", pidfile="server.pid")
    bottle.run(host=config.host_ip, port=8080, DEBUG=True)
if __name__ == "__main__":
    main()