#!/bin/sh
set -x
LOGLEVEL=${1:-WARNING}

python src/main.py train_relations --goldstd coloncancer_dev --log $LOGLEVEL --models goldstandard  --pairtype temporal --kernel jsre --tag temporaldev
python src/main.py test_relations --goldstd coloncancer_test --log $LOGLEVEL --models goldstandard --pairtype temporal --kernel jsre -o pickle results/coloncancerdev_temporal_coloncancertest --tag temporaldev
python src/evaluate.py evaluate coloncancer_test --results results/coloncancerdev_temporal_coloncancertest --models jsre --pairtype tlink --log $LOGLEVEL
python src/evaluate.py anafora coloncancer_test --results results/coloncancerdev_temporal_coloncancertest --models jsre --pairtype tlink --log $LOGLEVEL