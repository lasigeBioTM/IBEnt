#!/bin/sh
set -e
set -x
LOGLEVEL=${1:-WARNING}

#cd bin/stanford-corenlp-full-2015-12-09
#java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 &
#cd ../..

#python src/main.py load_corpus --goldstd coloncancer_train
python src/main.py load_corpus --goldstd coloncancer_dev
python src/main.py load_corpus --goldstd coloncancer_test
#cp data/coloncancer_train.pickle data/coloncancer_train.pickle.backup
cp data/coloncancer_dev.pickle data/lcoloncancer_dev.pickle.backup
cp data/coloncancer_test.pickle data/coloncancer_test.pickle.backup


python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event --entitytype event --log $LOGLEVEL
cp models/tempeval_train_event.ser.gz models/tempeval_train_event.ser.gz.backup

#python src/main.py test --goldstd coloncancer_dev -o pickle results/tempeval_train_dev_event --models models/tempeval_train_event --entitytype event --log $LOGLEVEL
#python src/evaluate.py evaluate coloncancer_dev --results results/tempeval_train_dev_event --models models/tempeval_train_event --entitytype event --log $LOGLEVEL

python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_event --models models/tempeval_train_event --entitytype event --log $LOGLEVEL
python src/evaluate.py evaluate coloncancer_test --results results/tempeval_train_test_event --models models/tempeval_train_event --entitytype event --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_event --models models/tempeval_train_event --entitytype event --log $LOGLEVEL


python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3 --entitytype timex3 --log $LOGLEVEL
cp models/tempeval_train_timex3.ser.gz models/tempeval_train_timex3.ser.gz.backup

#python src/main.py test --goldstd coloncancer_dev -o pickle results/tempeval_train_dev_timex3 --models models/tempeval_train_timex3 --entitytype timex3 --log $LOGLEVEL
#python src/evaluate.py evaluate coloncancer_dev --results results/tempeval_train_dev_timex3 --models models/tempeval_train_timex3 --entitytype timex3 --log $LOGLEVEL

python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3 --models models/tempeval_train_timex3 --entitytype timex3 --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_timex3 --models models/tempeval_train_timex3 --entitytype timex3 --log $LOGLEVEL