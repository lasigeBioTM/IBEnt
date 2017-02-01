# IBEnt
Framework for identifying biomedical relations

## Dependencies:
* Python 2.7 and Java 8
* Pre-processing:
    * [Genia Sentence Splitter](http://www.nactem.ac.uk/y-matsu/geniass/) (requires ruby)
    * [Python wrapper for Stanford CoreNLP](https://bitbucket.org/torotoki/corenlp-python)
* Term recognition
    * [Stanford NER 3.5.1](http://nlp.stanford.edu/software/CRF-NER.shtml)
* Relation extraction
    * [SVM-light-TK](http://disi.unitn.it/moschitti/Tree-Kernel.htm)
    * [Shallow Language Kernel](https://hlt-nlp.fbk.eu/technologies/jsre)
* requirements.txt - run `pip install -r requirements.txt`

## Configuration
After setting up the dependencies, you have to run `python src/config/config.py` to set up some values.

## Usage
To run distant supervision multi-instance learning experiments, use src/trainevaluate.py and check benchmarks/mil.sh for example.

