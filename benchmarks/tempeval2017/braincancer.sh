#!/bin/sh
set -e
set -x
LOGLEVEL=${1:-WARNING}


#coloncancerdev on braincancer test

#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_event.ser.gz models/tempeval_train_event.ser.gz.backup

#python src/main.py test --goldstd braincancer_test -o pickle results/tempeval_train_test_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#python src/evaluate.py evaluate braincancer_test --results results/tempeval_train_test_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_test --results results/tempeval_train_test_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL


#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_timex3.ser.gz models/tempeval_train_timex3.ser.gz.backup

#python src/main.py test --goldstd braincancer_test -o pickle results/tempeval_train_test_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
#python src/evaluate.py evaluate braincancer_test --results results/tempeval_train_test_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_test --results results/tempeval_train_test_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL


#coloncancer and braincancer train on braincancer test

#python src/main.py train --goldstd braincancer_train coloncancer_train --models models/coloncancer_braincancertrain_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd braincancer_train coloncancer_train --models models/coloncancer_braincancertrain_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite


#python src/main.py test --goldstd braincancer_test -o pickle results/tempeval_cancertrain_test_brain_event --models models/coloncancer_braincancertrain_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
python src/evaluate.py evaluate braincancer_test --results results/tempeval_cancertrain_test_brain_event --models models/coloncancer_braincancertrain_event_crfsuite --entitytype event --log $LOGLEVEL
python src/evaluate.py anafora braincancer_test --results results/tempeval_cancertrain_test_brain_event --models models/coloncancer_braincancertrain_event_crfsuite --entitytype event --log $LOGLEVEL

# event list

#python src/main.py train_matcher --goldstd braincancer_train --models models/events_list --entitytype event --log debug
#python src/main.py test_matcher --goldstd braincancer_test -o pickle results/tempeval_list_test_brain_event --models models/events_list --entitytype event --log $LOGLEVEL --crf crfsuite
#python src/evaluate.py evaluate braincancer_test --results results/tempeval_list_test_brain_event --models models/events_list --entitytype event --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_test --results results/tempeval_list_test_brain_event --models models/events_list --entitytype event --log $LOGLEVEL


#python src/main.py test --goldstd braincancer_test -o pickle results/tempeval_cancertrain_test_brain_timex3 --models models/coloncancer_braincancertrain_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
python src/evaluate.py evaluate braincancer_test --results results/tempeval_cancertrain_test_brain_timex3 --models models/coloncancer_braincancertrain_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL
python src/evaluate.py anafora braincancer_test --results results/tempeval_cancertrain_test_brain_timex3 --models models/coloncancer_braincancertrain_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL

# temporal list

#python src/main.py train_matcher --goldstd braincancer_train --models models/temporal_list --entitytype timex3 --log debug
#python src/main.py test_matcher --goldstd braincancer_test -o pickle results/tempeval_list_test_brain_timex3 --models models/temporal_list --entitytype event --log $LOGLEVEL
#python src/evaluate.py evaluate braincancer_test --results results/tempeval_list_test_brain_timex3 --models models/temporal_list --entitytype event --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_test --results results/tempeval_list_test_brain_timex3 --models models/temporal_list --entitytype event --log $LOGLEVEL



#

#coloncancer train on braincancer test

#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_event.ser.gz models/tempeval_train_event.ser.gz.backup

#python src/main.py test --goldstd braincancer_train -o pickle results/tempeval_train_train_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#python src/evaluate.py evaluate braincancer_train --results results/tempeval_train_train_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_train --rules stopwords --results results/tempeval_train_train_brain_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL


#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_timex3.ser.gz models/tempeval_train_timex3.ser.gz.backup

#python src/main.py test --goldstd braincancer_train -o pickle results/tempeval_train_train_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
#python src/evaluate.py evaluate braincancer_train --results results/tempeval_train_train_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL
#python src/evaluate.py anafora braincancer_train --results results/tempeval_train_train_brain_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL
