#!/bin/sh
set -e
set -x
LOGLEVEL=${1:-WARNING}


#python src/main.py train --goldstd coloncancer_train --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_event.ser.gz models/tempeval_train_event.ser.gz.backup

python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL --crf crfsuite
python src/evaluate.py evaluate coloncancer_test --results results/tempeval_train_test_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_event --models models/tempeval_train_event_crfsuite --entitytype event --log $LOGLEVEL


#python src/main.py train --goldstd coloncancer_train --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
#cp models/tempeval_train_timex3.ser.gz models/tempeval_train_timex3.ser.gz.backup

python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL --crf crfsuite
python src/evaluate.py evaluate coloncancer_test --results results/tempeval_train_test_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_timex3 --models models/tempeval_train_timex3_crfsuite --entitytype timex3 --log $LOGLEVEL