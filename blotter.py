import pandas as pd
import statistics as stats
import numpy as np


def onboard_historical_price_data(filename):
    # reads a csv that has a date column and returns it as a pandas DF
    df = pd.read_csv(filename, index_col="Date")
    df.sort_index(ascending=True, inplace=True)
    return df


def get_spread(hpd, stock_a, stock_b):
    # adds three new columns to a csv of date-indexed prices:
    # t_price_A: high+low+close price of stock A / 3
    # t_price_B: high+low+close price of stock B / 3
    # spread: difference between t-price of A wrt B

    hpd["t_price_A"] = (hpd[stock_a + "_High"] + hpd[stock_a + "_Low"] + hpd[
        stock_a + "_Close"]) / 3
    hpd["t_price_B"] = (hpd[stock_b + "_High"] + hpd[stock_b + "_Low"] + hpd[
        stock_b + "_Close"]) / 3
    hpd["spread"] = hpd["t_price_A"] - hpd["t_price_B"]
    return hpd


def get_bolling_band(hpd_with_spread, n, k, stock_a, stock_b):
    # Accepts the filename of a date-indexed CSV of historical prices, plus
    #   n and k, plus the symbols of two stocks A and B
    # Returns a pandas DF containing:
    # open_price_a, open_price_b, spread, upper_band, lower_band
    df = hpd_with_spread
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


def get_full_signal(hpd_with_bolling):
    # takes in the same params as above
    # returns a date-indexed pandas df, columns:
    #   pep_Open, ko_Open, pep_Close, ko_Close, spread, upper_band, lower_band, signal
    df = hpd_with_bolling
    df['signal'] = np.where((df['spread'] > df['upper_band']) & (df['spread'].shift(1) <= df['upper_band'].shift(1)), "x_up", "false")
    df['signal'] = np.where((df['spread'] < df['lower_band']) & (df['spread'].shift(1) >= df['lower_band'].shift(1)), "x_down", df['signal'])
    df = df.drop(df.index[0])
    print(df)
    return df


def calculate_entry_orders(fsignal, stock_a, stock_b, size_a, size_b,
                           trip, lmt_price_a, lmt_status_a, lmt_price_b,
                           lmt_status_b):
    # returns a blotter containing all entry orders given a set of data.
    df = fsignal
    df = df.reset_index()
    series = df[["Date", stock_a + "_Open", stock_b + "_Open"]]
    signals = df["signal"]
    series = series.drop(series.index[0]).reset_index(drop=True)
    signals = signals.drop(signals.index[-1]).reset_index(drop=True)

    temp = pd.DataFrame(series)
    temp = temp.assign(signal=pd.Series(signals, index=temp.index))
    entry = temp.loc[temp["signal"] != "false"]
    entry.set_index("Date", inplace=True, drop=True)

    entry_blotter = pd.DataFrame(columns=["DATE", "SYMBOL", "ACTION", "SIZE",
                                          "PRICE", "TRIP", "LMT_PRICE",
                                          "STATUS"])

    position = 0
    for i in range(len(entry)):
        signal = entry.iloc[i]['signal']
        trip = "Entry"
        # up: buy ko, sell pepsi (buy B (low), sell A (high))
        if ((position == 0 or position == -1) and signal == "x_up") or ((position == 0 or position == 1) and signal == "x_down"):
            # up: buy ko, sell pepsi (buy B (low), sell A (high))
            if (position == 0 or position == -1) and signal == "x_up":
                position = 1
                action_a = "SELL"
                action_b = "BUY"
            else:
                position = -1
                action_a = "BUY"
                action_b = "SELL"
            entry_blotter = pd.concat(
                [entry_blotter, pd.DataFrame(
                    {
                        "DATE": [entry.index[i]],
                        "SYMBOL": [stock_a],
                        "ACTION": [action_a],
                        "SIZE": [size_a],
                        "PRICE": [entry.iloc[i][stock_a + "_Open"]],
                        "TRIP": [trip],
                        "LMT_PRICE": [lmt_price_a],
                        "STATUS": [lmt_status_a]
                    }
                )]
            )
            entry_blotter = pd.concat(
                [entry_blotter, pd.DataFrame(
                    {
                        "DATE": [entry.index[i]],
                        "SYMBOL": [stock_b],
                        "ACTION": [action_b],
                        "SIZE": [size_b],
                        "PRICE": [entry.iloc[i][stock_b + "_Open"]],
                        "TRIP": [trip],
                        "LMT_PRICE": [lmt_price_b],
                        "STATUS": [lmt_status_b]
                    }
                )]
            )
    entry_blotter = entry_blotter.set_index("DATE")
    return entry_blotter


def calculate_exit_orders(entry_orders, historical_price_data, timeout, stoploss):
    # Accepts:
    # entry_orders: your blotter of all entry orders; i.e., the df that
    #    is returned by calculate_entry_orders().
    # historical_price_data: the date-indexed DF returned by onboard_historical_price_data
    # timeout: an integer. if an order stays open for this many periods (days),
    #   then it is closed using a market order at the end of the day. You get
    #   the CLOSE price for the fill price.
    # stoploss: a float (percentage). For example, you BOUGHT pep and put
    # out a limit order to SELL, but the price dropped and the SELL order never
    # filled. if, over the next {timeout} days, the LOW price of pep is LESS than
    # entry_price*(1-stoploss), then you know that your stoploss would ahve
    # triggered on that day, and you would have entered a market order to close
    # the position at a price of entry_price*(1-stoploss). And vice versa for
    # shorts.
    exit_orders = pd.DataFrame()
    return exit_orders


historical_price_data = onboard_historical_price_data('pep_ko_ivv.csv')
hpd_w_spread = get_spread(historical_price_data, 'pep', 'ko')
bbands = get_bolling_band(hpd_w_spread, 20, 2, 'pep', 'ko')
full_signal = get_full_signal(bbands)
entry_orders = calculate_entry_orders(full_signal, 'pep', 'ko', 1000, 1000,
                                      'Entry', 'N/A', 'N/A', 'FILLED', 'FILLED')
entry_orders.to_csv('../entry_orders.csv')

# MAGIKARP's ASSIGMENT:
# 1) write calculate_exit_orders() so that the following code works. (must have)
# 2) Make yourself a cool background, or a logo, or something with a Magikarp
# in it. I'll work that into your website :) (optional)

timeout = 20
stoploss = 0.3
exit_orders = calculate_exit_orders(entry_orders, historical_price_data, timeout, stoploss)
exit_orders.to_csv('../exit_orders.csv')

# pd.concat() exit orders and entry orders by ROW, sort by date... and that's
# your blotter. a complete record of trades you WOULD have made.
