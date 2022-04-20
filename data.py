import pandas as pd
import statistics as stats
import numpy as np


def get_data_csv(filename, stockA, stockB):
    df = pd.read_csv(filename, index_col="Date")
    df.sort_index(ascending=True, inplace=True)
    df["t_price_A"] = (df[stockA + "_High"] + df[stockA + "_Low"] + df[stockA + "_Close"]) / 3
    df["t_price_B"] = (df[stockB + "_High"] + df[stockB + "_Low"] + df[stockB + "_Close"]) / 3
    df["spread"] = df["t_price_A"] - df["t_price_B"]
    return df


def get_bolling_band(df, n, k, stockA, stockB):
    history = []
    upper_band = []
    lower_band = []
    spreads = df["spread"]
    series = df[[stockA+"_Open", stockB+"_Open", "spread"]]
    for spread in spreads:
        history.append(spread)
        if len(history) > n:
            del (history[0])
        upper_band.append(stats.mean(history) + k * np.std(history))
        lower_band.append(stats.mean(history) - k * np.std(history))
    df = pd.DataFrame(series)
    df = df.assign(upper_band=pd.Series(upper_band, index=df.index))
    df = df.assign(lower_band=pd.Series(lower_band, index=df.index))
    df.drop(df.index[0:6], inplace=True)
    return df


stockA = "pep"
stockB = "ko"

data_after_cal = get_data_csv("pep_ko_ivv.csv", stockA, stockB)

bolling_data = get_bolling_band(data_after_cal, 7, 2, stockA, stockB)

print(bolling_data)
