import numpy as np
from ampligraph.latent_features import ComplEx
from ampligraph.evaluation import train_test_split_no_unseen, select_best_model_ranking
from io import StringIO
import pandas as pd
import argparse
from best_model_params import param_grid
"""
Script to find a possible optimal model for a rela
"""
parser = argparse.ArgumentParser(description="Evaluate a given graph database")
parser.add_argument('-relations', help="Specify the file location of the various relations "
                                       "between nodes", required=True,
                    metavar="RPATH")
parser.add_argument('-word-filter', help="Specify the nodes/words that should be masked over for "
                                         "evaluation", required=True, metavar="FPATH",
                    dest="word_filter")
parser.add_argument('-max-combinations', help="Specifies the maximum amount of combinations of "
                                              "different model parameters that should be tried",
                    required=True, type=int, dest="max_combinations", metavar="AMOUNT")
parser.add_argument('-early-stopping', help="Should early stopping be used", metavar="ESTOP",
                    type=bool, required=False, dest='early_stopping', default=False)
parser.add_argument('-v', help="Verbose output for evaluation", required=False,
                    metavar="VERBOSE", dest="verbose", default=False, type=bool)
args = parser.parse_args()

with open(args.relations) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values
    X_train_valid, X_train = train_test_split_no_unseen(pdata, test_size=0.7)
    X_valid, X_test = train_test_split_no_unseen(X_train_valid, test_size=0.5,
                                                 allow_duplication=True)
    X = {'train': X_train,
         'valid': X_valid,
         'test': X_test}

with open(args.word_filter) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values.squeeze()

filter_triples = np.concatenate((X['train'], X['valid'], X['test']))

early_stopping_params = {
    'x_valid': X['valid'][::20],
    'criteria': 'mrr',
    'x_filter': filter_triples,
    'corruption_entities': pdata,
    'stop_interval': 4,
    'burn_in': 0,
    'check_interval': 50
}

if args.early_stopping:
    best_model, best_params, best_mrr_train, ranks_test, test_evaluation = \
        select_best_model_ranking(ComplEx, X['train'], X['valid'][::20], X['test'][:2000],
                                  param_grid,
                                  max_combinations=args.max_combinations,
                                  entities_subset=pdata,
                                  use_filter=True,
                                  verbose=args.verbose,
                                  early_stopping=True,
                                  early_stopping_params=early_stopping_params)
else:
    best_model, best_params, best_mrr_train, ranks_test, test_evaluation = \
        select_best_model_ranking(ComplEx, X['train'], X['valid'][::20], X['test'][:2000],
                                  param_grid,
                                  max_combinations=args.max_combinations,
                                  entities_subset=pdata,
                                  use_filter=True,
                                  verbose=args.verbose)

print({
    "bestModel": best_model,
    "bestParams": best_params,
    "bestMRR": best_mrr_train,
    "ranksTest": ranks_test,
    "testEval": test_evaluation,
})

