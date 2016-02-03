from __future__ import division, unicode_literals
import sys
from subprocess import Popen, PIPE, call
import logging
import codecs
import ner
import re
import atexit
from socket import error as SocketError
import errno

from text.protein_entity import ProteinEntity
from text.offset import Offsets, Offset
from classification.results import ResultsNER
from classification.ner.simpletagger import SimpleTaggerModel, create_entity
from config import config

stanford_coding = {"-LRB-": "<", "\/": "/", "&apos;": "'", "analogs": "analogues", "analog": "analogue",
                   "-RRB-": ">", ":&apos;s": "'s"}
# convert < to -LRB, etc
rep = dict((re.escape(v), k) for k, v in stanford_coding.iteritems())
pattern = re.compile("|".join(rep.keys()))


def replace_abbreviations(text):
    return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)


class StanfordNERModel(SimpleTaggerModel):
    RAM = config.stanford_ner_train_ram
    RAM_TEST = config.stanford_ner_test_ram
    STANFORD_BASE = config.stanford_ner_dir
    STANFORD_NER = "{}/stanford-ner.jar".format(STANFORD_BASE)
    NER_PROP = "{}/base.prop".format(STANFORD_BASE)
    logging.info(NER_PROP)
    PARAMS = ["java", RAM, "-Dfile.encoding=UTF-8", "-cp", STANFORD_NER,
              "edu.stanford.nlp.ie.crf.CRFClassifier", "-prop", NER_PROP,
              "-readerAndWriter", "edu.stanford.nlp.sequences.CoNLLDocumentReaderAndWriter"]
    logging.info(PARAMS)
    TEST_SENT = "Structure-activity relationships have been investigated for inhibition of DNA-dependent protein kinase (DNA-PK) and ATM kinase by a series of pyran-2-ones, pyran-4-ones, thiopyran-4-ones, and pyridin-4-ones."
    XML_PATTERN = re.compile(r'<([\w-]+?)>(.+?)</\1>')
    CLEAN_XML = re.compile(r'<[^>]*>')

    def __init__(self, path, etype, **kwargs):
        super(StanfordNERModel, self).__init__(path, etype, **kwargs)
        self.process = None
        self.tagger = None

    def write_prop(self):
        """
        Write Stanford-NER prop file based on base.prop
        :return:
        """
        lines = codecs.open(self.NER_PROP, "r", "utf-8").readlines()
        with codecs.open(self.NER_PROP, "w", "utf-8") as props:
            for l in lines:
                if l.startswith("trainFile"):
                    props.write("trainFile = {}.bilou\n".format(self.path))
                elif l.startswith("serializeTo"):
                    props.write("serializeTo = {}.ser.gz\n".format(self.path))
                elif l.startswith("entitySubclassification"):
                    props.write('entitySubclassification = SBIEO\n')
                elif l.startswith("retainEntitySubclassification"):
                    props.write("retainEntitySubclassification = false\n")
                else:
                    props.write(l)
        logging.info("wrote prop file")

    def train(self, entitytype):
        self.write_prop()
        self.save_corpus_to_sbilou(entitytype)
        logging.info("Training model with StanfordNER")
        process = Popen(self.PARAMS, stdout=PIPE, stderr=PIPE)
        # process.communicate()
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logging.info(output.strip())
        rc = process.poll()
        logging.info("model " + self.path +'.ser.gz trained')
        # Popen(["jar", "-uf", self.STANFORD_NER, "{}.ser.gz".format(self.path)]).communicate()
        logging.info("saved model file to {}".format(self.STANFORD_NER))

    def test(self, corpus, entitytype, port=9191):
        self.tagger = ner.SocketNER("localhost", port, output_format='inlineXML')
        tagged_sentences = []
        logging.info("sending sentences to tagger {}...".format(self.path))
        for isent, sid in enumerate(self.sids):
            #out = self.tagger.tag_text(replace_abbreviations(" ".join([t.text for t in self.tokens[isent]])))
            #out = self.tagger.tag_text(self.sentences[isent])
            text = self.sentences[isent]
            #logging.info("tagging: {}/{} - {}={}".format(isent, len(self.sids), sid, did))
            try:
                out = self.tagger.tag_text(text)
                #logging.debug("results:{}".format(out))
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise # Not error we are looking for
                print "socket error with sentence {}".format(text)
            except:
                print "other socket error!"
                out = self.tagger.tag_text(text)
                #print text, out
                #out = text
            tagged_sentences.append(out)
        results = self.process_results(tagged_sentences, corpus)
        return results

    def kill_process(self):
        self.process.kill()

    def process_results(self, sentences, corpus):
        results = ResultsNER(self.path)
        results.corpus = corpus
        for isent, sentence in enumerate(sentences):
            results = self.process_sentence(sentence, self.sids[isent], results)
        logging.info("found {} entities".format(len(results.entities)))
        return results

    def process_sentence(self, out, sid, results):
        # entities is a list of Offsets that correspond to part to entities (S, B, I, E)
        entities = self.get_offsets_for_tag(out, self.XML_PATTERN)
        sentence = results.corpus.documents['.'.join(sid.split('.')[:-1])].get_sentence(sid)
        if sentence is None:
            print sid
            print "not found!"
            print results.corpus.documents['.'.join(sid.split('.')[:-1])]
            print [s.sid for s in results.corpus.documents['.'.join(sid.split('.')[:-1])].sentences]
            sys.exit()
        sentence.tagged = out
        new_entity = None
        for e in entities:
            if not e.text or e.text.isspace():
                # we don't care if the token is nothing or just whitespace
                continue
            tokens = sentence.find_tokens_between(e.start, e.end, relativeto="sent")
            if not tokens:
                logging.debug("no tokens found between offset {}-{} on sentence {}".format(e.start, e.end, sentence.text))
                logging.debug("expected to find |{}|{}".format(e.text, e.tag))
                #logging.debug(sentence.tagged)
                #logging.debug([(t.start, t.end, t.text) for t in sentence.tokens])
                continue
            if e.tag.startswith("S"):
                single_entity = create_entity(tokens=tokens,
                                                      sid=sentence.sid, did=sentence.did,
                                                      text=e.text, score=1, etype=self.etype)
                eid = sentence.tag_entity(start=e.start, end=e.end, etype=self.etype,
                                            entity=single_entity, source=self.path)
                single_entity.eid = eid
                results.entities[eid] = single_entity # deepcopy
                #logging.info("new single entity: {}".format(single_entity))
            elif e.tag.startswith("B"):
                new_entity = create_entity(tokens=tokens,
                                                   sid=sentence.sid, did=sentence.did,
                                                   text=e.text, score=1, etype=self.etype)
            elif e.tag.startswith("I"):
                if not new_entity:
                    logging.info("starting with inside...")
                    new_entity = create_entity(tokens=tokens,
                                                   sid=sentence.sid, did=sentence.did,
                                                   text=e.text, score=1, etype=self.etype)
                else:
                    new_entity.tokens += tokens
            elif e.tag.startswith("E"):
                if not new_entity:
                    new_entity = create_entity(tokens=tokens,
                                               sid=sentence.sid, did=sentence.did,
                                               text=e.text,
                                               score=1, etype=self.etype)
                    logging.debug("started from a end: {0}".format(new_entity))
                else:
                    new_entity.tokens += tokens
                    new_entity.text= sentence.text[new_entity.tokens[0].start:new_entity.tokens[-1].end]
                    new_entity.end = new_entity.start + len(new_entity.text)
                    new_entity.dend = new_entity.dstart + len(new_entity.text)

                #logging.info("%s end: %s" % (new_entity.sid, str(new_entity)))
                #logging.debug("found the end: %s", ''.join([t.text for t in new_entity.tokens]))
                eid = sentence.tag_entity(start=new_entity.tokens[0].start,
                                          end=new_entity.tokens[-1].end, etype=self.etype,
                                          entity=new_entity, source=self.path)
                new_entity.eid = eid
                results.entities[eid] = new_entity # deepcopy
                new_entity = None
                #logging.debug("completed entity:{}".format(results.entities[eid]))
        return results

    def get_offsets_for_tag(self, data, tag):
        #data = "<ROOT>{}</ROOT>".format(data)
        #print data
        entities = []
        matches = tag.finditer(data)
        for match in matches:
            text = match.group(2)
            # logging.info("found {}-{} ({})".format(text, match.group(1), tag.pattern))
            start = len(self.CLEAN_XML.sub('', data[:match.start(2)]))
            end = start + len(text)
            entities.append(Offset(start, end, text=text, tag=match.group(1)))
        return entities

    def load_tagger(self, port=9191):
        """
        Start the server process with the classifier
        :return:
        """
        ner_args = ["java", self.RAM_TEST, "-Dfile.encoding=UTF-8", "-cp", self.STANFORD_NER, "edu.stanford.nlp.ie.NERServer",
                    "-port", str(port), "-loadClassifier", self.path + ".ser.gz", "-outputFormat", "inlineXML"]
        logging.info(' '.join(ner_args))
        logging.info("Starting the server for {}...".format(self.path))
        self.process = Popen(ner_args, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell=False)
        while True:
            out = self.process.stderr.readline()
            if out and out != "":
                logging.info(out)
            if "done" in out:
                logging.info("loaded {}".format(self.path))
                break
        #out = ner.communicate("Structure-activity relationships have been investigated for inhibition of DNA-dependent protein kinase (DNA-PK) and ATM kinase by a series of pyran-2-ones, pyran-4-ones, thiopyran-4-ones, and pyridin-4-ones.")
        #logging.info(out)
        #print 'Success!!'
        atexit.register(self.kill_process)
