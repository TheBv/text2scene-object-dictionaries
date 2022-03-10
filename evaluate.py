import numpy as np
from ampligraph.latent_features import ComplEx
from ampligraph.evaluation import evaluate_performance, mrr_score, hits_at_n_score, \
    train_test_split_no_unseen
from ampligraph.evaluation.metrics import mr_score
from io import StringIO
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="Evaluate a given graph database")
parser.add_argument('-relations', help="Specify the file location of the various relations "
                                       "between nodes", required=True,
                    metavar="RPATH")
parser.add_argument('-word-filter', help="Specify the nodes/words that should be masked over for "
                                         "evaluation", required=True, metavar="FPATH",
                    dest="word_filter",)
args = parser.parse_args()

with open(args.relations) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values
    X_train_valid, X_test = train_test_split_no_unseen(pdata, test_size=2)
    X_train, X_valid = train_test_split_no_unseen(pdata, test_size=2)
    X = {'train': X_train,
         'valid': X_valid,
         'test': X_test}
with open(args.word_filter) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values.squeeze()

filter_triples = np.concatenate((X['train'], X['valid'], X['test']))
model = ComplEx(batches_count=10, seed=0, epochs=100, k=150, eta=1,
                loss='nll', optimizer='adam')

model.fit(X['train'], True, {
    'x_valid': X['valid'][::2],
    'criteria': 'mrr',
    'x_filter': filter_triples,
    'corruption_entities': pdata,
    'stop_interval': 4,
    'burn_in': 0,
    'check_interval': 50
})

if not hasattr(model, 'early_stopping_epoch') or model.early_stopping_epoch is None:
    early_stopping_epoch = np.nan
else:
    early_stopping_epoch = model.early_stopping_epoch

ranks = evaluate_performance(X['test'], model=model,
                             filter_triples=filter_triples,
                             filter_unseen=False,
                             entities_subset=pdata,
                             use_default_protocol=True)
mr = mr_score(ranks)
mrr = mrr_score(ranks)
hits_1 = hits_at_n_score(ranks, n=1)
hits_3 = hits_at_n_score(ranks, n=3)
hits_10 = hits_at_n_score(ranks, n=10)

print({
    "mr": mr,
    "mrr": mrr,
    "H@1": hits_1,
    "H@3": hits_3,
    "H@10": hits_10,
    "early_stopping_epoch": early_stopping_epoch
})

# (batches_count=10, seed=0, epochs=100, k=150, eta=1,
#                 loss='nll', optimizer='adam')
# only bert
# {'mr': 180.5, 'mrr': 0.15106909022350198, 'H@1': 0.0, 'H@3': 0.25, 'H@10': 0.25, 'early_stopping_epoch': nan}
# all
# {'mr': 7276.0, 'mrr': 0.12708368688411456, 'H@1': 0.0, 'H@3': 0.25, 'H@10': 0.25, 'early_stopping_epoch': nan}
# no bert
# {'mr': 3851.75, 'mrr': 0.0684221944602932, 'H@1': 0.0, 'H@3': 0.0, 'H@10': 0.25, 'early_stopping_epoch': nan}


# s+o
# All relations
# 0.13571428571428573
# 0.5
# Just bert
# 0.0029832745209006067
# 0.0
# All without bert
# 0.5000475646879756
# 0.5

# s,o
# Just bert
# 0.08324855568026589
# 0.5
# No bert
# 0.5139127097559684
# 0.75
# All relations
# 0.45535714285714285
# 1.0

# o
# All relations
# 0.75
# 1.0
# no bert
# 0.5277777777777778
# 1.0
# Just bert
# 0.16346153846153846
# 1.0

# root_words_objects
# o
# Just Bert
# 0.25
# 1.0
# Everything
# 1.0
# 1.0
# No Bert
# 0.75
# 1.0

# s,o
# Everything
# 0.625
# 1.0
# Merge all relations into RootWords

# WITH "Match path = (o:RootWord)-[r]->(k:RootWord) return id(o) as word1, type(r) as Relation, id(k) as word2" AS query
# CALL apoc.export.csv.query(query, "bert_relations.csv", {})
# YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
# RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data;


# MATCH (o:RootWordObject)-[r]-()
# MATCH    (n:Object)
# MATCH  (n)-[r2]-(tgt)
# UNWIND r2 as relaties
# CALL apoc.merge.relationship(o,type(relaties),{properties:"combine"},{},tgt)
# Yield rel return count(rel)
