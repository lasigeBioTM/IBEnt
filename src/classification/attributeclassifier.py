import re


def check_between (e, window, bitmap, labels=("POS", "NEG")):
    # check if there is an event between the trigger word and the event in this window, according to bitmap
    polarityPredicted = labels[0]
    # start the search for events in between
    window_array = window.split("+") # +,+not+amenable+to+endoscopic+) -> [',', 'not', ...]
    # remove empty strings
    window_array = filter(None, window_array)
    #print "======================="
    #print "=> negative expression matched: " + str(e)
    #print "=> window array: " + str(window_array)
    position = 0
    window_between = []
    # find the negation word and select the words between the negation and the event
    bitmap_between=""
    for word in window_array:
        if word != '.' and re.search(word, e, re.IGNORECASE):
             #print "\t\t===>" + str(word)
             window_between = window_array[position+1:] # +not+amenable+to+endoscopic+
             bitmap_between = bitmap[position+1:] #100
        position += 1

    position = 0
    last_event = -1
    #print "=> windows between: " + str(window_between)
    #print "=> bitmap between: " + str(bitmap_between)
    # check if there is an event and/or a list word or in the between words

    for word in window_between:
        if re.search(word,'(was|of|any|be)', re.IGNORECASE) and last_event>=0 and 'condition' not in window_array :  #como por dois caracteres ",or"
            last_event=-1 # ignores the last event since it is a list of events
            # print "\t\t===> ignored last event due to: " + word
        elif bitmap_between[position] == '1':
            last_event = position
            # print "\t\t===> event between found: " + word
        position += 1
    if last_event == -1:  #no events in between words
       polarityPredicted = labels[1]

    # polarityPredicted="NEG"
    #print "=> polarity predicted: " + polarityPredicted
    return polarityPredicted


def classify_polarity(event, leftwindow, rightwindow, bitmap_left):

        regexpNegBoth = ['avoid','absent','none','never','denies','\+not\+(present|really|recommend|identif|a\+problem\+|given\+|indicated|making|feel|be\+able|been|see\+)','\+any\+(definitive\+|reason|signs|way\+)','unlike','\+no\+(erythema|cervical|fevers|history)\+','\+-\+(negative\+|no\+)','\+,\+or\+','minimally\+-\+invasive\+']
        regexpNegRight = []
        regexpNegLeft = ['\+no\+','\+fail\+','\+free\+','unnecessary','attempted','yet','denying','absen','\+not\+','without','\+negative\+','\+unable\+','\+too\+small\+','nonpolyposis','\+nor\+','\+or\+(other\+|peripheral|current|any|sign|hoarse|anesthetic|metastatic|illicit)','\+of\+any\+','nothing','\+too\+many\+']
        polarityPredicted = "POS"

        #print "event       = " + event
        #print "window      = " + leftwindow + rightwindow
        #print "bitmap_left = " + bitmap_left

        # remove leftwindow part before . and when there is a :
        if re.search('\..+:', leftwindow, re.IGNORECASE):
            #print "=> before leftwindow: " + leftwindow
            position = 0
            window_array = leftwindow.split("+")
            window_array = filter(None, window_array)
            window_between = []
            bitmap_between = ""
            for word in window_array:
                #print "\t=> window array: " + str(word)
                if word == '.' :
                     window_between = window_array[position+1:] # +not+amenable+to+endoscopic+
                     bitmap_between = bitmap_left[position+1:] #100
                if word == ':' and len(window_between) > 0:
                     window_array = window_between
                     bitmap_left = bitmap_between
                     leftwindow = '+' + '+'.join(window_array) + "+"
                position += 1
            #print "=> after leftwindow: " + leftwindow

        for e in regexpNegBoth:
            if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
                #print "matched expression = " + e
                polarityPredicted = check_between (e,leftwindow,bitmap_left)

        if polarityPredicted == "POS":
            for e in regexpNegLeft:
                #print "matched expression = " + e
                if re.search(e, leftwindow, re.IGNORECASE):
                    polarityPredicted = check_between (e,leftwindow,bitmap_left)

        if polarityPredicted == "POS":
            for e in regexpNegRight:
                if re.search(e, rightwindow, re.IGNORECASE):
                    polarityPredicted = "NEG"


        return polarityPredicted


def classify_modality(event, leftwindow, rightwindow, bitmap_left):
    regexpNegBothHedged = []
    regexpNegRightHedged = []
    regexpNegLeftHedged = ['\+tiny\+', 'believes', 'seems', 'likely', 'suspect', 'suspicious', 'seem',
                           'consistent\+with\+', 'appears', 'questionable', 'apparently', '\+may\+very\+well\+',
                           'thought\+by\+', 'definite', '\+known\+', 'possibly', 'recommend', '\+risk\+of\+',
                           'inclination']
    regexpNegBothHypothetical = ['\+may\+be\+made\+', 'in\+case\+of\+', '\+would\+be\+', ]
    regexpNegRightHypothetical = []
    regexpNegLeftHypothetical = ['\+if\+', 'might', 'any\+substantive', 'future', 'whether', '\+likely\+', 'potential',
                                 'possibility', '\+will\+try\+', '\+stable\+to\+', '\+I\+feel\+']
    regexpNegLeftHypotheticalCase = [
        '\+may\+', ]  # depois testar sem not                                                                     #depois tentar sem months
    regexpNegBothGeneric = ['\+in\+general\+', 'usually', '\+should\+not\+', '\+can\+', '\+not\+had\+', '\+allow\+',
                            '\+do\+not\+', 'include\+', '\+while\+', 'routinely', '\+(months\+|hour)', '\+best\+to\+', ]
    regexpNegRightGeneric = []
    regexpNegLeftGeneric = ['\+emerging\+', 'logistics']
    ModalityPredicted = "ACTUAL"

    for e in regexpNegBothHedged:
        if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
            ModalityPredicted = "HEDGED"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegLeftHedged:
            if re.search(e, leftwindow, re.IGNORECASE):
                ModalityPredicted = "HEDGED"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegRightHedged:
            if re.search(e, rightwindow, re.IGNORECASE):
                ModalityPredicted = "HEDGED"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegBothHypothetical:
            if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
                ModalityPredicted = check_between(e, leftwindow, bitmap_left, labels=("ACTUAL", "HYPOTHETICAL"))
                # ModalityPredicted = "HYPOTHETICAL"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegLeftHypothetical:
            if re.search(e, leftwindow, re.IGNORECASE):
                # print e
                ModalityPredicted = check_between(e, leftwindow, bitmap_left, labels=("ACTUAL", "HYPOTHETICAL"))
                # ModalityPredicted = "HYPOTHETICAL"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegLeftHypotheticalCase:
            if re.search(e, leftwindow):
                # print e
                ModalityPredicted = check_between(e, leftwindow, bitmap_left, labels=("ACTUAL", "HYPOTHETICAL"))
                # ModalityPredicted = "HYPOTHETICAL"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegRightHypothetical:
            if re.search(e, rightwindow, re.IGNORECASE):
                # print "hello"
                ModalityPredicted = check_between(e, leftwindow, bitmap_left, labels=("ACTUAL", "HYPOTHETICAL"))
                # ModalityPredicted = "HYPOTHETICAL"

    if ModalityPredicted == "ACTUAL":
        for e in regexpNegBothGeneric:
            if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
                ModalityPredicted = "GENERIC"

        if ModalityPredicted == "ACTUAL":
            for e in regexpNegLeftGeneric:
                if re.search(e, leftwindow, re.IGNORECASE):
                    ModalityPredicted = "GENERIC"

        if ModalityPredicted == "ACTUAL":
            for e in regexpNegRightGeneric:
                if re.search(e, rightwindow, re.IGNORECASE):
                    ModalityPredicted = "GENERIC"

    return ModalityPredicted

def classify_doctimerel(event, leftwindow, rightwindow, leftpos, rightpos, wordpos):

    DTRPredicted = "OVERLAP"
    regexBeforeTemporal = ['Initially', 'that\+time', "in\+the\+past" "\+ago\+", "in\+the+last", "the\+time",
                           "since\+then", "last\+few", "previously"]
    regexBeforeTemporal = ['Initially', 'that\+time', "in\+the\+past" "\+ago\+", "in\+the+last", "the\+time",
                           "since\+then", "last\+few", "previously"]
    regexBeforeWordPos = ['VBD']
    # print event, leftwindow, rightwindow, leftpos, rightpos, temporal, wordpos
    regexBothAfter = ["will", "tomorrow", "next", "post", "adjuvant"]
    regexPosAfter = ["MD"]
    regexLeftPosBefore = ["VBD"]
    # regexBeforeWordPos = ['']
    # regexLeftAfter = []
    # regexRightAfter = []
    # regexLeftPosAfter = []
    # regexRightPosAfter = []

    for e in regexBothAfter:
        if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
            DTRPredicted = "AFTER"

    for e in regexPosAfter:
        if re.search(e, leftpos + rightpos, re.IGNORECASE):
            DTRPredicted = "AFTER"
    # print temporal
    for e in regexBeforeTemporal:
        if re.search(e, leftwindow + rightwindow, re.IGNORECASE):
            # print temporal, e
            DTRPredicted = "BEFORE"

    for e in regexBeforeWordPos:
        if re.search(e, wordpos, re.IGNORECASE):
            DTRPredicted = "BEFORE"

    for e in regexLeftPosBefore:
        if re.search(e, leftpos, re.IGNORECASE):
            DTRPredicted = "BEFORE"

    return DTRPredicted

def classify_type(event, leftwindow, rightwindow):
    types = []

    regexpAspectual = ['\+results\+will\+be\+available']
    regexpEvidential = ['\+to\+have\+colon\+polyps\+in\+']

    type = 'N/A'

    for h in regexpAspectual:
        if re.search(h, leftwindow + rightwindow, re.IGNORECASE) \
        or re.search(r'nonrecurrent|(R|r)e-recurrent|Resume|Continuous|lasted|pursued|arises|initiated|initiating|quit|(O|o)ngoing|commenced|conclusion|finishing|finishes|began|stop|remains|remain|reinitiated|continued|hold|reoccurred|reappeared|(C|c)ontinue|encourage|maintained|pulled|resuming|completed|complete|continuing|starting|started|start|completion', event):
            type = 'ASPECTUAL'
            types.append(event)
            types.append(type)

        for h in regexpEvidential:
            if re.search(h, leftwindow + rightwindow, re.IGNORECASE) \
            or re.search(r'warned|(^sounded$)|indicating|conceded|(^(n|N)oticed$)|recalled|characterizes|(r|R)eportedly|opportunity|nervous|expresses|(^prefer$)|encouraged|denying|endorse|spirits|manifest|appreciated|adamant|summarized|determined|impression|unaware|gathered|verified|indicative|signifies|merits|recollection|detected|cognizant|REPORTED|tell|indicates|looks|suggestive|believes|(^admits$)|(^notice$)|expressed|(^suggest$)|visualized|demonstrate|(^reflect$)|reflecting|believe|wishing|estimation|states|stated|FINDINGS|voiced|(^admit$)|discusses|think|represent|acknowledges|reveal|considers|reveals|mentions|says|noticing|(^(d|D)ue$)|revealing|heard|(^felt$)|suggesting|according|(^(p|P)er$)|identifying|verbalized|notes|feel|mentioned|evidence|informs|show|noted|told|identified|confirm|demonstrating|demonstrated|found|tells|describes|described|(^(D|d)enies$)|relates', event):
                type = 'EVIDENTIAL'
                types.append(event)
                types.append(type)

    if type == 'N/A':
        types.append(event)
        types.append(type)

    return types

#To remove the '+' from the beginning and the end.
def singlestrip(x):
    y = x[1:-1]
    return y


#Processes the lines. The replaces are meant to "mask" the '+++' segments that might existe, since they mean an '+' was the next character in the window, and if we don't
#mask it then we'll get two empty strings when we split, instead of one with a '+'
def processline(event, lw, rw):
    y = {}
    y['Event'] = event
    l2 = lw.replace('+++','+$%%$+')
    l2list = singlestrip(l2).split('+')
    y['Lw'] = [i.replace('$%%$','+').upper() for i in l2list]
    l3 = rw.replace('+++','+$%%$+')
    l3list = singlestrip(l3).split('+')
    y['Rw'] = [i.replace('$%%$','+').upper() for i in l3list]
    #y['LEBitmap'] = l[4]
    #y['REBitmap'] = l[5]
    #y['Rwp'] = singlestrip(l[6]).split('+')
    #y['Lwp'] = singlestrip(l[7]).split('+')
    y['DegreePredicted'] = 'N/A'
    return y



ListLittle = ['SLIGHT', 'MINIMAL', 'SLIGHT', 'LITTLE', 'RARELY', 'MINIMALLY', 'BARELY', 'TRACE']
#Palavras que podem introduzir demasiado bias -> Barely, Trace
#Palvras que tambem o podem fazer, mas menos provavel -> Slight, Little, Minimally, Rarely
LittleLeftWindowsList = [1, 2, 1, 3, 2, 1, 1, 2]
LittleRightWindowsList = [0, 0, 0, 0, 0, 0, 0, 0]
LittleZip = zip(ListLittle,LittleLeftWindowsList,LittleRightWindowsList)

ListMost = ['ALMOST', 'OVERLY', 'ALMOST COMPLETELY', 'ASIDE FROM']
MostLeftWindowsList = [2, 1, 0 ,0]
MostRightWindowsList = [0, 0, 3, 3]
MostZip = zip(ListMost,MostLeftWindowsList,MostRightWindowsList)
#Palavras que podem introduzir demasiado bias -> Almost, Overly, Almost Completely, Aside From

def classify_degree(event, lw, rw):
    l = processline(event, lw, rw)
    for wordM, LeftwindowM, RightwindowM in MostZip:
        tt = wordM.split()
        n = len(tt)
        if n == 1:
            if (wordM in l['Lw'][-LeftwindowM:] or wordM in l['Rw'][:RightwindowM]):
                l['DegreePredicted'] = 'MOST'
                break
        if n == 2:
            if RightwindowM >=n: #Isto e uma protecao meio infantil. Basta nao por na lista uma Window menor que o numero de palavras
                if tt[0] in l['Rw'][:RightwindowM][:-n]:
                    index = l['Rw'][:RightwindowM].index(tt[0])
                    if l['Rw'][:RightwindowM][index+1] == tt[1]:
                        l['DegreePredicted'] = 'MOST'
                        break
            if LeftwindowM >=n:
                if tt[0] in l['Lw'][-LeftwindowM:][:-n]:
                    index = l['Lw'][-LeftwindowM:].index(tt[0])
                    if l['Lw'][-LeftwindowM:][index+1] == tt[1]:
                        l['DegreePredicted'] = 'MOST'
                        break
    for wordL, LeftwindowL, RightwindowL in LittleZip:
        tt = wordL.split()
        n = len(tt)
        if n == 1:
            if (wordL in l['Lw'][-LeftwindowL:] or wordL in l['Rw'][:RightwindowL]):
                if l['DegreePredicted'] == 'MOST':
                    print 'Houve substituicao de most por little na palavra '+ str(wordL)
                l['DegreePredicted'] = 'LITTLE'
                break
            if RightwindowL >=n: #Isto e uma protecao meio infantil. Basta nao por na lista uma Window menor que o numero de palavras
                if tt[0] in l['Rw'][:RightwindowL][:-n]:
                    index = l['Rw'][:RightwindowL].index(tt[0])
                    if l['Rw'][:RightwindowL][index+1] == tt[1]:
                        if l['DegreePredicted'] == 'MOST':
                            print 'Houve substituicao de most por little na palavra '+ str(wordL)
                        l['DegreePredicted'] = 'LITTLE'
                        break
            if LeftwindowL >=n:
                if tt[0] in l['Lw'][-LeftwindowL:][:-n]:
                    index = l['Lw'][-LeftwindowL:].index(tt[0])
                    if l['Lw'][-LeftwindowL:][index+1] == tt[1]:
                        if l['DegreePredicted'] == 'MOST':
                            print 'Houve substituicao de most por little na palavra '+ str(wordL)
                        l['DegreePredicted'] = 'LITTLE'
                        break
    return l['DegreePredicted']

def classify_time(time_expression, leftwindow, rightwindow):
    types = []


    regexpSET = ['\+\d{1,4}\+-\+mg\+']
    regexpQUANTIFIER = ['withoutcontext']
    regexpTIME = ['\+of\+dismissal\+']
    regexpPREPOSTEXP = ['withoutcontext']
    regexpDURATION = ['\+((G|g)reater|(L|l)ess)\+than\+\d{1,2}\+%\+of\+']

    ptype = 'DATE'

    for h in regexpSET:
        if re.search(h, leftwindow + rightwindow, re.IGNORECASE)\
        or re.search(r'^\d{1,3}\s/[a-zA-Z]',time_expression)\
        or re.search(r'^(weekly|a\smonthly|nightly|(D|d)aily|in\sthe\sevening|each\s(day|evening))$',time_expression)\
        or re.search(r'every|average',time_expression)\
        or re.search(r'(\s|-)daily$',time_expression)\
        or (re.search(r'by\smouth', time_expression) and re.search(r'daily', time_expression))\
        or re.search(r'per\s(day|week)$',time_expression)\
        or (re.search(r'mg|gm|pounds', time_expression) and re.search(r'^((M|m)ore\sthan|(G|g)reater|(L|l)ess\sthan)', time_expression))\
        or re.search(r'[a-zA-Z]{3,10}\stimes\sa\sday',time_expression):
            ptype = 'SET'
            types.append(time_expression)
            types.append(ptype)

        for h in regexpQUANTIFIER:
            if re.search(h, leftwindow + rightwindow, re.IGNORECASE)\
            or re.search(r'^(first|one|two|both|three|four|five|six|seven|eight|nine|ten)$', time_expression)\
            or re.search(r'^(one|two|three|four|five|six|seven|eight|nine|ten)\s(additional|cycle(s|))$', time_expression)\
            or (re.search(r'^(?!(19\d{2}).)*$', time_expression) and re.search(r'^1\d{3}$', time_expression))\
            or re.search(r'^\d{1,3}\s(fractions|units|tablets)$',time_expression)\
            or re.search(r'^(a\stotal\sof|(A|a)ll)',time_expression)\
            or re.search(r'^\d{1,3}$',time_expression)\
            or re.search(r'^\d{1,4}\smg$',time_expression)\
            or re.search(r'^times\s[a-zA-Z]{3,10}$', time_expression):
                ptype = 'QUANTIFIER'
                types.append(time_expression)
                types.append(ptype)

            for h in regexpTIME:
                if re.search(h, leftwindow + rightwindow, re.IGNORECASE)\
                or re.search(r'^(at|)(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,2}:\d{1,2})(\s|)(AM|PM|)$', time_expression)\
                or re.search(r'^at\s\d{1,2}or\d{1,2}:\d{1,2}$', time_expression)\
                or re.search(r'^\d{1,2}-[a-zA-Z]{3,5}-\d{4}\s\d{1,2}:\d{1,2}:\d{1,2}$', time_expression)\
                or (re.search(r'^((?!(last)).)*$', time_expression) and re.search(r'a\.m|p\.m', time_expression))\
                or re.search(r'^(the\s|)time\sof', time_expression)\
                or re.search(r'^((T|t)ime|TIME|the\sday|night|evening|the\smorning|(O|o)vernight|(later|earlier)\s(this\safternoon|today))$', time_expression):
                    ptype = 'TIME'
                    types.append(time_expression)
                    types.append(ptype)

                for h in regexpPREPOSTEXP:
                    if re.search(h, leftwindow + rightwindow, re.IGNORECASE)\
                    or re.search(r'^((immediate\s|)((P|p)ostoperative(ly|)|POST-OP|(I|i)ntra-op|(I|i)nterop|(P|p)reop|(P|p)ostsurgical|(P|p)ost|(P|p)ost-radiation|(P|p)ost-XRT|(P|p)ost(-|)op|(P|p)erioperative(ly|)|(I|i)nteroperative|(P|p)ost-operative(ly|)|(P|p)ost\spreoperative|(P|p)re(-|)operative(ly|)|periprocedural)(\speriod|))$',time_expression)\
                    or re.search(r'^((I|i)ntraop|(P|p)ost(-op|))',time_expression):
                        ptype = 'PREPOSTEXP'
                        types.append(time_expression)
                        types.append(ptype)

                    for h in regexpDURATION:
                        if re.search(h, leftwindow + rightwindow, re.IGNORECASE)\
                        or re.search(r'the\slast|amount\sof\stime', time_expression)\
                        or re.search(r'^((D|d)uration|day|over\stime|the\sinterim|during|short\stime)$', time_expression)\
                        or re.search(r'^(\d{1}(am|pm)-\d{1}(am|pm))$', time_expression)\
                        or re.search(r'^(((F|f)or(\stotal\sof|))|at\sleast|(in|)approximately|past|the\spast|about|the\snext|)\s(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2}|an|a)(-|\s)(minute|hour|day|week|month|year)(s|)$', time_expression)\
                        or re.search(r'^(at\sleast\s|the\sfirst\s|from\s|(A|a)pproximately\s|between\s|)(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})(-|\s)(or|to)\s(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})(-|\s)(second|minute|hour|day|week|month|year)(s|)(time|)$', time_expression)\
                        or re.search(r'^(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})(-|\s)(minute|hour|day|week|month|year|mth)(s|)$', time_expression)\
                        or re.search(r'^\d{1,2}-\d{1,2}/\d{1,2}\s(minute|hour|day|week|month|year)(s|)$', time_expression)\
                        or re.search(r'^(one|two|three|four|five|six|seven|eight|nine|ten)\sand\s(one|two|three|four|five|six|seven|eight|nine|ten)-half-(minute|hour|day|week|month|year)(s|)$', time_expression)\
                        or re.search(r'^(a\scouple\sof|(S|s)ince|(H|h)ome)', time_expression)\
                        or re.search(r'^[a-zA-Z]{3,10}\sto\s[a-zA-Z]{3,10}\sof\s\d{4}$', time_expression)\
                        or re.search(r'^(\d{1,2}\s(-|to)\s\d{1,2}\s(minute|hour|day|week|month|year)(s|)(out|))$', time_expression)\
                        or (re.search(r'^((?!(ago)).)*$', time_expression) and re.search(r'^a\sfew\s(minute|hour|day|week|month|year)(s|)', time_expression))\
                        or (re.search(r'^((?!(ago|every|times|later)).)*$', time_expression) and re.search(r'several\s', time_expression))\
                        or (re.search(r'^((?!(ago|every|another|in|earlier|prior)).)*$', time_expression) and re.search(r'\ssix-months', time_expression))\
                        or (re.search(r'^((?!(mg|gm|pounds)).)*$', time_expression) and re.search(r'^((M|m)ore\sthan|(G|g)reater|(L|l)ess\sthan)', time_expression))\
                        or (re.search(r'^((?!((immediate\s|)((P|p)ostoperative(ly|)|POST-OP|(I|i)ntra-op|(I|i)nterop|(P|p)reop|(P|p)ostsurgical|(P|p)ost|(P|p)ost-radiation|(P|p)ost-XRT|(P|p)ost(-|)op|(P|p)erioperative(ly|)|(I|i)nteroperative|(P|p)ost-operative(ly|)|(P|p)ost\spreoperative|(P|p)re(-|)operative(ly|)|periprocedural)(\speriod|))).)*$', time_expression) and re.search(r'period', time_expression)):
                            ptype = 'DURATION'
                            types.append(time_expression)
                            types.append(ptype)

        if ptype == 'DATE':
            types.append(time_expression)
            types.append(ptype)

    # r.write(types[0] + '\t' + types[1] + '\n')
    return types