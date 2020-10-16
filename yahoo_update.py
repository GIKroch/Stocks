import pandas as pd
import requests
import sqlite3
from lxml import html, etree
import time
from datetime import datetime, timedelta 

def convert_date (x):
    
    try:
        date = pd.to_datetime(x)
    
    except:
        date = None
        
    return date


def get_yahoo_data(ticker, market, first_date_to_get, today, conn):

    # Loading request data for specific ticker
    request = "https://finance.yahoo.com/quote/{}/history?p={}".format(ticker, ticker)
    response = requests.get(request)

    # Converting to html table format and reading into pandas dataframe
    doc = html.fromstring(response.content)
    table = doc.xpath("//table")
    table_tree = etree.tostring(table[0], method='xml')
    df = pd.read_html(table_tree)[0]
    
    # Manipulation on data and columns order to obtain a desired format
    df["Date"] = df["Date"].apply(lambda x: convert_date(x))
    df.dropna(inplace = True)
    df = df.loc[df["Open"].str.contains("Dividend") == False].copy()
    df.reset_index(inplace = True, drop = True)
    df.columns = ['date', 'open', 'high', 'low', 'close', 'adjusted', 'volume']
    df['ticker'] = ticker
    df['market'] = market
    df = df.loc[:,["ticker", "market", 'date', 'open', 'high', 'low', 'close', 'adjusted', 'volume']]
    df = df.loc[(df["date"] >= first_date_to_get) & (df['date'] < today)]
    
    return df

def yahoo_update():
    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()

    max_date_available = list(c.execute("SELECT MAX(Date) FROM stocks"))[0][0]
    max_date_available = datetime.strptime(max_date_available, "%Y-%m-%d %H:%M:%S" )

    first_date_to_get = max_date_available + timedelta(1)

    today = datetime.today() 
    today = datetime(today.year, today.month, today.day, 0, 0)

    business_dates = list(pd.bdate_range(first_date_to_get,today))

    if today != first_date_to_get:
        business_dates = list(pd.bdate_range(first_date_to_get,today))
        
        ## If today's date is in the list we have to drop it. It may happen when there is a weekend in between: 
        
        if today.date() in [ts.date() for ts in business_dates]:
            
        ## Dropping the last element
            business_dates.pop()
        
        ## Now we have a final list with business days for which data should be gathered
        
        ## Loading ticker, market pairs to iterate through
        ticker_market_list = list(c.execute("SELECT DISTINCT ticker, market FROM stocks"))
        
        for ticker, market in ticker_market_list:
            
            try:
                print(ticker, market)
                df = get_yahoo_data(ticker, market, first_date_to_get, today, conn)
                df.copy().to_sql("stocks", conn, if_exists = 'append', index = False)
                time.sleep(1)
            except Exception as e:
                print(e)
                pass
            
start = time.time()
yahoo_update()
end = time.time()


print("Update took ", (end - start)/60, "minutes")