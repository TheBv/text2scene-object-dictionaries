import json
import numpy as np
from ampligraph.latent_features import ComplEx
from ampligraph.evaluation import evaluate_performance, mrr_score, hits_at_n_score, \
    train_test_split_no_unseen
from ampligraph.utils.model_utils import create_tensorboard_visualizations
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
                    dest="word_filter")
parser.add_argument('-model-config', help="The file that holds the model evaluation properties. If"
                                          "not specified automatically uses evaluation_params.json in the"
                                          "root dir.", required=False, metavar="MCFG",
                    dest="model_config")
parser.add_argument('-v', help="Verbose output for evaluation", required=False,
                    metavar="VERBOSE", dest="verbose", default=False, type=bool)
parser.add_argument('-tensorboard-dir', help="Dir of the embedding for tensorboard",
                    required=False, metavar="TENSDIR", dest='tensorboard_dir')
args = parser.parse_args()

with open(args.relations) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values
    X_train_valid, X_train = train_test_split_no_unseen(pdata, test_size=0.7)
    X_test, X_valid = train_test_split_no_unseen(X_train_valid, test_size=0.5,
                                                 allow_duplication=True)
    X = {'train': X_train,
         'valid': X_valid,
         'test': X_test}
with open(args.word_filter) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values.squeeze()

filter_triples = np.concatenate((X['train'], X['valid'], X['test']))

cfg_file = "evaluation_params.json"
if args.model_config is not None:
    cfg_file = args.model_config
with open(cfg_file, "r") as file:
    config = json.load(file)

model = ComplEx(**config["cfg"])

if config["early_stopping"] is False:
    model.fit(np.concatenate((X['train'], X['valid'])))
else:
    model.fit(np.concatenate((X['train'], X['valid'])), True, {
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

if args.tensorboard_dir is not None:
    create_tensorboard_visualizations(model, args.tensorboard_dir)

ranks = evaluate_performance(X['test'][:2000], model=model,
                             filter_triples=filter_triples,
                             filter_unseen=True,
                             entities_subset=pdata,
                             use_default_protocol=True,
                             verbose=args.verbose)
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
