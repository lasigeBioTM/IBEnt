import logging
import re
import os
import sys
import atexit
import time
from text.entity import Entity
from config import config
from subprocess import Popen, PIPE
import cPickle as pickle
from EAtype import classify_type
from event_polarity import classify_polarity
from event_modality import classify_modality
from Script_EA_Degree import classify_degree
from event_dtr import classify_doctimerel


stopwords = set(["medication", "smear", "brain", "instructions", "tablets", "indication"])

umls_dic = {}  # text => (umls_match, umls_score)
if os.path.isfile("data/umls_dic.pickle"):
    logging.info("loading umls cache...")
    umls_dic = pickle.load(open("data/umls_dic.pickle", "rb"))
    loadedumlsdic = True
    logging.info("loaded umls dictionary with %s entries", str(len(umls_dic)))
else:
    umls_dic = {}
    loadedumlsdic = False
    logging.info("new umls dictionary")

ldpmap = None

def load_ldpmap():
    global ldpmap
    args = ["bin/LDPMap-master/bin/UMLSLDP", "../UMLS/2016AA/META/MRCONSO.RRF"]
    ldpmap = Popen(args, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell=False)
    while True:
        a = ldpmap.stdout.readline()
        if a == "Query Name:\n":
            print "loading...", a
            print "LDPmap loaded"
            break
        else:
            print "loading...", a

def kill_ldpmap():
    logging.info('Saving umls cache...!')
    pickle.dump(umls_dic, open("data/umls_dic.pickle", "wb"))
    if ldpmap is not None:
        ldpmap.kill()

atexit.register(kill_ldpmap)

def call_ldpmap(query):
    global ldpmap
    if ldpmap is None:
        load_ldpmap()
    start_time = time.time()
#    print ldpmap.stdout.readline()
    try:
        a = ldpmap.stdin.write(query + "\n")
    except UnicodeEncodeError:
        return "", ""
    while True:
        a = ldpmap.stdout.readline()
        if a == "Top Match Number:\n":
#            print a
#            print "query"
#            print
            break
#        else:
#            print a
    ldpmap.stdin.write("1\n")
    #print "b", b
    while True:
        a = ldpmap.stdout.readline()
        if a == "Query Name:\n":
            #print "a", a
            break
        elif a.startswith("C"):
            result = a
    result = result.strip().split(" ")
    umlsid = result[0].split("|")[0]
    score = float(result[-1])
    print query, result, time.time() - start_time, umlsid, score
    return umlsid, float(score)

class EventEntity(Entity):
    """Chemical entities"""
    def __init__(self, tokens, sid, **kwargs):
        # Entity.__init__(self, kwargs)
        super(EventEntity, self).__init__(tokens, **kwargs)
        self.sid = sid
        self.type = "event"
        self.subtype = kwargs.get("subtype")
        self.original_id = kwargs.get("original_id")
        self.degree = kwargs.get("degree")
        self.modality = kwargs.get("modality")
        self.polarity = kwargs.get("polarity")
        self.doctimerel = kwargs.get("doctimerel")

    def set_type(self):
        types = classify_type(re.escape(self.text), self.before_context, self.after_context)
        #print "setting time type", types
        self.subtype = types[1]

    def set_modality(self):
        types = classify_modality(re.escape(self.text), self.before_context, self.after_context, self.before_events)
        #print "setting time type", types
        self.modality = types

    def set_polarity(self):
        types = classify_polarity(re.escape(self.text), self.before_context, self.after_context, self.before_events)
        #print "setting time type", types
        self.polarity = types

    def set_degree(self):
        types = classify_degree(re.escape(self.text), self.before_context, self.after_context)
        self.degree = types

    def set_doctimerel(self):
        types = classify_doctimerel(re.escape(self.text), self.before_context, self.after_context,
                             self.before_pos5, self.after_pos5, self.word_pos)
        self.dtr = types

    def set_attributes(self, context, entity_tokens=None):
        break_words = ["but", "with"]
        # generate context windows

        firsttoken = self.tokens[0].order
        lasttoken = self.tokens[-1].order

        lw = 5
        before_tokens5 = []
        before_count = 0
        for i in range(firsttoken-1, -1, -1):
            if context[i].text in break_words:
                break
            before_count += 1
            #else:
            #    print "ignored", sentence.tokens[i].text
            before_tokens5 = [context[i]] + before_tokens5
            if before_count == lw:
                #if len(before_tokens5) > lw:
                #    print len(before_tokens5)
                break
        rw = 5
        after_tokens5 = []
        after_count = 0
        for i in range(lasttoken+1,len(context)):
            if context[i].text in break_words:
                break
            #if len(sentence.tokens[i].tags):
            #    print sentence.tokens[i].tags
            #if len(sentence.tokens[i].text) > 2 and "goldstandard_event" not in sentence.tokens[i].tags.keys():
            after_count += 1
            #else:
            #    print "ignored", sentence.tokens[i].text
            after_tokens5 =  after_tokens5 + [context[i]]
            if after_count == rw:
                #if len(after_tokens5) > rw:
                #    print len(after_tokens5)
                break
        self.before_context = "+" + "+".join([re.escape(t.text) for t in before_tokens5]) + "+"
        self.after_context = "+" + "+".join([re.escape(t.text) for t in after_tokens5]) + "+"
        self.before_pos5 = "+" + "+".join([t.pos for t in before_tokens5]) + "+"
        self.after_pos5 = "+" + "+".join([t.pos for t in after_tokens5]) + "+"
        self.word_pos = "+" + "+".join([t.pos for t in self.tokens]) + "+"
        self.sentence_time = "+".join([t.text for t in context if "goldstandard_timex3" in t.tags])
        if entity_tokens:
            self.before_events = "".join([str(int(t.order in entity_tokens)) for t in before_tokens5])
            #if self.did == "doc0055_RAD" and self.text == "exam":
            #    print entity_tokens
            #    print self.before_events
        else:
            self.before_events = "".join([str(int("goldstandard_event" in t.tags)) for t in before_tokens5])
        #self.before_events = "".join([str(int("goldstandard_event" in t.tags)) for t in before_tokens5])
        #self.before_events = "".join([str(int(any([x.endswith("event") for x in t.tags]))) for t in before_tokens5])
        #s
        self.set_type()
        self.set_modality()
        self.set_polarity()
        self.set_degree()
        self.set_doctimerel()

    def normalize(self):
        global umls_dic

        if self.text in umls_dic:
            match = umls_dic[self.text]
        else:
            match = call_ldpmap(self.text)
            umls_dic[self.text] = match
        # print match
        if match[1] > 0.8:
            # return "UMLS{}-{}".format(n, match[0])
            self.normalized = match[0]
            self.normalized_score = float(match[1])
            self.normalized_ref = "UMLS"
        else:
            self.normalized = self.text
            self.normalized_score = 0
            self.normalized_ref = "text"


    def get_dic(self):
        dic = super(EventEntity, self).get_dic()
        dic["subtype"] = self.subtype
        return dic

    def validate(self, ths, rules, *args, **kwargs):
        """
        Use rules to validate if the entity was correctly identified
        :param rules:
        :return: True if entity does not fall into any of the rules, False if it does
        """
        if "stopwords" in rules:
            # todo: use regex
            words = self.text.split(" ")
            stop = False
            for s in stopwords:
                if any([s == w.lower() for w in words]):
                    logging.debug("ignored stopword %s" % self.text)
                    stop = True
            if stop:
                return []

        if "paren" in rules:
            if (self.text[-1] == ")" and "(" not in self.text) or (self.text[-1] == "]" and "[" not in self.text) or \
                    (self.text[-1] == "}" and "{" not in self.text):
                logging.debug("parenthesis %s" % self.text)
                self.dend -= 1
                self.end -= 1
                self.text = self.text[:-1]
            if (self.text[0] == "(" and ")" not in self.text) or (self.text[0] == "[" and "]" not in self.text) or \
                    (self.text[0] == "{" and "}" not in self.text):
                logging.debug("parenthesis %s" % self.text)
                self.dstart += 1
                self.start += 1
                self.text = self.text[1:]

        if "hyphen" in rules and "-" in self.text and all([len(t) > 3 for t in self.text.split("-")]):
            logging.debug("ignored hyphen %s" % self.text)
            return []

        #if all filters are 0, do not even check
        if "ssm" in ths and ths["ssm"] != 0 and self.ssm_score < ths["ssm"] and self.text.lower() not in chem_words:
            #logging.debug("filtered %s => %s" % (self.text,  str(self.ssm_score)))
            return []

        if "alpha" in rules:
            alpha = False
            for c in self.text.strip():
                if c.isalpha():
                    alpha = True
                    break
            if not alpha:
                logging.debug("ignored no alpha %s" % self.text)
                return []

        if "dash" in rules and (self.text.startswith("-") or self.text.endswith("-")):
            logging.debug("excluded for -: {}".format(self.text))
            return False
        return [self]
