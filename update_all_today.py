import pandas as pd
import pandas_datareader.data as web
from datetime import datetime, timedelta
import sqlite3

## The idea is to create a few tables with measures, once the data is updated. In such a way, we avoid calculating the same measure values many times in application 
import measures


def get_data(ticker, market, industry, start, end, conn):
    
    df = web.DataReader(ticker, 'yahoo', start, end)
    df.columns = [column.lower() for column in df.columns]
    df.reset_index(inplace = True)
    df.rename(columns = {"adj close": "adjusted", "Date":"date"}, inplace = True)
    df["ticker"] = ticker
    df["market"] = market
    df["industry"] = industry
    # df = df.loc[:,["ticker", 'market', 'industry', 'date', 'high', 'low', 'open', 'close', 'adjusted', 'volume']]
    df = df.loc[:,["ticker", 'market', 'industry', 'date', 'adjusted']]
    
    
    df.to_sql("stocks", conn, if_exists='append', index = False)


def update_data_today():

    # Check for a business day
    start = datetime(2010, 1, 1)
    end = datetime.today()

    if bool(len(pd.bdate_range(end, end))) == True:

        conn = sqlite3.connect("stocks.db")
        c = conn.cursor()
        c.execute("DROP TABLE stocks")
        c.execute("""CREATE TABLE stocks (indx INTEGER PRIMARY KEY, 
                                        ticker TEXT,
                                        market TEXT,
                                        industry TEXT, 
                                        date DATE, 
                                        adjusted REAL
                                        ) """)
        conn.commit()

        etoro_stocks = pd.read_sql_query("""
        
                                        WITH etoro AS(
                                        SELECT 
                                            ticker, 
                                            market 
                                        FROM etoro_stocks
                                        ), industry AS(
                                        SELECT
                                            ticker, 
                                            gics_sector AS industry
                                        FROM 
                                            industries
                                        )
                                        SELECT
                                        etoro.ticker, 
                                        etoro.market, 
                                        industry.industry
                                        FROM 
                                        etoro
                                        LEFT JOIN
                                        industry ON etoro.ticker = industry.ticker
        """, conn)
        
        

        for index, row in etoro_stocks.iterrows():
            ticker = row["ticker"] 
            market = row["market"]
            industry = row['industry']
            
            try:
                print(ticker)
                get_data(ticker, market, industry, start, end, conn)
            except:
                print("ERROR", ticker)
                pass
    else:
        print("It's a free day")
        pass

def calculate_measures(conn):

    print("Calculate measures is running")

    df_measures = measures.create_data(90, conn)

    ## MA_BUY data
    df_measures_extracted = measures.buy_sell_ma_rule(df_measures, "BUY")
    # df_measures_extracted = df_measures_extracted.loc[:,['ticker', 'date', 'adjusted', 'pct_change']]
    df_measures_extracted.to_sql('ma_buy', conn, if_exists='replace')

    ## MA_SELL data
    df_measures_extracted = measures.buy_sell_ma_rule(df_measures, "SELL")
    # df_measures_extracted = df_measures_extracted.loc[:,['ticker', 'date', 'adjusted', 'pct_change']]
    df_measures_extracted.to_sql('ma_sell', conn, if_exists='replace')

    ## MAX_PCT_CHANGE
    df_measures_extracted = df_measures.loc[df_measures['date'] == df_measures['date'].max()].copy()
    df_measures_extracted.sort_values("pct_change", ascending = False, inplace = True)
    df_measures_extracted.to_sql('max_pct_change', conn, if_exists='replace')

    ## MIN PRICE 7 days - 7 days of constant drop
    df_measures_extracted = measures.lowest_price_in_ndays(df_measures, 7)
    df_measures_extracted.to_sql('min_price_consecutive_7', conn, if_exists='replace')

    ## MIN PRICE 4 days - 4 days of constant drop
    df_measures_extracted = measures.lowest_price_in_ndays(df_measures, 4)
    df_measures_extracted.to_sql('min_price_consecutive_4', conn, if_exists='replace')

    ## Biggest price changes between most recent date and 7 days ago
    df_price_change_14 = measures.biggest_price_change_in_ndays(df_measures, 14)
    
    df_biggest_negative_change = df_price_change_14.head(20)
    df_biggest_negative_change.to_sql('biggest_negative_change_in_14_days', conn, if_exists='replace')

    ## Biggest price changes between most recent date and 7 days ago
    df_price_change_7 = measures.biggest_price_change_in_ndays(df_measures, 7)
    
    df_biggest_negative_change = df_price_change_7.head(20)
    df_biggest_negative_change.to_sql('biggest_negative_change_in_7_days', conn, if_exists='replace')

    ## SR Last 30 days 
    df_sr_30 = measures.get_sharpe_ratio_df(df_measures, 30)
    df_sr_30.to_sql("sharpe_ratio_last_30_days", conn, if_exists = 'replace')
    
    ## SR Last 14
    df_sr_14 = measures.get_sharpe_ratio_df(df_measures, 14)
    df_sr_14.to_sql("sharpe_ratio_last_14_days", conn, if_exists = 'replace')


update_data_today()
conn = sqlite3.connect("stocks.db")
calculate_measures(conn)