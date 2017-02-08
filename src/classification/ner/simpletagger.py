import codecs
import logging
import unicodedata
import gc
from subprocess import Popen, PIPE
import sys
import os
import atexit
import time
import cPickle as pickle
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '../../..'))
from classification.model import Model
from text.chemical_entity import element_base, ChemicalEntity
from text.chemical_entity import amino_acids
from text.dna_entity import DNAEntity
from text.entity import Entity
from text.mirna_entity import MirnaEntity
from text.protein_entity import ProteinEntity
from text.time_entity import TimeEntity
from text.event_entity import EventEntity, umls_dic, ldpmap, call_ldpmap

feature_extractors = {# "text": lambda x, i: x.tokens[i].text,
                      "prefix3": lambda x, i: prefix(x, i, 3, 0),
                      "prevprefix3": lambda x, i: prefix(x, i, 3, -1),
                      "nextprefix3": lambda x, i: prefix(x, i, 3, 1),
                      "suffix3": lambda x, i: suffix(x, i, 3, 0),
                      "prevsuffix3": lambda x, i: suffix(x, i, 3, -1),
                      "nextsuffix3": lambda x, i: suffix(x, i, 3, 1),
                      "prefix2": lambda x, i: prefix(x, i, 2, 0),
                      "suffix2": lambda x, i: suffix(x, i, 2, 0),
                      "prefix4": lambda x, i: prefix(x, i, 4, 0),
                      "suffix4": lambda x, i: suffix(x, i, 4, 0),
                      "prefix2": lambda x, i: prefix(x, i, 2, -1),
                      "suffix2": lambda x, i: suffix(x, i, 2, -1),
                      "prefix4": lambda x, i: prefix(x, i, 4, -1),
                      "suffix4": lambda x, i: suffix(x, i, 4, -1),
                      "prefix2": lambda x, i: prefix(x, i, 2, 1),
                      "suffix2": lambda x, i: suffix(x, i, 2, 1),
                      "prefix4": lambda x, i: prefix(x, i, 4, 1),
                      "suffix4": lambda x, i: suffix(x, i, 4, 1),
                      "hasnumber": lambda x, i: "HASNUMBER=" + str(any(c.isdigit() for c in x.tokens[i].text)),
                      "case": lambda x, i: get_case(x, i, 0),
                      "prevcase": lambda x, i: get_case(x, i, -1),
                      "nextcase": lambda x, i: get_case(x, i, 1),
                      "lemma": lambda x, i: get_lemma(x, i, 0),
                      "prevlemma": lambda x, i: get_lemma(x, i, -1),
                      "nextlemma": lambda x, i: get_lemma(x, i, 1),
                      #"postag": lambda x, i: x.tokens[i].genia_pos,
                      "postag": lambda x, i: get_pos(x, i,0),
                      "prevpostag": lambda x, i: get_pos(x, i,-1),
                      "nextpostag": lambda x, i: get_pos(x, i, 1),
                      "wordclass": lambda x, i: wordclass(x.tokens[i].text),
                      "prevwordclass": lambda x, i: get_wordclass(x, i, -1),
                      "nextwordclass": lambda x, i: get_wordclass(x, i, 1),
                      "simplewordclass": lambda x, i: simplewordclass(x.tokens[i].text),
                      #"prevcase2": lambda x, i: get_case(x, i, -2),
                      #"nextcase2": lambda x, i: get_case(x, i, 2),
                      #"prevcase2": lambda x, i: get_case(x, i, -2),
                      #"nextcase2": lambda x, i: get_case(x, i, 2),

                      }

chem_features = feature_extractors.copy()
chem_features.update({ "greek": lambda x, i: str(has_greek_symbol(x.tokens[i].text)),
                        "aminoacid": lambda x, i: str(any(w in amino_acids for w in x.tokens[i].text.split('-'))),
                        "periodictable": lambda x, i: str(x.tokens[i].text in element_base.keys() or x.tokens[i].text.title() in zip(*element_base.values())[0])
                                     })

prot_features = feature_extractors.copy()
prot_features.update({"genia_tag": lambda x, i: genia_tag(x, i),
                      "genia_chunk": lambda x, i: genia_chunk(x, i)})

mirna_features = feature_extractors.copy()
mirna_features.update({"mir": lambda x, i: mirna(x, i),
                       # "prev_mir": lambda x, i: x.tokens[i-1].text.lower().startswith("mir"),
                       })

time_features = feature_extractors.copy()
time_features.update({"nertag": lambda x, i: timex_tag(x, i, 0),
                      "nertag-1": lambda x, i: timex_tag(x, i, -1),
                      "nertag1": lambda x, i: timex_tag(x, i, 1),
                      #"prevpostag2": lambda x, i: get_pos(x, i, -2),
                      #"nextpostag2": lambda x, i: get_pos(x, i, 2),
                      #"prevlemma2": lambda x, i: get_lemma(x, i, -2),
                      #"nextlemma2": lambda x, i: get_lemma(x, i, 2),
                      })

event_features = feature_extractors.copy()
event_features.update({"prevpostag2": lambda x, i: get_pos(x, i, -2),
                      "nextpostag2": lambda x, i: get_pos(x, i, 2),
                      "prevlemma2": lambda x, i: get_lemma(x, i, -2),
                      "nextlemma2": lambda x, i: get_lemma(x, i, 2),
                      "umlsname": lambda x, i: get_umls(x, i, 0),
                      "umlsname-1": lambda x, i: get_umls(x, i, -1),
                      "umlsname+1": lambda x, i: get_umls(x, i, 1),
                      #"umlsscore": lambda x, i: str(get_umls(x, i, 0)[1])
                      #"text": lambda x, i: get_text(x, i, 0),
                      #"text-1": lambda x, i: get_text(x, i, -1),
                      #"text1": lambda x, i: get_text(x, i, 1),
                      })




#print call_ldpmap("bleeding")


def get_umls(sentence, i, n=0):
    global umls_dic
    if i + n >= len(sentence.tokens):
        return "EOS"
    elif i + n < 0:
        return "BOS"
    elif sentence.tokens[i + n].text in umls_dic:
        match = umls_dic[sentence.tokens[i + n].text]
    else:
        match = call_ldpmap(sentence.tokens[i + n].text)
        umls_dic[sentence.tokens[i + n].text] = match
    if match[1] > 0.8:
        return "UMLS{}-{}".format(n, match[0])
    else:
        return "UMLS{}-NOMATCH".format(n)


def timex_tag(sentence, i, n=0):
    if i + n >= len(sentence.tokens):
        return "EOS"
    elif i + n < 0:
        return "BOS"
    elif sentence.tokens[i + n].tag in ("DATE", "TIME", "DURATION", "SET"):
        # print sentence.tokens[i + n].text, sentence.tokens[i + n].tag
        return "SNER{}={}".format(n, sentence.tokens[i + n].tag)
    else:
        return "SNER{}=0".format(n)


def genia_chunk(sentence, i):
    if hasattr(sentence[i], "genia_chunk"):
        print sentence[i].genia_chunk
        return "GENIA-" + sentence[i].genia_chunk
    else:
        return "NOGENIA"

def genia_tag(sentence, i):
    if hasattr(sentence[i], "genia_tag"):
        print sentence[i].genia_tag
        return "GENIA-" + sentence[i].genia_tag
    else:
        return "NOGENIA"

def mirna(sentence, i):
    # TODO: regex
    if sentence.tokens[i].text.lower().startswith("mir"):
        return "MIR_START"
    elif sentence.tokens[i].text.lower() == "-":
        return "MIR_DASH"
    else:
        return "NOMIR"

def word_in_dictionary(word, dictionary):
    # TODO:
    pass

#def prev_wordclass(sentence, i, n=1):
    #if i - n < 0:
        #return "BOS"
    #else:
        #return wordclass(sentence.tokens[i-n].text)

#def next_wordclass(sentence, i, n=1):
    #if i + n >= len(sentence.tokens):
        #return "EOS"
    #else:
        #return wordclass(sentence.tokens[i+n].text)

def get_wordclass(sentence, i, n):
    if i + n >= len(sentence.tokens):
        return "EOS"
    elif i + n < 0:
        return "BOS"
    else:
        return "WORDCLASS{}={}".format(n, wordclass(sentence.tokens[i+n].text))

def get_text(sentence, i, n=1):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        return u"TEXT{}={}".format(n, sentence.tokens[i+n].text)

def get_case(sentence, i, n=1):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        return "CASE{}={}".format(n, word_case(sentence.tokens[i+n].text))

def get_lemma(sentence, i, n=1):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        return u"LEMMA{}={}".format(n, sentence.tokens[i+n].lemma)

def get_pos(sentence, i, n=1):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        # return sentence.tokens[i+1].genia_pos
        return "POS{}={}".format(n, sentence.tokens[i + n].pos)

def word_case(word):
    if word.islower():
        case = 'LOWERCASE'
    elif word.isupper():
        case = 'UPPERCASE'
    elif word.istitle():
        case = 'TITLECASE'
    else:
        case = 'MIXEDCASE'
    return case


def has_greek_symbol(word):
    for c in word:
        #print c
        try:
            if 'GREEK' in unicodedata.name(c):
                hasgreek = 'HASGREEK'
                return True
        except ValueError:
            return False
    return False


def prefix(sentence, i , size, n):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        return u"PREFIX{}={}".format(n, sentence.tokens[i+n].text[:size])

def suffix(sentence, i , size, n):
    if i + n < 0:
        return "BOS"
    elif i + n >= len(sentence.tokens):
        return "EOS"
    else:
        return u"SUFFIX{}={}".format(n, sentence.tokens[i+n].text[-size:])


def wordclass(word):
    wclass = ''
    for c in word:
        if c.isdigit():
            wclass += '0'
        elif c.islower():
            wclass += 'a'
        elif c.isupper():
            wclass += 'A'
        else:
            wclass += 'x'
    return wclass


def simplewordclass(word):
    wclass = '.'
    for c in word:
        if c.isdigit() and wclass[-1] != '0':
            wclass += '0'
        elif c.islower() and wclass[-1] != 'a':
            wclass += 'a'
        elif c.isupper() and wclass[-1] != 'A':
            wclass += 'A'
        elif not c.isdigit() and not c.islower() and not c.isupper() and wclass[-1] != 'x':
            wclass += 'x'
    return "SIMPLEWORDCLASS=" + wclass[1:]


class SimpleTaggerModel(Model):
    """Model trained with a tagger"""
    def __init__(self, path, etype, **kwargs):
        """
        Generic NER classifier
        :param path: Location of the model file
        :param etype: type of entities classified
        """
        super(SimpleTaggerModel, self).__init__(path, **kwargs)
        self.sids = []
        self.tagger = None
        self.trainer = None
        #self.sentences = []
        self.etype = etype
        self.subtype = kwargs.get("subtype", "all")


    def load_data(self, corpus, flist, etype="all", mode="train", doctype="all", subtype="all"):
        #tr = tracker.SummaryTracker()
        """
            Load the data from the corpus to the format required by crfsuite.
            Generate the following variables:
                - self.data = list of features for each token for each sentence
                - self.labels = list of labels for each token for each sentence
                - self.sids = list of sentence IDs
                - self.tokens = list of tokens for each sentence
        """
        logging.info("Loading data for type %s" % etype)
        fname = "f" + str(len(flist))
        nsentences = 0
        didx = 0
        savecorpus = False # do not save the corpus if no new features are generated
        for di, did in enumerate(corpus.documents):
            logging.info("{} - {}/{}".format(did, di, len(corpus.documents)))
            if doctype != "all" and doctype not in did:
                continue
            # logging.debug("processing doc %s/%s" % (didx, len(corpus.documents)))
            for si, sentence in enumerate(corpus.documents[did].sentences):
                # logging.info("{}/{}".format(si, len(corpus.documents[did].sentences)))
                # skip if no entities in this sentence
                if sentence.sid in corpus.documents[did].invalid_sids:
                    logging.debug("Invalid sentence: {} - {}".format(sentence.sid, sentence.text))
                    continue
                if sentence.sid in corpus.documents[did].title_sids:
                    logging.debug("Title sentence: {} - {}".format(sentence.sid, sentence.text))
                    continue
                if mode == "train" and "goldstandard" not in sentence.entities.elist:
                    # logging.debug("Skipped sentence without entities: {}".format(sentence.sid))
                    continue
                sentencefeatures = []
                sentencelabels = []
                sentencetokens = []
                sentencesubtypes = []
                for i in range(len(sentence.tokens)):
                    if sentence.tokens[i].text:
                        #tokensubtype = sentence.tokens[i].tags.get("goldstandard_subtype", "none")
                        # if fname in sentence.tokens[i].features:
                        #     tokenfeatures = sentence.tokens[i].features[fname]
                            #logging.info("loaded features from corpus: %s" % tokenfeatures)
                        #     if etype == "all":
                        #         tokenlabel = sentence.tokens[i].tags.get("goldstandard", "other")
                        #     else:
                        #         tokenlabel = sentence.tokens[i].tags.get("goldstandard_" + type, "other")
                        # else:
                        tokenfeatures, tokenlabel = self.generate_features(sentence, i, flist, etype)
                        # savecorpus = True
                        sentence.tokens[i].features[fname] = tokenfeatures
                        # if tokenlabel != "other":
                        #      logging.debug("%s %s" % (tokenfeatures, tokenlabel))
                        sentencefeatures.append(tokenfeatures)
                        sentencelabels.append(tokenlabel)
                        sentencetokens.append(sentence.tokens[i])
                        del tokenfeatures
                            #sentencesubtypes.append(tokensubtype)
                        # print sentencesubtypes
                #logging.info("%s" % set(sentencesubtypes))
                #if subtype == "all" or subtype in sentencesubtypes:
                #logging.debug(sentencesubtypes)
                nsentences += 1
                self.data.append(tuple(sentencefeatures))
                self.labels.append(tuple(sentencelabels))
                del sentencefeatures
                del sentencelabels
                self.sids.append(sentence.sid)
                self.tokens.append(tuple(sentencetokens))
                #if mode != "train":

                    #self.subtypes.append(tuple(sentencesubtypes))
                    #self.sentences.append(sentence.text)
            if didx % 1000 == 0:
                gc.collect()
            #    tr.print_diff()

            didx += 1
        # save data back to corpus to improve performance
        #if subtype == "all" and savecorpus:
        #    corpus.save()
        logging.info("used %s sentences for model %s" % (nsentences, etype))
        #tr.print_diff()

    def copy_data(self, basemodel, t="all"):
        #logging.debug(self.subtypes)
        if t != "all":
            # right_sents = [i for i in range(len(basemodel.subtypes)) if t in basemodel.subtypes[i]]
            #logging.debug(right_sents)
            # print t, self.subtypes
            self.data = [basemodel.data[i] for i in range(len(basemodel.subtypes))]
            labels = [basemodel.labels[i] for i in range(len(basemodel.subtypes))]
            self.labels = []
            for il, l in enumerate(labels):
                self.labels.append([])
                for it, tl in enumerate(l):
                    # print it, tl, basemodel.subtypes[il][it]
                    if basemodel.subtypes[il][it] == t:
                        self.labels[-1].append(tl)
                    else:
                        self.labels[-1].append("other")
                # print self.labels[-1]
            self.sids = [basemodel.sids[i] for i in range(len(basemodel.subtypes))]
            self.tokens =  [basemodel.tokens[i] for i in range(len(basemodel.subtypes))]
            #self.sentences = [basemodel.sentences[i] for i in range(len(basemodel.subtypes))]
        else:
            self.data = basemodel.data[:]
            self.labels = basemodel.labels[:]
            self.sids = basemodel.sids
            self.tokens = basemodel.tokens[:]
            #self.sentences = basemodel.sentences[:]
        logging.info("copied %s for model %s" % (len(self.data), t))

    def generate_features(self, sentence, i, flist, subtype):
        """
            Features is dictionary mapping of featurename:value.
            Label is the correct label of the token. It is always other if
            the text is not annotated.
        """
        if subtype == "all":
            label = sentence.tokens[i].tags.get("goldstandard", "other")
        else:
            label = sentence.tokens[i].tags.get("goldstandard_" + subtype, "other")
        features = []
        for f in flist:
            #if f not in sentence.tokens[i].features:
            if subtype == "protein":
                fvalue = prot_features[f](sentence, i)
            elif subtype == "mirna":
                fvalue = mirna_features[f](sentence, i)
            else:
                fvalue = feature_extractors[f](sentence, i)
            # sentence.tokens[i].features[f] = fvalue
            #else: uncomment if it gets too slow
            #    fvalue = sentence.tokens[i].features[f]
            if fvalue != "BOS" and fvalue != "EOS":
                features.append(f + "=" + fvalue)
        # if label != "other":
        #     logging.debug("{} {}".format(sentence.tokens[i], label))
        #logging.debug(features)
        features = set(features)
        return features, label

    def save_corpus_to_sbilou(self):
        """
        Saves the data that was loaded into simple tagger format to a file compatible with Stanford NER
        :param entity_type:
        :return:
        """
        logging.info("saving loaded corpus to Stanford NER format...")
        lines = []
        for isent, sentence in enumerate(self.sids):
            for it, l in enumerate(self.labels[isent]):
                if l == "other":
                    label = "O"
                elif l == "start":
                    label = "B-{}".format(self.etype.upper())
                elif l == "end":
                    label = "E-{}".format(self.etype.upper())
                elif l == "middle":
                    label = "I-{}".format(self.etype.upper())
                elif l == "single":
                    label = "S-{}".format(self.etype.upper())
                #label += "_" + entity_type
                try:
                    lines.append("{0}\t{1}\n".format(self.tokens[isent][it].text, label))
                except UnicodeEncodeError: #fml
                    lines.append(u"{0}\t{1}\n".format(self.tokens[isent][it].text, label))
            lines.append("\n")
        with codecs.open("{}.bilou".format(self.path), "w", "utf-8") as output:
            output.write("".join(lines))
        logging.info("done")


def create_entity(tokens, sid, did, text, score, etype, **kwargs):
    """
    Create a new entity based on the type of model
    :param tokens: list of Tokens
    :param sid: ID of the sentence
    :param did: ID of the document
    :param text: string
    :param score:
    :param etype: Type of the entity
    :return: entity
    """
    e = None
    if etype == "chemical":
        e = ChemicalEntity(tokens, sid, text=text, score=score,
                           did=did, eid=kwargs.get("eid"), subtype=kwargs.get("subtype"))
    elif etype == "mirna":
        e = MirnaEntity(tokens, sid, text=text, did=did, score=score,
                        eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"))
    elif etype == "protein" or etype == "gene":
        e = ProteinEntity(tokens, sid, text=text, did=did,score=score,
                          eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"))
    elif etype == "dna":
        e = DNAEntity(tokens, sid, text=text, did=did,score=score,
                          eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"))
    elif etype == "event":
         e = EventEntity(tokens, sid, text=text, did=did,score=score,
                         eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"),
                         original_id=kwargs.get("original_id"))
    elif etype in ("timex3", "sectiontime", "doctime"):
         e = TimeEntity(tokens, sid, text=text, did=did,score=score,
                        eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"),
                        original_id=kwargs.get("original_id"))
    else:
        e = Entity(tokens, sid, text=text, did=did,score=score,
                        eid=kwargs.get("eid"), subtype=kwargs.get("subtype"), nextword=kwargs.get("nextword"),
                        original_id=kwargs.get("original_id"), sid=sid)
        e.type = etype
    return e


class BiasModel(SimpleTaggerModel):
    """Model which cheats by using the gold standard tags"""

    def test(self):
        # TODO: return results
        self.predicted = self.labels

