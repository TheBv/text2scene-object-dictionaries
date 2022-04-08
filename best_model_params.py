import numpy as np

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