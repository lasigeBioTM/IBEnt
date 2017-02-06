#!/bin/sh
set -e
set -x
LOGLEVEL=${1:-WARNING}

#python src/main.py annotate --goldstd coloncancer_train
#python src/main.py annotate --goldstd coloncancer_dev
#python src/main.py annotate --goldstd coloncancer_test

#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event_na_crfsuite --entitytype event --entitysubtype "N/A" --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event_aspectual_crfsuite --entitytype event --entitysubtype ASPECTUAL --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_event_evidential_crfsuite --entitytype event --entitysubtype EVIDENTIAL --log $LOGLEVEL --crf crfsuite

#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_event_na --models models/tempeval_train_event_na_crfsuite --entitytype event --entitysubtype "N/A" --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_event_aspectual --models models/tempeval_train_event_aspectual_crfsuite --entitytype event --entitysubtype ASPECTUAL --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_event_evidential --models models/tempeval_train_event_evidential_crfsuite --entitytype event --entitysubtype EVIDENTIAL --log $LOGLEVEL --crf crfsuite


#python src/classification/results.py combine coloncancer_test --entitytype event --finalmodel models/tempeval_train_event_subtypes_crfsuite \
                                                              #--results results/tempeval_train_test_event_na results/tempeval_train_test_event_aspectual results/tempeval_train_test_event_evidential \
                                                              #-o results/tempeval_train_test_event_subtypes \
                                                              #--models models/tempeval_train_event_na_crfsuite models/tempeval_train_event_aspectual_crfsuite models/tempeval_train_event_evidential_crfsuite
#python src/evaluate.py evaluate coloncancer_test --results results/tempeval_train_test_event_subtypes --models models/tempeval_train_event_subtypes_crfsuite --entitytype event --log $LOGLEVEL
#python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_event_subtypes --models models/tempeval_train_event_subtypes_crfsuite --entitytype event --log $LOGLEVEL


#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_date_crfsuite --entitytype timex3 --entitysubtype DATE --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_time_crfsuite --entitytype timex3 --entitysubtype TIME --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_duration_crfsuite --entitytype timex3 --entitysubtype DURATION --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_quantifier_crfsuite --entitytype timex3 --entitysubtype QUANTIFIER --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_prepostexp_crfsuite --entitytype timex3 --entitysubtype PREPOSTEXP --log $LOGLEVEL --crf crfsuite
#python src/main.py train --goldstd coloncancer_dev --models models/tempeval_train_timex3_set_crfsuite --entitytype timex3 --entitysubtype SET --log $LOGLEVEL --crf crfsuite

#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_date --models models/tempeval_train_timex3_date_crfsuite --entitytype timex3 --entitysubtype DATE --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_time --models models/tempeval_train_timex3_time_crfsuite --entitytype timex3 --entitysubtype TIME --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_duration --models models/tempeval_train_timex3_duration_crfsuite --entitytype timex3 --entitysubtype DURATION --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_quantifier --models models/tempeval_train_timex3_quantifier_crfsuite --entitytype timex3 --entitysubtype QUANTIFIER --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_prepostexp --models models/tempeval_train_timex3_prepostexp_crfsuite --entitytype timex3 --entitysubtype PREPOSTEXP --log $LOGLEVEL --crf crfsuite
#python src/main.py test --goldstd coloncancer_test -o pickle results/tempeval_train_test_timex3_set --models models/tempeval_train_timex3_set_crfsuite --entitytype timex3 --entitysubtype SET --log $LOGLEVEL --crf crfsuite


python src/classification/results.py combine coloncancer_test --entitytype timex3 --finalmodel models/tempeval_train_timex3_subtypes_crfsuite \
                                                              --results results/tempeval_train_test_timex3_date results/tempeval_train_test_timex3_time results/tempeval_train_test_timex3_duration results/tempeval_train_test_timex3_quantifier results/tempeval_train_test_timex3_prepostexp results/tempeval_train_test_timex3_set \
                                                              -o results/tempeval_train_test_timex3_subtypes \
                                                              --models models/tempeval_train_timex3_date_crfsuite models/tempeval_train_timex3_time_crfsuite models/tempeval_train_timex3_duration_crfsuite models/tempeval_train_timex3_quantifier_crfsuite models/tempeval_train_timex3_prepostexp_crfsuite models/tempeval_train_timex3_set_crfsuite
python src/evaluate.py evaluate coloncancer_test --results results/tempeval_train_test_timex3_subtypes --models models/tempeval_train_timex3_subtypes_crfsuite --entitytype timex3 --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/tempeval_train_test_timex3_subtypes --models models/tempeval_train_timex3_subtypes_crfsuite --entitytype timex3 --log $LOGLEVEL
