import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize


def to_df_func(X, cols):
    return pd.DataFrame(X, columns=cols)


def str_to_int_func(X):
    return X.apply(pd.to_numeric, errors="coerce")


def winsorize_array(X, limits=(0.01, 0.01)):
    X = np.asarray(X, dtype=float)
    out = np.empty_like(X)
    for j in range(X.shape[1]):
        col = X[:, j]
        out[:, j] = winsorize(col, limits=limits).data
    return out
