import pandas as pd
import pandas_datareader.data as web
from datetime import datetime, timedelta
import sqlite3


def get_data(ticker, market, start, end, conn):
    
    df = web.DataReader(ticker, 'yahoo', start, end)
    df.columns = [column.lower() for column in df.columns]
    df.reset_index(inplace = True)
    df.rename(columns = {"adj close": "adjusted", "Date":"date"}, inplace = True)
    df["ticker"] = ticker
    df["market"] = market
    df = df.loc[:,["ticker", 'market', 'date', 'high', 'low', 'open', 'close', 'adjusted', 'volume']]
    
    
    df.to_sql("stocks", conn, if_exists='append', index = False)


def update_data():

    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()
    c.execute("DROP TABLE stocks")
    c.execute("""CREATE TABLE stocks (indx INTEGER PRIMARY KEY, 
                                    ticker TEXT,
                                    market TEXT,
                                    date DATE, 
                                    high REAL, 
                                    low REAL, 
                                    open REAL,
                                    close REAL,
                                    adjusted REAL,
                                    volume REAL 
                                     
                                    ) """)
    conn.commit()

    etoro_stocks = pd.read_excel("etoro_stocks.xlsx")
    
    start = datetime(2010, 1, 1)
    end = datetime.today() - timedelta(1)

    for index, row in etoro_stocks.iterrows():
        ticker = row["Ticker"] 
        market = row["Market"]
        
        try:
            print(ticker)
            get_data(ticker, market, start, end, conn)
        except:
            print("ERROR", ticker)
            pass

update_data()