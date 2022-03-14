import numpy as np
from ampligraph.latent_features import ComplEx
from ampligraph.evaluation import train_test_split_no_unseen, select_best_model_ranking
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
parser.add_argument('-max-combinations', help="Specifies the maximum amount of combinations of "
                                              "different model parameters that should be tried",
                    required=True, type=int, dest="max_combinations", metavar="AMOUNT")
args = parser.parse_args()

with open(args.relations) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values
    X_train_valid, X_train = train_test_split_no_unseen(pdata, test_size=0.7)
    X_valid, X_test = train_test_split_no_unseen(X_train_valid, test_size=0.5, allow_duplication=True)
    X = {'train': X_train,
         'valid': X_valid,
         'test': X_test}
with open(args.word_filter) as file:
    data = file.read()
    pdata = pd.read_csv(StringIO(data), delimiter=',').values.squeeze()
# train_test_split_no_unseen(pd.read_csv('resources/csv/bert-relations.csv'))
filter_triples = np.concatenate((X['train'], X['valid'], X['test']))

param_grid = {
    "batches_count": [20, 30],
    "seed": 0,
    "epochs": [100, 150],
    "k": [50, 100],
    "eta": [5, 10, 15],
    "loss": ["pairwise", "nll"],
    "loss_params": {
        "margin": [2]
    },
    "embedding_model_params": {
    },
    "regularizer": ["LP", None],
    "regularizer_params": {
        "p": [1, 3],
        "lambda": [1e-4, 1e-5]
    },
    "optimizer": ["adagrad", "adam"],
    "optimizer_params": {
        "lr": lambda: np.random.uniform(0.0001, 0.01)
    },
    "verbose": True
}
print(select_best_model_ranking(ComplEx, X['train'], X['valid'][::20], X['test'][:2000],
                                param_grid,
                                max_combinations=args.max_combinations,
                                entities_subset=pdata,
                                use_filter=True,
                                verbose=True,
                                ))

#best_model    {'batches_count': 50, 'seed': 0, 'epochs': 100, 'k': 50, 'eta': 15, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': 'LP', 'regularizer_params': {'p': 3, 'lambda': 0.0001}, 'optimizer': 'adagrad', 'optimizer_params': {'lr': 0.0014386599167139755}, 'verbose': False},
#       0.286528018192309,
#       array([[2806,    7], [ 345,    1]]),
#        {'mrr': 0.286528018192309, 'mr': 789.75, 'hits_1': 0.25, 'hits_3': 0.25, 'hits_10': 0.5},
#        [{'model_name': 'ComplEx', 'model_params': {'batches_count': 10, 'seed': 0, 'epochs': 150, 'k': 100, 'eta': 5, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.006273280598181127}, 'verbose': False}, 'results': {'mrr': 0.1974301877708233, 'mr': 42.75, 'hits_1': 0.0, 'hits_3': 0.25, 'hits_10': 0.5}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 10, 'seed': 0, 'epochs': 100, 'k': 100, 'eta': 15, 'loss': 'pairwise', 'loss_params': {'margin': 2}, 'embedding_model_params': {}, 'regularizer': 'LP', 'regularizer_params': {'p': 1, 'lambda': 0.0001}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.00793807787701838}, 'verbose': False}, 'results': {'exception': '2 root error(s) found.\n  (0) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_22 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n\t [[add_10/_83]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n  (1) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_22 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n0 successful operations.\n0 derived errors ignored.\n\nOriginal stack trace for \'mul_22\':\n  File "/Users/Patrick/PycharmProjects/text2scene/bestModel.py", line 60, in <module>\n    early_stopping=True))\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\evaluation\\protocol.py", line 1476, in select_best_model_ranking\n    model.fit(X_train, early_stopping, early_stopping_params)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 373, in fit\n    tensorboard_logs_path=tensorboard_logs_path)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 1118, in fit\n    loss = self._get_model_loss(dataset_iterator)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 692, in _get_model_loss\n    scores_neg = self._fn(e_s_neg, e_p_neg, e_o_neg)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 263, in _fn\n    tf.reduce_sum(e_p_img * e_s_img * e_o_real, axis=1)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 899, in binary_op_wrapper\n    return func(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 1206, in _mul_dispatch\n    return gen_math_ops.mul(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\gen_math_ops.py", line 6701, in mul\n    "Mul", x=x, y=y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\op_def_library.py", line 794, in _apply_op_helper\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\util\\deprecation.py", line 507, in new_func\n    return func(*args, **kwargs)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3357, in create_op\n    attrs, op_def, compute_device)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3426, in _create_op_internal\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 1748, in __init__\n    self._traceback = tf_stack.extract_stack()\n'}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 50, 'seed': 0, 'epochs': 100, 'k': 50, 'eta': 10, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.006516901533306853}, 'verbose': False}, 'results': {'mrr': 0.06123556792178073, 'mr': 106.25, 'hits_1': 0.0, 'hits_3': 0.0, 'hits_10': 0.25}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 10, 'seed': 0, 'epochs': 150, 'k': 100, 'eta': 15, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.008011669785745563}, 'verbose': False}, 'results': {'exception': '2 root error(s) found.\n  (0) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_16 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n\t [[add_7/_91]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n  (1) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_16 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n0 successful operations.\n0 derived errors ignored.\n\nOriginal stack trace for \'mul_16\':\n  File "/Users/Patrick/PycharmProjects/text2scene/bestModel.py", line 60, in <module>\n    early_stopping=True))\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\evaluation\\protocol.py", line 1476, in select_best_model_ranking\n    model.fit(X_train, early_stopping, early_stopping_params)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 373, in fit\n    tensorboard_logs_path=tensorboard_logs_path)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 1118, in fit\n    loss = self._get_model_loss(dataset_iterator)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 692, in _get_model_loss\n    scores_neg = self._fn(e_s_neg, e_p_neg, e_o_neg)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 262, in _fn\n    tf.reduce_sum(e_p_img * e_s_real * e_o_img, axis=1) - \\\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 899, in binary_op_wrapper\n    return func(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 1206, in _mul_dispatch\n    return gen_math_ops.mul(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\gen_math_ops.py", line 6701, in mul\n    "Mul", x=x, y=y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\op_def_library.py", line 794, in _apply_op_helper\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\util\\deprecation.py", line 507, in new_func\n    return func(*args, **kwargs)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3357, in create_op\n    attrs, op_def, compute_device)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3426, in _create_op_internal\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 1748, in __init__\n    self._traceback = tf_stack.extract_stack()\n'}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 50, 'seed': 0, 'epochs': 150, 'k': 100, 'eta': 15, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': 'LP', 'regularizer_params': {'p': 3, 'lambda': 1e-05}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.00945222227879088}, 'verbose': False}, 'results': {'mrr': 0.092364442028845, 'mr': 482.75, 'hits_1': 0.0, 'hits_3': 0.25, 'hits_10': 0.25}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 50, 'seed': 0, 'epochs': 100, 'k': 50, 'eta': 15, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': 'LP', 'regularizer_params': {'p': 3, 'lambda': 0.0001}, 'optimizer': 'adagrad', 'optimizer_params': {'lr': 0.0014386599167139755}, 'verbose': False}, 'results': {'mrr': 0.286528018192309, 'mr': 789.75, 'hits_1': 0.25, 'hits_3': 0.25, 'hits_10': 0.5}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 10, 'seed': 0, 'epochs': 150, 'k': 100, 'eta': 15, 'loss': 'pairwise', 'loss_params': {'margin': 2}, 'embedding_model_params': {}, 'regularizer': 'LP', 'regularizer_params': {'p': 3, 'lambda': 1e-05}, 'optimizer': 'adagrad', 'optimizer_params': {'lr': 0.0068500209611244865}, 'verbose': False}, 'results': {'exception': '2 root error(s) found.\n  (0) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_20 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n\t [[add_10/_83]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n  (1) Resource exhausted: OOM when allocating tensor with shape[1178910,100] and type float on /job:localhost/replica:0/task:0/device:GPU:0 by allocator GPU_0_bfc\n\t [[node mul_20 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\nHint: If you want to see a list of allocated tensors when OOM happens, add report_tensor_allocations_upon_oom to RunOptions for current allocation info.\n\n0 successful operations.\n0 derived errors ignored.\n\nOriginal stack trace for \'mul_20\':\n  File "/Users/Patrick/PycharmProjects/text2scene/bestModel.py", line 60, in <module>\n    early_stopping=True))\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\evaluation\\protocol.py", line 1476, in select_best_model_ranking\n    model.fit(X_train, early_stopping, early_stopping_params)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 373, in fit\n    tensorboard_logs_path=tensorboard_logs_path)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 1118, in fit\n    loss = self._get_model_loss(dataset_iterator)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 692, in _get_model_loss\n    scores_neg = self._fn(e_s_neg, e_p_neg, e_o_neg)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 262, in _fn\n    tf.reduce_sum(e_p_img * e_s_real * e_o_img, axis=1) - \\\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 899, in binary_op_wrapper\n    return func(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\math_ops.py", line 1206, in _mul_dispatch\n    return gen_math_ops.mul(x, y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\gen_math_ops.py", line 6701, in mul\n    "Mul", x=x, y=y, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\op_def_library.py", line 794, in _apply_op_helper\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\util\\deprecation.py", line 507, in new_func\n    return func(*args, **kwargs)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3357, in create_op\n    attrs, op_def, compute_device)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3426, in _create_op_internal\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 1748, in __init__\n    self._traceback = tf_stack.extract_stack()\n'}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 10, 'seed': 0, 'epochs': 150, 'k': 50, 'eta': 10, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.006566086354399584}, 'verbose': False}, 'results': {'mrr': 0.1345300716982133, 'mr': 395.0, 'hits_1': 0.0, 'hits_3': 0.25, 'hits_10': 0.25}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 50, 'seed': 0, 'epochs': 100, 'k': 50, 'eta': 5, 'loss': 'pairwise', 'loss_params': {'margin': 2}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adam', 'optimizer_params': {'lr': 0.0004804117220800738}, 'verbose': False}, 'results': {'mrr': 0.22374282694050135, 'mr': 121.5, 'hits_1': 0.0, 'hits_3': 0.25, 'hits_10': 0.75}}, {'model_name': 'ComplEx', 'model_params': {'batches_count': 50, 'seed': 0, 'epochs': 100, 'k': 50, 'eta': 5, 'loss': 'nll', 'loss_params': {}, 'embedding_model_params': {}, 'regularizer': None, 'regularizer_params': {}, 'optimizer': 'adagrad', 'optimizer_params': {'lr': 0.0065657724221074455}, 'verbose': False}, 'results': {'exception': '2 root error(s) found.\n  (0) Invalid argument: indices[17667] = 153024 is not in [0, 16997)\n\t [[node embedding_lookup_6 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\n  (1) Invalid argument: indices[17667] = 153024 is not in [0, 16997)\n\t [[node embedding_lookup_6 (defined at \\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py:1748) ]]\n\t [[embedding_lookup_8/_195]]\n0 successful operations.\n0 derived errors ignored.\n\nOriginal stack trace for \'embedding_lookup_6\':\n  File "/Users/Patrick/PycharmProjects/text2scene/bestModel.py", line 60, in <module>\n    early_stopping=True))\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\evaluation\\protocol.py", line 1476, in select_best_model_ranking\n    model.fit(X_train, early_stopping, early_stopping_params)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\ComplEx.py", line 373, in fit\n    tensorboard_logs_path=tensorboard_logs_path)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 1129, in fit\n    self._initialize_early_stopping()\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 793, in _initialize_early_stopping\n    self._initialize_eval_graph("valid")\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 1496, in _initialize_eval_graph\n    e_s, e_p, e_o = self._lookup_embeddings(self.out_corr)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 489, in _lookup_embeddings\n    e_s = self._entity_lookup(x[:, 0])\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\ampligraph\\latent_features\\models\\EmbeddingModel.py", line 518, in _entity_lookup\n    emb = tf.nn.embedding_lookup(self.ent_emb, remapping)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\embedding_ops.py", line 317, in embedding_lookup\n    transform_fn=None)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\embedding_ops.py", line 135, in _embedding_lookup_and_transform\n    array_ops.gather(params[0], ids, name=name), ids, max_norm)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\util\\dispatch.py", line 180, in wrapper\n    return target(*args, **kwargs)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\array_ops.py", line 3956, in gather\n    params, indices, axis, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\ops\\gen_array_ops.py", line 4082, in gather_v2\n    batch_dims=batch_dims, name=name)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\op_def_library.py", line 794, in _apply_op_helper\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\util\\deprecation.py", line 507, in new_func\n    return func(*args, **kwargs)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3357, in create_op\n    attrs, op_def, compute_device)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 3426, in _create_op_internal\n    op_def=op_def)\n  File "\\Users\\Patrick\\PycharmProjects\\text2scene\\venvNew\\lib\\site-packages\\tensorflow_core\\python\\framework\\ops.py", line 1748, in __init__\n    self._traceback = tf_stack.extract_stack()\n'}}])