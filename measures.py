import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


# conn = sqlite3.connect("stocks.db")

def create_data(time_range, conn):
    
    ## The assumption is we only take data from last 3 months
    bottom_date = datetime.today() - timedelta(time_range)

    ## Converting to desired format
    bottom_date = bottom_date.strftime(format = "%Y-%m-%d 00:00:00")
    bottom_date = "'" + bottom_date + "'"
    df = pd.read_sql_query("SELECT ticker, date, adjusted FROM stocks WHERE date >= {}".format(bottom_date), conn)
    ## Sorting values to have correct stocks for specific ticker grouped in one cluster
    df = df.sort_values(["ticker", 'date'])

    ## Calculating measures for each ticker separately

    ## Pct change
    df['pct_change'] = df.groupby('ticker')['adjusted'].apply(lambda x: x.pct_change(1))

    ## Moving averages
    df['ma8'] = df.groupby('ticker')['adjusted'].apply(lambda x: x.rolling(8).mean())
    df['ma21'] = df.groupby('ticker')['adjusted'].apply(lambda x: x.rolling(21).mean())

    ## Change in moving averages
    df['ma8_pct_change'] = df.groupby('ticker')['ma8'].apply(lambda x: x.pct_change(1))
    df['ma21_pct_change'] = df.groupby('ticker')['ma21'].apply(lambda x: x.pct_change(1))
    return df

def buy_sell_ma_rule(df, buy_sell):
    
    ## Buy when both ma8 and ma21 change their trend to positive, start rising
    if buy_sell == "BUY":

        buy = df.groupby('ticker').apply(lambda x: np.where(
            (x['ma8_pct_change'] > 0) & (x['ma8_pct_change'].shift(1) < 0) & (x['ma21_pct_change'] > 0) & (x['ma21_pct_change'].shift(1) < 0), 
            "YES", 
            "NO"))

        buy = buy.to_list()
        buy = [x for y in buy for x in y]

        df['buy'] = buy

        return df.loc[(df['buy'] == 'YES') & (df['date'] == df['date'].max())]

    else:

    ## Sell when both ma8 and ma21 change their trend to negative, start plummeting
        sell = df.groupby('ticker').apply(lambda x: np.where(
        (x['ma8_pct_change'] < 0) & (x['ma8_pct_change'].shift(1) > 0) & (x['ma21_pct_change'] < 0) & (x['ma21_pct_change'].shift(1) > 0), 
        "YES", 
        "NO"))

        sell = sell.to_list()
        sell = [x for y in sell for x in y]

        df['sell'] = sell

        return df.loc[(df['sell'] == 'YES') & (df['date'] == df['date'].max())]
    

def lowest_price_in_ndays(df, ndays):

    tickers_with_lowest_price = []
    for ticker in df['ticker'].unique():
        
        df_ticker = df.loc[df['ticker'] == ticker].copy()
        dates = list(df_ticker['date'].sort_values(ascending = False).unique())


        ## Getting latest change in price for the ticker.List of dates is sorted from the latest, then we get the first list element
        max_date = dates[0]

        price_change = df_ticker.loc[df_ticker['date'] == str(max_date), 'pct_change']
        price_change = price_change.values[0]
        
        trend_change = True
        
        if price_change < 0: 

            trend_change = False

            for nday in range(1, ndays + 1):   

                prev_date = dates[nday]
                price_change_nday = df_ticker.loc[df_ticker['date'] == prev_date, 'pct_change']
                price_change_nday = price_change_nday.values[0]

                if price_change_nday > 0:
                    trend_change = True

                    break


        if trend_change == False:
            tickers_with_lowest_price.append(ticker)

        else:
            continue
            
    
    df_to_return = df.loc[(df['ticker'].isin(tickers_with_lowest_price)) & (df['date'].isin(dates[0:ndays + 1]))].sort_values(by = ['ticker', 'date'])
    return df_to_return

def first_price_increase(df, ticker, ndays):

    
    ## Getting data subset for the specific ticker
    df_ticker = df.loc[df['ticker'] == ticker].copy()


    ## Creating list of dates available for ticker

    dates = list(df_ticker['date'].sort_values(ascending = False).unique())

    ## Getting latest change in price for the ticker.List of dates is sorted from the latest, then we get the first list element
    max_date = dates[0]


    price_change = df_ticker.loc[df_ticker['date'] == str(max_date), 'pct_change']
    price_change = price_change.values[0]

    ## If price change is positive we start backwards itteration, otherwise we drop a case and carry on with the next ticker
    ## Number of days we want to check backwards - ndays

    if price_change > 0:
        
        trend_change = True
        
        for nday in range(1, ndays + 1):   
            
            prev_date = dates[nday]
            price_change_nday = df_ticker.loc[df_ticker['date'] == prev_date, 'pct_change']
            price_change_nday = price_change_nday.values[0]

            if price_change_nday > 0:
                trend_change = False
                break
                
            
        if trend_change is True:
            return ticker
        else:
            return None
        
    else:
        return None

def first_price_increase_all(df, tickers_trend_change):

    for ticker in df['ticker'].unique():
        ticker = first_price_increase(df, ticker, 4)
    
        if ticker is not None:
            tickers_trend_change.append(ticker)

    return tickers_trend_change


def biggest_price_change_in_ndays(df, ndays):

    data_to_return = []
    for ticker in df['ticker'].unique():
        
        try:
            df_ticker = df.loc[df['ticker'] == ticker].copy()
            dates = list(df_ticker['date'].sort_values(ascending = False).unique())

            ## Getting latest change in price for the ticker.List of dates is sorted from the latest, then we get the first list element
            most_recent_date = dates[0]
            historical_date = dates[ndays]

            most_recent_price = df_ticker.loc[df_ticker['date'] == str(most_recent_date), 'adjusted']
            most_recent_price = most_recent_price.values[0]

            historical_price = df_ticker.loc[df_ticker['date'] == str(historical_date), 'adjusted']
            historical_price = historical_price.values[0]

            price_change = (most_recent_price/historical_price - 1) * 100


            data_to_return.append([ticker, most_recent_date, most_recent_price, historical_price, price_change])
            
        except:
            continue
        
    
    df_to_return = pd.DataFrame(data_to_return, columns = ['ticker', 'most_recent_date', 'most_recent_price', 'historical_price', 'price_change'])
    df_to_return.sort_values('price_change', inplace = True)
    
    return df_to_return