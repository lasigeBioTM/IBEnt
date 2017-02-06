# coding=utf-8
import os
import logging
import time
import sys
from operator import itemgetter
import pprint
from xml.dom import minidom

from nltk.stem.porter import *
import re
from collections import Counter
import operator
import progressbar as pb
from subprocess import check_output

from text.corpus import Corpus
from text.document import Document
import xml.etree.ElementTree as ET
from text.pair import Pairs


class TempEvalCorpus(Corpus):
    """
    TempEval corpus used for NER and RE on the SemEval - Clinical tempeval 2015.
    self.path is the base directory of the files of this corpus.
    """

    def __init__(self, corpusdir, **kwargs):
        super(TempEvalCorpus, self).__init__(corpusdir, **kwargs)
        self.invalid_sections = (20104, 20105, 20116, 20138)

    def load_corpus(self, corenlpserver):
        # self.path is the base directory of the files of this corpus

#         if more than one file:
        trainfiles = [self.path + f for f in os.listdir(self.path) if not f.endswith('~')] # opens all files in folder (see config file)
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', ' ', pb.Timer()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=len(trainfiles)).start()
        for i, openfile in enumerate(trainfiles):
            # print("file: "+openfile)
            with open(openfile, 'r') as inputfile:
                newdoc = Document(inputfile.read(), process=False, did=os.path.basename(openfile), title = "titulo_"+os.path.basename(openfile))
            newdoc.process_document(corenlpserver, "biomedical") #process_document chama o tokenizer
            valid = True
            invalid_sids = []
            for s in newdoc.sentences:
                if s.text in ['[start section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = False
                if not valid:
                    invalid_sids.append(s.sid)
                if s.text in ['[end section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = True
                if (s.text.startswith("[") and s.text.endswith("]")) or s.text.istitle():
                    newdoc.title_sids.append(s.sid)
            newdoc.invalid_sids = invalid_sids
            logging.debug("invalid sentences: {}".format(invalid_sids))
            logging.debug("title sentences: {}".format(newdoc.title_sids))
            self.documents[newdoc.did] = newdoc
            pbar.update(i+1)

    def get_invalid_sentences(self):
        for did in self.documents:
            self.documents[did].invalid_sids = []
            valid = True
            invalid_sids = []
            for s in self.documents[did].sentences:
                if s.text in ['[start section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = False
                if not valid or s.text.startswith("[meta"):
                    invalid_sids.append(s.sid)
                if s.text in ['[end section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = True
            self.documents[did].invalid_sids = invalid_sids
            logging.debug("invalid sentences: {}".format(invalid_sids))

    def load_annotations(self, ann_dir, entity_type, relation_type):
        self.stemmer = PorterStemmer()
        self.get_invalid_sentences()
        logging.info("Cleaning previous annotations...")
        for did in self.documents:
            for s in self.documents[did].sentences:
                if "goldstandard" in s.entities.elist:
                    s.entities.elist["goldstandard"] = []
        traindirs = os.listdir(ann_dir) # list of directories corresponding to each document
        trainfiles = []
        for d in traindirs:
            fname = ann_dir + "/" + d + "/" + d + ".Temporal-Relation.gold.completed.xml"
            fname2 = ann_dir + "/" + d + "/" + d + ".Temporal-Entity.gold.completed.xml"
            if os.path.isfile(fname):
                trainfiles.append(fname)
            elif os.path.isfile(fname2):
                    trainfiles.append(fname2)
            else:
                print "no annotations for this doc: {}".format(d)

        total = len(trainfiles)
        logging.info("loading annotations...")
        stats = {}
        relation_words = {}
        with open(self.path + self.name + "_time_entities.txt", 'w') as timefile:
            timefile.write("time\tlabel\tleft_window_5\tright_window_5\tleft_event_bitmap\tright_event_bitmap\tright_window_5_pos\tleft_window_5_pos\tword_pos\n")
        with open(self.path + self.name + "_event_type.txt", 'w') as typefile:
            typefile.write("event\tlabel\tleft_window_5\tright_window_5\tleft_event_bitmap\tright_event_bitmap\tright_window_5_pos\tleft_window_5_pos\tword_pos\n")
        with open(self.path + self.name + "_event_polarity.txt", 'w') as polfile:
            polfile.write("event\tlabel\tleft_window_5\tright_window_5\tleft_event_bitmap\tright_event_bitmap\tright_window_5_pos\tleft_window_5_pos\tword_pos\n")
        with open(self.path + self.name + "_event_degree.txt", 'w') as degfile:
            degfile.write("event\tlabel\tleft_window_5\tright_window_5\tleft_event_bitmap\tright_event_bitmap\tright_window_5_pos\tleft_window_5_pos\tword_pos\n")
        with open(self.path + self.name + "_event_modality.txt", 'w') as modfile:
            modfile.write("event\tlabel\tleft_window_5\tright_window_5\tleft_event_bitmap\tright_event_bitmap\tright_window_5_pos\tleft_window_5_pos\tword_pos\n")
        with open(self.path + self.name + "_doctimerel.txt", 'w') as dtrfile:
            dtrfile.write("event\tlabel\tleft_window_5\tright_window_5\tdoctate\tsentencetimes\n")
        for current, f in enumerate(trainfiles):
            logging.debug('%s:%s/%s', f, current + 1, total)
            with open(f, 'r') as xml:
                #parse DDI corpus file
                t = time.time()
                root = ET.fromstring(xml.read())
                did = traindirs[current]
                if did not in self.documents:
                    print "no text for this document: {}".format(did)
                    # sys.exit()
                    continue
                annotations = root.find("annotations")
                self.load_entities(annotations, did)
                all_words = Counter(re.split("\W", self.documents[did].text.lower()))

                doc_stats, doc_words = self.load_relations(annotations, did, all_words)
                #for k in doc_stats:
                    #if k not in stats:
                        #stats[k] = 0
                    #stats[k] += doc_stats[k]
                #for t in doc_words:
                    #if t not in relation_words:
                        #relation_words[t] = {}
                    #for w in doc_words[t]:
                        #if w not in relation_words[t]:
                            #relation_words[t][w] = 0
                        #relation_words[t][w] += doc_words[t][w]
        #pp = pprint.PrettyPrinter()
        #pp.pprint(stats)
        #for t in relation_words:
            #relation_words[t] = sorted(relation_words[t].items(), key=operator.itemgetter(1))[-20:]
            #relation_words[t].reverse()
        #pp.pprint(relation_words)


    def load_entities(self, annotations_tag, did):
        entity_list = []
        print self.path + "time_entities.txt"
        timefile = open(self.path + self.name + "_time_entities.txt", 'a')
        eventtype = open(self.path + self.name + "_event_type.txt", 'a')
        eventpolarity = open(self.path + self.name + "_event_polarity.txt", 'a')
        eventdegree = open(self.path + self.name + "_event_degree.txt", 'a')
        eventmodality = open(self.path + self.name + "_event_modality.txt", 'a')
        eventdtr = open(self.path + self.name + "_doctimerel.txt", 'a')
        for entity in annotations_tag.findall("entity"):
            span = entity.find("span").text
            if ";" in span:
                # entity is not sequential: skip for now
                continue
            span = span.split(",")
            start = int(span[0])
            end = int(span[1])
            entity_type = entity.find("type").text
            entity_id = entity.find("id").text
            entity_props = entity.find("properties")
            if entity_type == "EVENT":
                entity_subtype = entity_props.find("Type").text
                entity_polarity = entity_props.find("Polarity").text
                entity_degree = entity_props.find("Degree").text
                entity_modality = entity_props.find("ContextualModality").text
                entity_doctimerel = entity_props.find("DocTimeRel").text
                attributes = (entity_polarity, entity_degree, entity_modality, entity_doctimerel)
            elif entity_type == "TIMEX3":
                entity_subtype = entity_props.find("Class").text
                attributes = (None, None, None, None)
            else:
                entity_subtype = "all"
                attributes = (None, None, None, None)
            entity_list.append((start, end, entity_type, entity_id, entity_subtype, attributes))
        entity_list = sorted(entity_list, key=itemgetter(0)) # sort by start
        for e in entity_list:
            # print e, self.documents[did].text[e[0]:e[1]]
            entity_text = self.documents[did].text[e[0]:e[1]]

            if e[2] in ("EVENT", "TIMEX3", "SECTIONTIME", "DOCTIME"): # choose type: TIMEX3 or EVENT (also SECTIONTIME and DOCTIME)
                sentence = self.documents[did].find_sentence_containing(e[0], e[1], chemdner=False)
                if sentence is not None:
                    # e[0] and e[1] are relative to the document, so subtract sentence offset
                    start = e[0] - sentence.offset
                    end = e[1] - sentence.offset
                    eid = sentence.tag_entity(start, end, e[2].lower(), text=entity_text, original_id=e[3], subtype=e[4],
                                        polarity=e[5][0], degree=e[5][1], modality=e[5][2], doctimerel=e[5][3])
                    # print eid
                    if eid is None:
                        logging.info("skipped {}".format(e[3]))
                        continue
                    entity = sentence.entities.get_entity(eid)
                    # print e, self.documents[did].text[e[0]:e[1]]
                    #
                    #break_words = ["but", "with", "and"]
                    break_words = ["but", "with"]
                    # generate context windows

                    firsttoken = entity.tokens[0].order
                    lasttoken = entity.tokens[-1].order

                    lw = 10
                    before_tokens5 = []
                    before_count = 0
                    for i in range(firsttoken-1, -1, -1):
                        if sentence.tokens[i].text in break_words:
                            break
                        #if len(sentence.tokens[i].text) > 2 and "goldstandard_event" not in sentence.tokens[i].tags:
                        before_count += 1
                        #else:
                        #    print "ignored", sentence.tokens[i].text
                        before_tokens5 = [sentence.tokens[i]] + before_tokens5
                        if before_count == lw:
                            #if len(before_tokens5) > lw:
                            #    print len(before_tokens5)
                            break
                    #before_tokens = sentence.tokens[max(0,firsttoken-10):firsttoken]
                    #if len(before_tokens) < 10:
                        #print [t.text for t in bef6ore_tokens], entity.text, firsttoken
                    #    diff_tokens = 10 - len(before_tokens)
                    #    sentence_order = int(sentence.sid.split("s")[-1])
                    #    for i in range(sentence_order-1, -1, -1):
                    #        if self.documents[did].sentences[i].text[0].isupper():
                    #            main_sentence = self.documents[did].sentences[i]
                                #print sentence.text
                                #print "found main sentence", main_sentence.text
                    #            before_tokens = main_sentence.tokens[-diff_tokens:] + before_tokens
                    #            break
                    #after_tokens = sentence.tokens[lasttoken+1:lasttoken+6]
                    rw = 10
                    after_tokens5 = []
                    after_count = 0
                    for i in range(lasttoken+1,len(sentence.tokens)):
                        if sentence.tokens[i].text in break_words:
                            break
                        #if len(sentence.tokens[i].tags):
                        #    print sentence.tokens[i].tags
                        #if len(sentence.tokens[i].text) > 2 and "goldstandard_event" not in sentence.tokens[i].tags.keys():
                        after_count += 1
                        #else:
                        #    print "ignored", sentence.tokens[i].text
                        after_tokens5 =  after_tokens5 + [sentence.tokens[i]]
                        if after_count == rw:
                            #if len(after_tokens5) > rw:
                            #    print len(after_tokens5)
                            break

                    if e[2] == "EVENT":
                        sentence_time = "+".join([t.text for t in sentence.tokens if "goldstandard_timex3" in t.tags]) + "+"
                        doc_time = self.documents[did].text.split("\n")[0]
                        #if sentence_time:
                        #    print entity.text, entity.doctimerel, sentence_time
                        #    print doc_time

                    #before_context3 = "+" + "+".join([t.text for t in before_tokens3]) + "+"
                    before_context5 = "+" + "+".join([t.text for t in before_tokens5]) + "+"
                    #after_context3 = "+" + "+".join([t.text for t in after_tokens3]) + "+"
                    after_context5 = "+" + "+".join([t.text for t in after_tokens5]) + "+"
                    before_pos5 = "+" + "+".join([t.pos for t in before_tokens5]) + "+"
                    #before_pos5 = "+" + "+".join([t.pos for t in before_tokens5]) + "+"
                    after_pos5 = "+" + "+".join([t.pos for t in after_tokens5]) + "+"
                    before_events5 = "".join([str(int("goldstandard_event" in t.tags)) for t in before_tokens5])
                    after_events5 = "".join([str(int("goldstandard_event" in t.tags)) for t in after_tokens5])
                    word_pos = "+" + "+".join([t.pos for t in entity.tokens]) + "+"
                    if e[2] == "TIMEX3":
                        timefile.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity_text, entity.subtype,
                                                        before_context5, after_context5,
                                                        before_events5, after_events5,
                                                        before_pos5, after_pos5,
                                                        word_pos))
                    elif e[2] == "EVENT":
                        eventtype.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity.text, entity.subtype,
                                                        before_context5, after_context5,
                                                        before_events5, after_events5,
                                                        before_pos5, after_pos5,
                                                        word_pos))
                        eventpolarity.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity.text, entity.polarity,
                                                        before_context5, after_context5,
                                                        before_events5, after_events5,
                                                        before_pos5, after_pos5,
                                                        word_pos))
                        eventdegree.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity.text, entity.degree,
                                                        before_context5, after_context5,
                                                        before_events5, after_events5,
                                                        before_pos5, after_pos5,
                                                        word_pos))
                        eventmodality.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity.text, entity.modality,
                                                        before_context5, after_context5,
                                                        before_events5, after_events5,
                                                        before_pos5, after_pos5,
                                                        word_pos))
                        eventdtr.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(entity.text, entity.doctimerel,
                                                                        before_context5, after_context5,
                                                                        before_pos5, after_pos5,
                                                                        doc_time, sentence_time, word_pos))
                        #eventtype.write("{}\t{}\n".format(entity_text, e[4]))
                        #eventpolarity.write("{}\t{}\n".format(entity_text, e[5][0]))
                        #eventdegree.write("{}\t{}\n".format(entity_text, e[5][1]))
                        #eventmodality.write("{}\t{}\n".format(entity_text, e[5][2]))

                else:
                    print "could not find sentence for this span: {}-{}".format(e[0], e[1])
        eventtype.close()
        eventpolarity.close()
        eventdegree.close()
        eventmodality.close()
        timefile.close()





    def load_relations(self, annotations_tag, did, allwords):
        stats = {"path_count": 0, "clinic_count": 0,
                 "path_doc_chars": 0, "clinic_doc_chars": 0,
                 "path_nentities": 0, "clinic_nentities": 0,
                 "path_nrelations": 0, "clinic_nrelations": 0,
                 "path_relation_dist": 0, "clinic_relation_dist": 0,
                 "path_event_time": 0, "path_time_event": 0, "path_time_time": 0, "path_event_event": 0,
                 "clinic_event_time": 0, "clinic_time_event": 0, "clinic_time_time": 0, "clinic_event_event": 0,

                 "path_nevent_source": 0, "path_ntime_source": 0,
                 "clinic_nevent_source": 0, "clinic_ntime_source": 0,
                 "path_nevent_target": 0, "path_ntime_target": 0,
                 "clinic_nevent_target": 0, "clinic_ntime_target": 0,
                 "clinic_multisentence":0, "path_multisentence": 0}

        wordsdic = {"path_event_time": {}, "path_time_event": {}, "path_time_time": {}, "path_event_event": {},
                 "clinic_event_time": {}, "clinic_time_event": {}, "clinic_time_time": {}, "clinic_event_event": {}}
        if "path" in did:
            doc_type = "path_"
        else:
            doc_type = "clinic_"
        stats[doc_type + "count"] += 1
        stats[doc_type + "doc_chars"] += len(self.documents[did].text)
        source_relation = {} # (source original id, target original id, relation original id)
        entity_list = {} # all entities of this document original_id => entity
        for relation in annotations_tag.findall("relation"):
            stats[doc_type + "nrelations"] += 1
            props = relation.find("properties")
            source_id = props.find("Source").text
            target_id = props.find("Target").text
            # relation_type = relation.find("type").text
            #relation_id = relation.find("id").text
            if source_id not in source_relation:
                source_relation[source_id] = []
            source_relation[source_id].append(target_id)
        self.documents[did].pairs = Pairs()
        for sentence in self.documents[did].sentences:
            if "goldstandard" in sentence.entities.elist:
                for entity in sentence.entities.elist["goldstandard"]:
                    entity_list[entity.original_id] = entity
                    stats[doc_type + "nentities"] += 1
        for eid in entity_list:
            entity = entity_list[eid]
            entity.targets = []
            if entity.original_id in source_relation:
                for target in source_relation[entity.original_id]:
                    if target not in entity_list:
                        print "target not in entity list:", target
                    else:
                        #pairwordsdic = {}
                        entity.targets.append((entity_list[target].eid, "temporal"))
                        #e2 = get_entity(self.documents[did], entity_list[target].eid)
                        # print "{}:{}=>{}:{}".format(entity.type, entity.text, e2.type, e2.text)
                        # print "||{}||".format(self.documents[did].text[entity.dstart:e2.dend])

                        #stats[doc_type + "relation_dist"] += len(self.documents[did].text[entity.dend:e2.dstart])
                        #stats[doc_type + "n{}_source".format(entity.type)] += 1
                        #stats[doc_type + "n{}_target".format(e2.type)] += 1
                        #stats[doc_type + "{}_{}".format(entity.type, e2.type)] += 1

                        #words = re.split("\W", self.documents[did].text[entity.dend:e2.dstart].lower())
                        #stems = set()
                        #stems = []
                        #for w in words:
                            #if w.strip() == "":
                                #continue
                            #if w.isdigit():
                            #    stem = "#digit#"
                            #else:
                                #stem = self.stemmer.stem(w)
                            #    stem = w
                            #stems.add(stem)
                            #stems.append(w)
                        #for stem in stems:
                            #if stem not in pairwordsdic:
                                #pairwordsdic[stem] = 0
                            #pairwordsdic[stem] += 1


                        #if e2.sid != entity.sid:
                            #stats[doc_type + "multisentence"] += 1
                        #for stem in pairwordsdic:
                            #if stem not in wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)]:
                                #wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)][stem] = 0
                            #wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)][stem] += pairwordsdic[stem]*1.0/allwords[stem]
                """        # logging.debug("multi-sentence:{}+{}".format(sentence1.text, sentence2.text))
                        chardist = e2.dstart - e1.dend
                        if chardist > maxdist[0] and e1.type != "time" and not e1.text.isupper():
                            print e1.type
                            maxdist = (chardist, "{}=>{}".format(e1, e2))
                        # logging.debug("dist between entities: {}".format(chardist))"""
                    # logging.debug("|{}|=>|{}|".format(e1.text, e2.text))
                    #self.documents[did].add_relation(e1, e2, "tlink", relation=True)
                """    npairs += 1
                elif '\n' not in self.documents[did].text[e1.dstart:e2.dend] or e1.text.isupper() or e1.type == "time":
                    self.documents[did].add_relation(e1, e2, "tlink", relation=False)
                    npairs += 1
                if (e2.original_id, e1.original_id) in relation_list:
                    inverted += 1"""
                """    if e1.sid != e2.sid:
                        sentence1 = self.documents[did].get_sentence(e1.sid)
                        sentence2 = self.documents[did].get_sentence(e2.sid)
                        # logging.debug("multi-sentence:{}+{}".format(sentence1.text, sentence2.text))
                        chardist = e2.dstart - e1.dend
                        if chardist > maxdist[0] and e2.type != "timex3" and not e2.text.isupper():
                            #print e2.type
                            maxdist = (chardist, "{}<={}".format(e1, e2))
                        # logging.debug("dist between entities: {}".format(chardist))

                    # logging.debug("|{}|<=|{}|".format(e1.text, e2.text))
                    self.documents[did].add_relation(e2, e1, "tlink", relation=True, original_id=relation_id)
                else:
                    self.documents[did].add_relation(e2, e1, "tlink", relation=False, original_id=relation_id)"""
        return stats, wordsdic


def get_entity(document, eid, source="goldstandard"):
    for sentence in document.sentences:
        if source in sentence.entities.elist:
            for e in sentence.entities.elist[source]:
                if e.eid == eid:
                    return e
    print "no entity found for eid {}".format(eid)
    return None

def run_anafora_evaluation(annotations_path, results, doctype="all", etype=""):
    anafora_command = ["python", "-m", "anafora.evaluate", "-r", annotations_path, "-p", results,
                       "-i", etype.upper()]
    if doctype != "all":
        anafora_command += ["-x", ".*{}.*".format(doctype)]
    r = check_output(anafora_command)
    return r

def write_tempeval_results(results, models, ths, rules):
    print "saving results to {}".format(results.path + ".tsv")
    n = 0
    for did in results.corpus.documents:
        root = ET.Element("data") # XML data
        head = ET.SubElement(root, "annotations") #XML annotations


        for sentence in results.corpus.documents[did].sentences:
            entity_tokens = set()
            sentence_entities = []
            for s in sentence.entities.elist:
                if s.startswith(models):
                    for e in sentence.entities.elist[s]:
                        val = e.validate(ths, rules)
                        if not val:
                            continue
                        entity_tokens.update(set([t.order for t in e.tokens]))
                        sentence_entities.append(val)
                    for val in sentence_entities:
                        # iterate over val in case it was split into multiple entities
                        for iv, v in enumerate(val):
                            v.set_attributes(sentence.tokens, entity_tokens)
                            n=n+1
                            head = add_entity_to_doc(head, v, n)

        #for p in results.document_pairs[did].pairs:
        #    if p.recognized_by.get("svmtk") == 1 or p.recognized_by.get("jsre") == 1 or p.recognized_by.get("rules") == 1:
        #        head = add_relation_to_doc(head, p)

        #tree = ET.ElementTree(root)
        if not os.path.exists(results.path + "/" + did + "/"):
            os.makedirs(results.path + "/" + did + "/")
        name = results.path + "/" + did + "/" + did + ".Temporal-Relation.system.completed.xml"
        x = ET.tostring(root)
        try:
            xmlstr = minidom.parseString(x)
            xmlstr = xmlstr.toprettyxml(indent="   ")
            with open(name, "w") as f:
                f.write(xmlstr)
        except:
            print x

def write_tempeval_relations_report(results, goldset, path="relations_report.txt"):
    all_pairs = set()
    lines = []
    for did in results.corpus.documents:
        for p in results.document_pairs[did].pairs:
            if p.recognized_by.get("svmtk") == 1 or p.recognized_by.get("jsre") == 1 or p.recognized_by.get("rules") == 1:
                pair = (did, (p.entities[0].dstart, p.entities[0].dend), (p.entities[1].dstart, p.entities[1].dend))
                if pair in goldset:
                    # tp.append(p)
                    lines.append((p.did, "TP", p.entities[0].text + "=>" + p.entities[1].text,
                                 results.corpus.documents[did].text[pair[1][1]:pair[2][0]]))
                else:
                    lines.append((p.did, "FP", p.entities[0].text + "=>" + p.entities[1].text,
                                  results.corpus.documents[did].text[pair[1][1]:pair[2][0]]))
                all_pairs.add(pair)
    for pair in goldset:
        if pair not in all_pairs:
            lines.append((p.did, "FN", results.corpus.documents[did].text[pair[1][0]:pair[1][1]] + "=>" +\
                           results.corpus.documents[did].text[pair[2][0]:pair[2][1]],
                          results.corpus.documents[did].text[pair[1][1]:pair[2][0]]))
    lines.sort()
    with codecs.open(path, "w", "utf-8") as report:
        for l in lines:
            report.write("\t".join(l) + "\n")
    # print random.sample(all_pairs,5)
    # print random.sample(goldset,5)


def add_entity_to_doc(doc_element, entity, n):
    entityname = ET.SubElement(doc_element, "entity")
    id = ET.SubElement(entityname, "id")
    id.text = "t" + str(n)
    #entityname.append(ET.Comment(entity.text))
    #id.text = str(len(doc_element.findall("entity")))
    span = ET.SubElement(entityname, "span")
    span.text = str(entity.dstart)+","+str(entity.dend)
    etype = ET.SubElement(entityname, "type")
    propertiesname = ET.SubElement(entityname, "properties")
    if entity.type == "time":
        etype.text = "TIMEX3"
        timeclass = ET.SubElement(propertiesname, "Class")
        timeclass.text = entity.subtype
    else:
        etype.text = "EVENT"
        subtype = ET.SubElement(propertiesname, "Type")
        subtype.text = entity.subtype
        modality = ET.SubElement(propertiesname, "ContextualModality")
        modality.text = entity.modality
        polarity = ET.SubElement(propertiesname, "Polarity")
        polarity.text = entity.polarity
        dtr = ET.SubElement(propertiesname, "DocTimeRel")
        dtr.text = entity.dtr
        degree = ET.SubElement(propertiesname, "Degree")
        degree.text = entity.degree


    #classs = ET.SubElement(propertiesname, "Class")
    #value = ET.SubElement(propertiesname, "Value")
    ####
    #propertiesname = ET.SubElement(entityname, "properties") #XML
    #classs = ET.SubElement(propertiesname, "Class") # XML
    #classs.text = "asdasd"#entity.tag
    ##
    return doc_element

def add_relation_to_doc(doc_element, relation):
    relationname = ET.SubElement(doc_element, "relation") #XML entity
    id = ET.SubElement(relationname, "id") #XML id
    id.text = convert_id(relation.pid)
    # id.append(ET.Comment(relation.entities[0].text + "+" + relation.entities[1].text))
    #id.text = str(len(doc_element.findall("entity"))) esta so comentado
    type = ET.SubElement(relationname, "type") #XML
    type.text = "TLINK"
    # entity1 = ET.SubElement(relationname, "parentsType")
    # entity1.text = "TemporalRelations"
    propertiesname = ET.SubElement(relationname, "properties") #XML
    source = ET.SubElement(propertiesname, "Source") # XML
    source.text = convert_id(relation.entities[0].eid)
    propertiesname.append(ET.Comment("Source:{}".format(relation.entities[0].text)))
    t = ET.SubElement(propertiesname, "Type") # XML
    t.text = "CONTAINS"
    target = ET.SubElement(propertiesname, "Target") # XML
    target.text = convert_id(relation.entities[1].eid)
    propertiesname.append(ET.Comment("Target:{}".format(relation.entities[1].text)))
    return doc_element


def get_thymedata_gold_ann_set(gold_path, etype, text_path, doctype):
    gold_set = set()
    relation_gold_set = set() # (did,(start,end),(start,end))
    doc_to_id_to_span = {}
    traindirs = os.listdir(gold_path) # list of directories corresponding to each document
    trainfiles = []
    for d in traindirs:
        if doctype != "tempeval" and doctype not in d:
            continue
        fname = gold_path + "/" + d + "/" + d + ".Temporal-Relation.gold.completed.xml"
        fname2 = gold_path + "/" + d + "/" + d + ".Temporal-Entity.gold.completed.xml"
        if os.path.isfile(fname):
            trainfiles.append(fname)
        elif os.path.isfile(fname2):
                trainfiles.append(fname2)
        else:
            print "no annotations for this doc: {}".format(d)

    total = len(trainfiles)
    # logging.info("loading annotations...")
    for current, f in enumerate(trainfiles):
        # logging.debug('%s:%s/%s', f, current + 1, total)
        with open(f, 'r') as xml:
            #logging.debug("opening {}".format(f))
            root = ET.fromstring(xml.read())
            did = traindirs[current]
            doc_to_id_to_span[did] = {}
            with open(text_path + "/" + did) as text_file:
                doc_text = text_file.read()
            annotations = root.find("annotations")
            for entity in annotations.findall("entity"):
                eid = entity.find("id").text
                span = entity.find("span").text
                if ";" in span:
                    # entity is not sequential: skip for now
                    continue
                span = span.split(",")
                start = int(span[0])
                end = int(span[1])
                entity_type = entity.find("type").text.lower()
                doc_to_id_to_span[did][eid] = (start, end)
                # logging.debug(entity_type)
                if etype != "all" and entity_type != etype:
                    continue
                else:
                    gold_set.add((did, start, end, doc_text[start:end]))
            # print doc_to_id_to_span[did]
            for relation in annotations.findall("relation"):
                props = relation.find("properties")
                if props.find("Type").text == "CONTAINS":
                    eid1 = props.find("Source").text
                    eid2 = props.find("Target").text
                    if eid1 not in doc_to_id_to_span[did] or eid2 not in doc_to_id_to_span[did]:
                        # print "excluded", eid1, eid1 in doc_to_id_to_span, eid2, eid2 in doc_to_id_to_span
                        continue
                    relation_gold_set.add((did, doc_to_id_to_span[did][eid1], doc_to_id_to_span[did][eid2], ""))
    print "entities from gold standard:", len(gold_set)
    return gold_set, relation_gold_set
