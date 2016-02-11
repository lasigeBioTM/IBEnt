from __future__ import unicode_literals
import logging
import sys
from xml.etree import ElementTree as ET
import re
from text.protein_entity import ProteinEntity

from token2 import Token2
from entity import Entities
from classification.ner.simpletagger import create_entity
from classification.rext.relations import Pairs
from classification.rext import ddi_kernels
from classification.rext import relations
from text.chemical_entity import ChemicalEntity
from text.mirna_entity import MirnaEntity
from text.event_entity import EventEntity
from text.time_entity import TimeEntity
from text.tlink import TLink


class Sentence(object):
    """Sentence from a document, to be annotated"""
    def __init__(self, text, offset=0, **kwargs):
        self.text = text
        self.sid = kwargs.get("sid")
        self.did = kwargs.get("did")
        self.entities = Entities(sid=self.sid, did=self.did)
        self.offset = offset
        self.pairs = Pairs()
        self.parsetree = None
        self.tokens = []

    def process_corenlp_sentence(self, corenlpres):
        """
        Process the results obtained with CoreNLP for this sentence
        :param corenlpres:
        :return:
        """
        # self.sentences = []
        if len(corenlpres['sentences']) > 1:
            sys.exit("Number of sentences from CoreNLP is not 1.")
        if len(corenlpres['sentences']) == 0:
            self.tokens = []
            self.create_newtoken("", {})
            logging.debug("no sentences")
            logging.debug(self.text)
            return
        sentence = corenlpres['sentences'][0]
        # print sentence
        self.parsetree = sentence['parsetree']
        for t in sentence['words']:
            # print t[0]
            if t[0]:
                # TODO: specific rules for each corpus
                token_seq = re.split(r'(\w+)(-|/|\\|\+|\.)(\w+)', t[0])
                #token_seq = rext.split(r'(\w+)(/|\\|\+|\.)(\w+)', t[0])

                if len(token_seq) > 1: # and all([len(elem) > 1 for elem in token_seq]):
                    #logging.info("{}: {}".format(t[0], "&".join(token_seq)))
                    for its, ts in enumerate(token_seq):
                        if ts.strip() != "":
                            charoffset_begin = int(t[1]["CharacterOffsetBegin"])
                            if token_seq[:its]: # not the first token
                                charoffset_begin += sum([len(x) for x in token_seq[:its]])
                            # charoffset_begin += its
                            charoffset_end = len(ts) + charoffset_begin
                            #logging.info(str(charoffset_begin) + ":" + str(charoffset_end))
                            ts_props = {"CharacterOffsetBegin": charoffset_begin,
                                        "CharacterOffsetEnd": charoffset_end,
                                        "PartOfSpeech": t[1]["PartOfSpeech"],
                                        "NamedEntityTag": t[1]["NamedEntityTag"],
                                        "Lemma": t[1]["Lemma"]}
                            self.create_newtoken(ts, ts_props)

                else:
                    self.create_newtoken(t[0], t[1])

    def create_newtoken(self, text, props):
        newtoken = Token2(text, order=len(self.tokens))
        try:
            newtoken.start = int(props["CharacterOffsetBegin"])
            newtoken.dstart = newtoken.start + self.offset
            newtoken.end = int(props["CharacterOffsetEnd"])
            newtoken.dend = newtoken.end + self.offset
            newtoken.pos = props["PartOfSpeech"]
            newtoken.tag = props["NamedEntityTag"]
            newtoken.lemma = props["Lemma"]
            # newtoken.stem = porter.stem_word(newtoken.text)
            newtoken.tid = self.sid + ".t" + str(len(self.tokens))
            self.tokens.append(newtoken)
            # print "|{}| <=> |{}|".format(text, self.text[newtoken.start:newtoken.end])
        except KeyError:
            logging.debug("error: text={} props={}".format(text, props))
            return None
        # logging.debug(newtoken.text)
        return newtoken

    def add_relation(self, entity1, entity2, subtype, source="goldstandard", **kwargs):
        if self.pairs.pairs.get(source):
            pid = self.sid + ".p" + str(len(self.pairs.pairs[source]))
        else:
            pid = self.sid + ".p0"
        if subtype == "tlink":
            self.pairs.add_pair(TLink(entity1, entity2, original_id=kwargs.get("original_id"),
                                     did=self.did, pid=pid, rtype=subtype), source)

    def tag_entity(self, start, end, etype, entity=None, source="goldstandard", **kwargs):
        """Find the tokens that match this entity. start and end are relative to the sentence.
           Totalchars is the offset of the sentence on the document."""
        tlist = []
        # print self.tokens
        nextword = ""
        for t in self.tokens:
            # discard tokens that intersect the entity for now
            # print t.start, t.end, t.text
            if t.start >= start and t.end <= end:
                tlist.append(t)
            elif t.start == end+1:
                nextword = t.text
        if tlist:
            newtext = self.text[tlist[0].start:tlist[-1].end]
            if entity:
                entity.text = newtext
            if "text" in kwargs and newtext != kwargs["text"]:
                if newtext not in kwargs["text"] and kwargs["text"] not in newtext:
                    print "not added, text does not match", newtext, kwargs["text"]
                    return None
                else:
                    logging.info("{} {} |{}|=>|{}| {} {} {} {}".format(tlist[0].start, tlist[-1].end, newtext, kwargs["text"],
                                 start, end, self.sid, self.text))
            #     print "tokens found:", [t.text for t in tlist]
                # sys.exit()
            # else:
            # print "found the tokens!", start, end, kwargs["text"], self.sid
            if self.entities.elist.get(source):
                eid = self.sid + ".e" + str(len(self.entities.elist[source]))
            else:
                eid = self.sid + ".e0"
            if entity is None:
                entity = create_entity(tlist, self.sid, did=self.did, text=newtext, score=kwargs.get("score"),
                                       etype=etype, eid=eid, subtype=kwargs.get("subtype"),
                                       original_id=kwargs.get("original_id"), nextword=nextword)
            self.entities.add_entity(entity, source)
            self.label_tokens(tlist, source, etype)
            logging.debug("added {} to {}, now with {} entities".format(newtext, self.sid,
                                                                             len(self.entities.elist[source])))
            return eid
        else:
            print "no tokens found:"
            print self.sid, start, end, kwargs.get("text")
            print [(t.start, t.end, t.text) for t in self.tokens]

    def label_tokens(self, tlist, source, etype):
        if len(tlist) == 1:
            tlist[0].tags[source] = "single"
            tlist[0].tags[source + "_subtype"] = etype
            tlist[0].tags[source + "_" + etype] = "single"
        else:
            for t in range(len(tlist)):
                if t == 0:
                    tlist[t].tags[source] = "start"
                    tlist[t].tags[source + "_" + etype] = "start"
                    tlist[t].tags[source + "_subtype"] = etype
                elif t == len(tlist) - 1:
                    tlist[t].tags[source] = "end"
                    tlist[t].tags[source + "_" + etype] = "end"
                    tlist[t].tags[source + "_subtype"] = etype
                else:
                    tlist[t].tags[source] = "middle"
                    tlist[t].tags[source + "_" + etype] = "middle"
                    tlist[t].tags[source + "_subtype"] = etype
        #logging.debug([t.tags for t in self.tokens])

    def write_bioc_results(self, parent, source):
        bioc_sentence = ET.SubElement(parent, "sentence")
        bioc_sentence_offset = ET.SubElement(bioc_sentence, "offset")
        bioc_sentence_offset.text = str(self.tokens[0].dstart)
        bioc_sentence_text = ET.SubElement(bioc_sentence, "text")
        bioc_sentence_text.text = self.text

        if source in self.entities.elist:
            for entity in self.entities.elist[source]:
                bioc_annotation = entity.write_bioc_annotation(bioc_sentence)
        return bioc_sentence

    def get_dic(self, source):
        dic = {}
        dic["id"] = self.sid
        dic["offset"] = str(self.tokens[0].dstart)
        dic["text"] = self.text
        dic["entities"] = []
        if source in self.entities.elist:
            for entity in self.entities.elist[source]:
                dic["entities"].append(entity.get_dic())
            dic["entities"] = sorted(dic["entities"], key=lambda k: k['offset'])
            for ei, e in enumerate(dic["entities"]):
                e["eid"] = self.sid + ".e{}".format(ei)
        dic["pairs"] = self.pairs.get_dic()
        return dic

    def find_tokens(self, text, start, end, count, relativeto="doc"):
        candidates = []
        for t in self.tokens:
            if t.text == text:
                print t.text, text
                candidates.append(t)
        print text, candidates
        if len(candidates) == 0:
            print "could not find tokens!"
        elif len(candidates) == 1:
            return candidates
        elif len(candidates)-1 > count:
            candidates[count]
        """else:
            dist = []
            for c in candidates:
                if relativeto == "doc":
                    d = c.dstart
                else:
                    d = c.start
                dist.append(abs(d-start))
            return [candidates[dist.index(min(dist))]]"""

    def find_tokens_between(self, start, end, relativeto="doc"):
        """Return list of tokens between offsets. Use relativeto to consider doc indexes or
           sentence indexes."""
        foundtokens = []
        for t in self.tokens:
            if relativeto.startswith("doc") and t.dstart >= start and t.dend <= end:
                foundtokens.append(t)
            elif relativeto.startswith("sent") and t.start >= start and t.end <= end:
                foundtokens.append(t)
        return foundtokens

    def test_relations(self, pairs, basemodel, classifiers=[relations.SLK_PRED, relations.SST_PRED],
                       tag="", backup=False, printstd=False):
        #data =  ddi_train_slk.model, ddi_train_sst.model
        tempfiles = []

        if relations.SLK_PRED in classifiers:
            logging.info("**Testing SLK classifier %s ..." % (tag,))
            #testpairdic = ddi_kernels.fromddiDic(testdocs)
            ddi_kernels.generatejSREdata(pairs, self, basemodel, tag + "ddi_test_jsre.txt")
            ddi_kernels.testjSRE(tag + "ddi_test_jsre.txt", tag + "ddi_test_result.txt",
                                 model=tag + "all_ddi_train_slk.model")
            self.pairs.pairs = ddi_kernels.getjSREPredicitons(tag + "ddi_test_jsre.txt", tag + "ddi_test_result.txt",
                                                      self.pairs.pairs)
            tempfiles.append(ddi_kernels.basedir + tag + "ddi_test_jsre.txt")
            tempfiles.append(ddi_kernels.basedir + tag + "ddi_test_result.txt")

        if relations.SST_PRED in classifiers:
            logging.info("****Testing SST classifier %s ..." % (tag,))
            self.pairs.pairs = ddi_kernels.testSVMTK(self, self.pairs.pairs, pairs,
                                             model=tag + "all_ddi_train_sst.model", tag=tag)
        for p in self.pairs.pairs:
            for r in self.pairs.pairs[p].recognized_by:
                if self.pairs.pairs[p].recognized_by[r] == 1:
                    p.relation = True
        return tempfiles
