import sys
import logging
import re
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '..'))
from classification.attributeclassifier import classify_time
from text.entity import Entity

stopwords = set(["previously", "currently"])
time_words = set()
#with open("TermList.txt") as termlist:
#    for l in termlist:
#        time_words.add(l.strip().lower())

class TimeEntity(Entity):
    def __init__(self, tokens, sid, **kwargs):
        # ChemicalEntity.__init__(self, kwargs)
        super(TimeEntity, self).__init__(tokens, **kwargs)
        self.sid = sid
        self.type = "time"
        self.subtype = kwargs.get("subtype")
        self.original_id = kwargs.get("original_id")

    def set_type(self):
        types = classify_time(self.text, self.before_context, self.after_context)
        # print "setting time type", types
        self.subtype = types[1]

    def set_attributes(self, context, sentence_entities):
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
        self.before_events = "".join([str(int("goldstandard_event" in t.tags)) for t in before_tokens5])
        self.set_type()

    def validate(self, ths, rules, *args, **kwargs):
        """
        Use rules to validate if the entity was correctly identified
        :param rules:
        :return: True if entity does not fall into any of the rules, False if it does
        """
        final_entities = [self]
        if "dividedates" in rules:
            if re.match(r"^\d{4}-\d{1,2}-\d{1,2}\s+\d{4}-\d{1,2}-\d{1,2}$", self.text):
                newtext1, newtext2 = self.text.split("  ")
                print newtext1, newtext2
                self.text = newtext1
                entity2 = TimeEntity(self.tokens)
                entity2.text = newtext2
                entity2.dend = self.dend
                self.dend = self.dstart + len(self.text)
                entity2.end = self.end
                self.end = self.start + len(self.text)
                entity2.start = entity2.end - len(entity2.text)
                entity2.dstart = entity2.dend - len(entity2.text)
                final_entities.append(entity2)

        if "stopwords" in rules:
            # todo: use regex
            words = self.text.split(" ")
            swords = [w.split("-") for w in words]
            words = []
            for w in swords:
                for sw in w:
                    words.append(sw)
            stop = False
            for s in stopwords:
                if any([s == w.lower() for w in words]):
                    logging.debug("ignored stopword %s" % self.text)
                    stop = True
            if stop:
                return False

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
            return False

        if "alpha" in rules:
            alpha = False
            for c in self.text.strip():
                if c.isalpha():
                    alpha = True
                    break
            if not alpha:
                logging.debug("ignored no alpha %s" % self.text)
                return False

        if "dash" in rules and (self.text.startswith("-") or self.text.endswith("-")):
            logging.debug("excluded for -: {}".format(self.text))
            return False
            # print final_entities
            return False

        return final_entities