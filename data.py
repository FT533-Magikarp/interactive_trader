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
    series = df[[stockA + "_Open", stockB + "_Open", "spread"]]
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


def get_signal(df):
    signal = []
    df.sort_index(ascending=False, inplace=True)
    spread = df["spread"]
    upper_band = df["upper_band"]
    lower_band = df["lower_band"]
    for i in range(len(df) - 1):
        if spread[i] > upper_band[i] and spread[i + 1] <= upper_band[i + 1]:
            signal.append("x_up")
        elif spread[i] < lower_band[i] and spread[i + 1] >= upper_band[i + 1]:
            signal.append("x_down")
        else:
            signal.append("false")
    df = df.drop(df.index[-1])
    df = df.assign(signal=pd.Series(signal, index=df.index))
    return df


stockA = "pep"
stockB = "ko"

data_after_cal = get_data_csv("pep_ko_ivv.csv", stockA, stockB)

bolling_data = get_bolling_band(data_after_cal, 7, 2, stockA, stockB)

signal_data = get_signal(bolling_data)

series1 = signal_data.loc[signal_data["signal"] != "false"]

length = len(series1)

file = pd.read_csv("Action.csv")

for i in range(len(series1)):
    if series1.iloc[length - 1 - i]['signal'] == 'x_up':
        file = pd.concat(
            [file, pd.DataFrame({
                "DATE": [series1.index[length - 1 - i]],
                "SYMBOL1": ['PEP'],
                "ACTION": ['SELL'],
                "SIZE": ['1000'],
                "PRICE": [series1.iloc[length - 1 - i]['pep_Open']],
                "TRIP": ['Entry'],
                "LMT_PRICE": ['N/A'],
                "STATUS": ['Filled'],

                "SYMBOL2": ['KO'],
                "ACTION2": ['BUY'],
                "SIZE2": ['1000'],
                "PRICE2": [series1.iloc[length - 1 - i]['ko_Open']],
                "TRIP2": ['Entry'],
                "LMT_PRICE2": ['N/A'],
                "STATUS2": ['Filled'],
            })])
    elif series1.iloc[length - 1 - i]['signal'] == 'x_down':
        file = pd.concat(
            [file, pd.DataFrame({
                "DATE": [series1.index[length - 1 - i]],
                "SYMBOL1": ['PEP'],
                "ACTION": ['BUY'],
                "SIZE": ['1000'],
                "PRICE": [series1.iloc[length - 1 - i]['pep_Open']],
                "TRIP": ['Entry'],
                "LMT_PRICE": ['N/A'],
                "STATUS": ['Filled'],

                "SYMBOL2": ['KO'],
                "ACTION2": ['SELL'],
                "SIZE2": ['1000'],
                "PRICE2": [series1.iloc[length - 1 - i]['ko_Open']],
                "TRIP2": ['Entry'],
                "LMT_PRICE2": ['N/A'],
                "STATUS2": ['Filled'],
            })])

file.to_csv("Action2.csv")

# print(series1.index[0])
print(file)
