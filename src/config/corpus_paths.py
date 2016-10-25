chemdner_sample_base = "corpora/CHEMDNER/CHEMDNER_SAMPLE_JUNE25/"
cpatents_sample_base = "corpora/CHEMDNER-patents/chemdner_cemp_sample_v02/"
pubmed_test_base = "corpora/pubmed-test/"
transmir_base = "corpora/transmir/"

paths = {}

paths.update({
    'coloncancer_train':{
        'text': "corpora/thymedata-1.1.0/text/Train/",
        'annotations': "corpora/thymedata-1.1.0/coloncancer/Train/",
        'format': "tempeval",
        'corpus': "data/coloncancer_train.pickle"
    },
    'coloncancer_sample':{
        'text': "corpora/thymedata-1.1.0/text/sample/",
        'annotations': "corpora/thymedata-1.1.0/coloncancer/sample/",
        'format': "tempeval",
        'corpus': "data/coloncancer_sample.pickle"
    },
    'coloncancer_dev':{
            'text': "corpora/thymedata-1.1.0/text/Dev/",
            'annotations': "corpora/thymedata-1.1.0/coloncancer/Dev/",
            'format': "tempeval",
            'corpus': "data/coloncancer_dev.pickle"
        },
    'coloncancer_test': {
        'text': "corpora/thymedata-1.1.0/text/test/",
        'annotations': "corpora/thymedata-1.1.0/coloncancer/test/",
        'format': "tempeval",
        'corpus': "data/coloncancer_test.pickle"
    },
    'mirna_cf': {
        'corpus': "corpora/cf_corpus/abstracts.txt.pickle",
        'format': "mirna",
        'annotations': ""
    },
    'mirna_cf_annotated': {
        'corpus': "data/mirna_cf_annotated.pickle",
        'format': "mirna",
        'annotations': ""
    },

    'mirna_ds': {
        'corpus': "corpora/mirna-ds/abstracts_11k.txt.pickle",
        'format': "mirna",
        'annotations': ""
    },
    'mirna_ds_annotated': {
        'corpus': "corpora/mirna-ds/mirna_ds_annotated.pickle",
        'format': "mirna",
        'annotations': ""
    },

    ### TransmiR corpus
    'transmir': {
        'text': "data/transmir_v1.2.tsv",
        'annotations': "data/transmir_v1.2.tsv",
        'corpus': "data/transmir_v1.2.tsv.pickle",
        'format': "transmir"
    },
    'transmir_annotated': {
        'text': "data/transmir_v1.2.tsv",
        'annotations': "data/transmir_v1.2.tsv",
        'corpus': "data/transmir_annotated.pickle",
        'format': "transmir"
    },
    'pubmed_test': {
        'text': pubmed_test_base + "pmids_test.txt",
        'annotations': "",
        'corpus': "data/pmids_test.txt.pickle",
        'format': "pubmed"
    },

    ### BioCreative '15 CHEMDNER subtask
    'cemp_sample':{
                    'text': cpatents_sample_base + "chemdner_patents_sample_text.txt",
                    'annotations': cpatents_sample_base + "chemdner_cemp_gold_standard_sample.tsv",
                    'cem': cpatents_sample_base + "chemdner_cemp_gold_standard_sample_eval.tsv",
                    'corpus': "data/chemdner_patents_sample_text.txt.pickle",
                    'format': "chemdner",
                    },
})