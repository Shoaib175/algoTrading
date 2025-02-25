import MetaTrader5 as mt5
import pandas as pd
import time

ACCOUNT_NUMBER = 202887015
PASSWORD = "Restricted@2799"
SERVER = "Exness-MT5Trial7"
SYMBOL = "XAUUSDm"
TIMEFRAME = mt5.TIMEFRAME_M5
BOLLINGER_PERIOD = 12
LOT_SIZE = 0.01
STD_DEV = 2


def waitForNewCandle():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)  # Get latest candle
    last_time = rates[-1]['time']

    while True:
        new_rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)  # Fetch latest again
        if new_rates[-1]['time'] != last_time:  # New candle detected

            return new_rates[-1]['close']  #returns the current close price




def get_sma(symbol, timeframe, period):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
    df = pd.DataFrame(rates)
    df['SMA'] = df['close'].rolling(window=period).mean()
    return df['SMA'].iloc[-1]

def get_upper_band(symbol, timeframe, period, std_dev):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
    df = pd.DataFrame(rates)
    df['SMA'] = df['close'].rolling(window=period).mean()
    df['STD'] = df['close'].rolling(window=period).std()
    df['Upper_Band'] = df['SMA'] + (df['STD']*std_dev)
    return df['Upper_Band'].iloc[-1]

def get_lower_band(symbol, timeframe, period, std_dev):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
    df = pd.DataFrame(rates)
    df['SMA'] = df['close'].rolling(window=period).mean()
    df['STD'] = df['close'].rolling(window=period).std()
    df['Lower_Band'] = df['SMA'] - (df['STD']*std_dev)
    return df['Lower_Band'].iloc[-1]

def get_current_price(symbol,timeframe,period):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    df = pd.DataFrame(rates)
    return df['close'].iloc[0]


def checkCurrentCandleClose():

    print("Waiting for Candle to Close...")
    curr_close = waitForNewCandle()
    upper_band, lower_band = get_bb(SYMBOL, TIMEFRAME, BOLLINGER_PERIOD)
    print (f"UpperBand :{upper_band}  LowerBand{lower_band}   CurrClose {curr_close}")
    if(curr_close>upper_band):
        print(f"Current Candle closed: {curr_close} above Upper Band: {upper_band}")
        return "SELL", True
    elif (curr_close<lower_band):
        print(f"Current Candle closed: {curr_close} below Lower Band: {lower_band}")
        return "BUY", True

    else:
        print(f"Current Candle did not close above Upper Band OR below Lower Band")
        return "NONE", False


def place_order_buy(take_profit, close):
    SPREAD = mt5.symbol_info_tick(SYMBOL).ask - mt5.symbol_info_tick(SYMBOL).bid
    order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": mt5.ORDER_TYPE_BUY,
        "tp":take_profit,
        "sl": close - (SPREAD*5),
        "price": mt5.symbol_info_tick(SYMBOL).ask,
        "deviation": 10,
        "magic": 123400,
        "comment": "Bollinger Bot BUY",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(order)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
    else:
        print("Buy Order placed")

def place_order_sell(take_profit, close):
    SPREAD = mt5.symbol_info_tick(SYMBOL).ask - mt5.symbol_info_tick(SYMBOL).bid
    order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": mt5.ORDER_TYPE_SELL,
        "tp":take_profit,
        "sl": close + (SPREAD*5),
        "price": mt5.symbol_info_tick(SYMBOL).bid,
        "deviation": 10,
        "magic": 123400,
        "comment": "Bollinger Bot SELL",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(order)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
    else:
        print("SELL Order placed")


def place_order(indicator, stop_loss, condition):

    if condition:

        if(indicator=="BUY"):
            order_type = mt5.ORDER_TYPE_BUY
        elif(indicator=="SELL"):
            order_type = mt5.ORDER_TYPE_SELL
        takeprofit = take_profit(SYMBOL, TIMEFRAME, BOLLINGER_PERIOD)

        order = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL,
            "volume": LOT_SIZE,
            "type": order_type,
            "tp":takeprofit,
            "sl": stop_loss,
            "price": mt5.symbol_info_tick(SYMBOL).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(SYMBOL).bid,
            "deviation": 10,
            "magic": 123400,
            "comment": "Bollinger Bot",
            "type_filling": mt5.ORDER_FILLING_IOC,
            }
        result = mt5.order_send(order)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.comment}")
        else:
            print("Order placed")
    else:
        return None

def calculateSL(indicator, condition):
    if condition:
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 2)
        prev_close = rates[-2]['close']
        spread = mt5.symbol_info_tick(SYMBOL).ask - mt5.symbol_info_tick(SYMBOL).bid
        if(indicator == "BUY"):
            stop_loss = prev_close - spread
            return stop_loss
        elif (indicator == "SELL"):
            stop_loss = prev_close + spread
            return stop_loss
    else:
        return None


if __name__=="__main__":
    mt5.initialize()
    print("Bot Initialized")
    mt5.login(ACCOUNT_NUMBER, PASSWORD, SERVER)
    print("Login Successful")

    while True:
        upper_band = get_upper_band(SYMBOL,TIMEFRAME, BOLLINGER_PERIOD, STD_DEV)
        lower_band = get_lower_band(SYMBOL,TIMEFRAME, BOLLINGER_PERIOD, STD_DEV)
        current_price = get_current_price(SYMBOL, TIMEFRAME, BOLLINGER_PERIOD)
        sma = get_sma(SYMBOL, TIMEFRAME, BOLLINGER_PERIOD)
        take_profit = sma

        if(current_price<lower_band):
            print("Price Went below Lower Band, waiting for candle to close....")
            close = waitForNewCandle()
            place_order_buy(take_profit, close)

        elif(current_price>upper_band):
            print("Price Went above Upper Band, waiting for candle to close....")
            close = waitForNewCandle()
            place_order_sell(take_profit, close)




