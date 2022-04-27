import pandas as pd
import statistics as stats
import numpy as np


def get_data_csv(filename):
    df = pd.read_csv(filename, index_col="Date")
    df.sort_index(ascending=True, inplace=True)
    return df


def get_spread(filename, stock_a, stock_b):
    df = get_data_csv(filename)
    df["t_price_A"] = (df[stock_a + "_High"] + df[stock_a + "_Low"] + df[stock_a + "_Close"]) / 3
    df["t_price_B"] = (df[stock_b + "_High"] + df[stock_b + "_Low"] + df[stock_b + "_Close"]) / 3
    df["spread"] = df["t_price_A"] - df["t_price_B"]
    return df


def get_bolling_band(filename, n, k, stock_a, stock_b):
    df = get_spread(filename, stock_a, stock_b)
    history = []
    upper_band = []
    lower_band = []
    spreads = df["spread"]
    series = df[[stock_a + "_Open", stock_b + "_Open", "spread"]]
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


def get_full_signal(filename, n, k, stock_a, stock_b):
    df = get_bolling_band(filename, n, k, stock_a, stock_b)
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


def get_table(filename, n, k, stock_a, stock_b, size_a, size_b, trip,
              lmt_price_a, lmt_status_a, lmt_price_b, lmt_status_b):
    df = get_full_signal(filename, n, k, stock_a, stock_b)
    df = df.reset_index()
    series = df[["Date", stockA + "_Open", stockB + "_Open"]]
    signal = df["signal"]
    series = series.drop(series.index[-1]).reset_index(drop=True)
    signal = signal.drop(signal.index[0]).reset_index(drop=True)
    temp = pd.DataFrame(series)
    temp = temp.assign(signal=pd.Series(signal, index=temp.index))
    entry = temp.loc[temp["signal"] != "false"]
    entry.set_index("Date", inplace=True, drop=True)

    entry = entry.sort_index(ascending=True)

    columns = ["DATE", "SYMBOL1", "ACTION", "SIZE", "PRICE", "TRIP", "LMT_PRICE", "STATUS",
               "SYMBOL2", "ACTION2", "SIZE2", "PRICE2", "TRIP2", "LMT_PRICE2", "STATUS2"]
    file = pd.DataFrame(columns=columns)

    position = 0
    for i in range(len(entry)):
        # up: buy ko, sell pepsi (buy B (low), sell A (high))
        if position == 0 and signal[i] == "x_up":
            position = 1
            file = pd.concat(
                [file, pd.DataFrame(
                    {
                        "DATE": [entry.index[i]],
                        "SYMBOL1": [stock_a],
                        "ACTION": ['SELL'],
                        "SIZE": [size_a],
                        "PRICE": [entry.iloc[i][stock_a+"_Open"]],
                        "TRIP": [trip],
                        "LMT_PRICE": [lmt_price_a],
                        "STATUS": [lmt_status_a],
                        "SYMBOL2": [stock_b],
                        "ACTION2": ['BUY'],
                        "SIZE2": [size_b],
                        "PRICE2": [entry.iloc[i][stock_b + "_Open"]],
                        "TRIP2": [trip],
                        "LMT_PRICE2": [lmt_price_b],
                        "STATUS2": [lmt_status_b],
                    }
                )]
            )
        # down: buy pepsi, sell ko (buy high, sell low)
        elif position == 1 and signal[i] == "x_down":
            position = 0
            file = pd.concat(
                [file, pd.DataFrame(
                    {
                        "DATE": [entry.index[i]],
                        "SYMBOL1": [stock_a],
                        "ACTION": ['BUY'],
                        "SIZE": [size_a],
                        "PRICE": [entry.iloc[i][stock_a+"_Open"]],
                        "TRIP": [trip],
                        "LMT_PRICE": [lmt_price_a],
                        "STATUS": [lmt_status_a],
                        "SYMBOL2": [stock_b],
                        "ACTION2": ['SELL'],
                        "SIZE2": [size_b],
                        "PRICE2": [entry.iloc[i][stock_b + "_Open"]],
                        "TRIP2": [trip],
                        "LMT_PRICE2": [lmt_price_b],
                        "STATUS2": [lmt_status_b],
                    }
                )]
            )
    file = file.set_index("DATE")
    file.to_csv("action.csv")


if __name__ == "__main__":
    file_name = "pep_ko_ivv.csv"
    stockA = "pep"
    stockB = "ko"

    #  parameters:
    sizeA = 1000
    sizeB = 1000
    moving_average_num = 7
    std_level = 0.5   # when: try k = 2, only x_up signal => means only 1 entry  => so we need to set exit
                      # when: k > 2.1, no signal
    lmt_priceA = 'N/A'
    lmt_statusA = 'Filled'
    lmt_priceB = 'N/A'
    lmt_statusB = 'Filled'

    # data & table
    # all_data = get_full_signal(file_name, moving_average_num, std_level, stockA, stockB)
    get_table(file_name, moving_average_num, std_level, stockA, stockB, sizeA, sizeB, "Entry",
              lmt_priceA, lmt_statusA, lmt_priceB, lmt_statusB)


