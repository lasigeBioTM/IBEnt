#!/bin/sh
set -e
trap 'kill $(jobs -pr)' SIGINT SIGTERM EXIT

#cd bin/stanford-corenlp-full-2015-12-09
#java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 &
#cd ../..

python src/server.py &
sleep 10
python src/client.py 0