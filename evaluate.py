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
    X_train_valid, X_train = train_test_split_no_unseen(pdata, test_size=0.7)
    X_test, X_valid = train_test_split_no_unseen(X_train_valid, test_size=0.5, allow_duplication=True)
    X = {'train': X_train,
         'valid': X_valid,
         'test': X_test}
with open(args.word_filter) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values.squeeze()

filter_triples = np.concatenate((X['train'], X['valid'], X['test']))
model = ComplEx(batches_count=10, seed=0, epochs=100, k=150, eta=1,
                loss='nll', optimizer='adam')

model.fit(np.concatenate((X['train'], X['valid'])))
# Let's not do early stopping
# , True, {
#     'x_valid': X['valid'][::2],
#     'criteria': 'mrr',
#     'x_filter': filter_triples,
#     'corruption_entities': pdata,
#     'stop_interval': 4,
#     'burn_in': 0,
#     'check_interval': 50
# })

if not hasattr(model, 'early_stopping_epoch') or model.early_stopping_epoch is None:
    early_stopping_epoch = np.nan
else:
    early_stopping_epoch = model.early_stopping_epoch

ranks = evaluate_performance(X['test'][:2000], model=model,
                             filter_triples=filter_triples,
                             filter_unseen=True,
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
