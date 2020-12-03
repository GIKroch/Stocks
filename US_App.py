import sqlite3
import pandas as pd
# import pandas_datareader.data as web
import time
from datetime import datetime, timedelta, date
import plotly.offline as pyo
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import measures



###################################################################################################################################################################################################################

## Connecting to database

### Check same thread dodane, żeby pozbyć się errora - docelowo dobrze jakby tego nie było
# conn = sqlite3.connect(r"Z:\Stocks\stocks.db", check_same_thread = False)
conn = sqlite3.connect("stocks.db", check_same_thread = False)

c = conn.cursor()
## Running an update_data script - all conditions whether the data should be updated are not, are resolved in a script itself


############################################################################################################# Loading info about industries #######################################################################

################################ industries
industries = list(c.execute("SELECT DISTINCT industry FROM stocks"))
industries = [industry[0] for industry in industries]
industries.sort()
industries.insert(0, "All")

############################################################################################################# Dates ###############################################################################################

number_of_dates = len(list(c.execute("SELECT DISTINCT date FROM stocks")))
## Creating dates for date range selection
max_date = list(c.execute("SELECT  MAX(date) FROM stocks"))[0][0]
max_date = max_date.split(" ")[0]
max_date = max_date.split("-")
max_year = int(max_date[0])
max_month = int(max_date[1])
max_day = int(max_date[2])

## also, on default last 7 days will be presented, we get 
distinct_dates = list(c.execute("SELECT  DISTINCT date FROM stocks ORDER BY date DESC"))
distinct_dates = [date[0] for date in distinct_dates]

last_week_date = distinct_dates[6]
last_week_date = last_week_date.split(" ")[0]
last_week_date = last_week_date.split("-")

last_week_year = int(last_week_date[0])
last_week_month = int(last_week_date[1])
last_week_day = int(last_week_date[2])

## MAX Recent price per stock
max_price = list(c.execute("""SELECT MAX(adjusted) 
                             FROM stocks 
                             WHERE date 
                             IN (SELECT MAX(date) FROM stocks)"""))[0][0]

############################################################################################################## Dash App ########################################################################################

app = dash.Dash(__name__)
app.layout = html.Div([

                        ## Creating separeted tabs 
                        dcc.Tabs(id='tabs', value='dashboard', children=[
                            dcc.Tab(id = "project-description", label='Project Description', value='project-description'),
                            dcc.Tab(id = "dashboard", label='Dashboard', value='dashboard'),
                            
                        ]), 
                        html.Div(id='tabs_content') 
    ])

## Tab selection
@app.callback(Output('tabs_content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'dashboard':
        return html.Div([
                        html.Div([
                            dcc.Dropdown(
                            id = "Industry", 
                            options = [
                                {'label': industry, "value": industry} for industry in industries
                            ], 
                            value = "All"
                            ),  

                            dcc.RangeSlider(
                            id = 'stock_value_slider',
                            min = 0,
                            max = max_price,
                            step = 1,
                            value = [0,100]
                            ),
                        
                            html.Div(id='slider_output'), 
                    
                            dcc.Dropdown(
                            id = 'ticker'
                            )

                        ], id = 'plot_selectors1'), 
                        
                        html.Div([
                            dcc.DatePickerRange(
                            id='date_range',
                            display_format = "D/M/YYYY",
                            first_day_of_week = 1,
                            min_date_allowed=date(2010, 1, 1),
                            max_date_allowed = date(max_year, max_month, max_day) + timedelta(1),
                            start_date=date(last_week_year, last_week_month, last_week_day),
                            end_date=date(max_year, max_month, max_day) + timedelta(1)
                            )
                        ], id = 'date_range_div'),

                        dcc.Checklist(
                        id = 'plot_content',
                        options=[
                            {'label': 'MA8', 'value': 'MA8'},
                            {'label': 'MA21', 'value': 'MA21'},
                            {'label': 'Candlestick', 'value': 'Candlestick'}, 
                            {'label': 'Bollinger Bands', 'value': 'Bollinger Bands'}
                        ],
                        value = ["MA8"], 
                        labelStyle={'display': 'inline-block'}
                        ),  
                        

                        dcc.Graph(id = "stock_series"),

                        
                        html.Div([
                            dcc.Dropdown(id = 'ma_buy_sell_type', 
                            options = [
                            {'label':"BUY", "value": "BUY"}, 
                            {'label':"SELL", "value": "SELL"}
                            ],
                            value = "BUY"
                        
                            ),

                            dash_table.DataTable(
                            id='ma_buy_sell_table',
                            columns=None,
                            data=None,
                            ), 
                        ], id = 'table-left'),

                        html.Div([
                            dcc.Dropdown(id = 'ndays_measure_type', 
                                    options = [
                            {'label': 'MAX PCT CHANGE POSITIVE', 'value': 'MAX_PCT_CHANGE_POSITIVE'}, 
                            {'label': 'MAX_PCT_CHANGE_NEGATIVE', 'value': 'MAX_PCT_CHANGE_NEGATIVE'}, 
                            {'label': 'CONSTANT PRICE DROP 7 DAYS', 'value': 'CONSTANT_PRICE_DROP_7_DAYS'}, 
                            {'label': 'CONSTANT PRICE DROP 4 DAYS', 'value': 'CONSTANT_PRICE_DROP_4_DAYS'}, 
                            {'label': 'BIGGEST NEGATIVE CHANGE IN 7 DAYS', 'value': 'BIGGEST_NEGATIVE_CHANGE_IN_7_DAYS'},
                            {'label': 'BIGGEST NEGATIVE CHANGE IN 14 DAYS', 'value': 'BIGGEST_NEGATIVE_CHANGE_IN_14_DAYS'}, 
                            {'label': 'SHARPE RATIO LAST 14 DAYS DATA', 'value':'SHARPE_RATIO_LAST_14_DAYS_DATA'}, 
                            {'label': 'SHARPE RATIO LAST 30 DAYS DATA', 'value':'SHARPE_RATIO_LAST_30_DAYS_DATA'}],
                            value = "MAX_PCT_CHANGE_POSITIVE"
                            ), 

                            dash_table.DataTable(
                            id='ndays_measure_table',
                            columns=None,
                            data=None, 
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi")

                        ], id = 'table-right')
                          
        ]) 

    elif tab == 'project-description':
        return html.Div([
                dcc.Markdown('''
                            #### Welcome to my app for the technical analysis of US equities. 

                            When I graduated from my Master's in Data Science in July 2020, I instantly started thinking on how to futher develop my analytical skills. 
                            Obviously, I'm learning a lot on daily basis working as data analyst in Citi. However, there are so many things one can learn, that it would be a huge loss for me not to take up other chances.  
                            
                            To improve analytical skills one needs to get data to practice at. What would be a better source than US stocks market, with high-volume data and millions of practitioners around the world? 
                            What's exciting about the stock market is its unpredictibility. Sure, there are a lot of strategies and techniques which can help you to earn money on the market. However, you can never be sure of profits. 
                              

                            I started working on this app to suport my trading on eToro platform. To keep things simple I've focused only on NYSE and NASDAQ equities. 

                            The app has been created in Python, the packages used: 
                            * Backend:
                                * Dash - Web App Framework [Dash Home Page](https://plotly.com/dash/)
                                * Plotly - Interactive Plotting Engine [Plotly Home Page](https://plotly.com/)
                                * Sqlite3 - As Backend Database 
                            * Computations: 
                                * Pandas 
                                * Numpy 
                            * Web scraping:
                                * Selenium 
                                * Scrapy
                            

                            ''')
        ], id = "description")
            
########################################################################################## Dashboard functions ######################################################################################

## Showing/Hiding stock_value_slider based on a choice from first Dropdown

## Printing values selected through price range slider
@app.callback(
    [Output('slider_output', 'children'),
    ],
    [
    Input('stock_value_slider', 'value')])
def update_price_slider_output(stock_values):

    value1 = stock_values[0]
    value2 = stock_values[1]
    str_to_ret = 'Desired price range to filter tickers: {} - {}'.format(value1, value2)
    to_return = [str_to_ret]
    

    return to_return

## Filtering tickers based on industry choice from first dropdown list and price range slider
@app.callback(
    Output("ticker", "options"), 
    [
        Input("Industry", "value"), 
        Input("stock_value_slider", "value")
    ]
)
def get_tickers(industry, stock_value_prices):

    lower_bound = stock_value_prices[0]
    higher_bound = stock_value_prices[1]

    if industry == "All":
        
        lower_bound = stock_value_prices[0]
        higher_bound = stock_value_prices[1]

        ## Choosing tickers based on their prices from last available day
        tickers_to_return = list(c.execute("""SELECT ticker 
                               FROM stocks 
                               WHERE adjusted >= ? and adjusted <= ?
                               AND date IN (SELECT MAX(date) FROM stocks)""", (lower_bound, higher_bound)))
        
        tickers_to_return = [ticker[0] for ticker in tickers_to_return]
        options = [{"label": ticker, "value": ticker} for ticker in tickers_to_return]

    else: 
        tickers_to_return = list(c.execute("""SELECT ticker 
                                              FROM stocks 
                                              WHERE adjusted >= ? 
                                              AND adjusted <= ?
                                              AND industry = ?
                                              AND date IN (SELECT MAX(date) FROM stocks)""", (lower_bound, higher_bound, industry)))

        tickers_to_return = [ticker[0] for ticker in tickers_to_return]
        options = [{"label": ticker, "value": ticker} for ticker in tickers_to_return]

        
    return options

# Function used for filtering data based on provided date ranges
@app.callback(
    # Function used for filtering data based on provided date ranges
    Output('stock_series', 'figure'),
    [
     Input('ticker', 'value'),
    Input("date_range", "start_date"), 
    Input("date_range", "end_date"), 
    Input("plot_content", "value")
     
     ])
def get_plot(ticker, start_date, end_date, plot_content):

    ## Checking what additional plot elements have been chosen and applying functions to achieve proper visualisation

    df = pd.read_sql_query("""SELECT date, ticker, open, high, low, close, "adjusted" FROM stocks WHERE ticker = ?""", conn, params = (ticker,))

    df.sort_values(by = ['date'], inplace = True)
    ## Calculating moving averages, before date filtering is imposed
    df["MA8"] = df["adjusted"].rolling(8).mean()
    df["MA21"] = df["adjusted"].rolling(21).mean()

    ## Calculating values for Bollinger Bands
    df["Upper_band"] = df["adjusted"].rolling(21).mean() + (df["adjusted"].rolling(21).std() * 2) 
    df["Lower_band"] =  df["adjusted"].rolling(21).mean() - (df["adjusted"].rolling(21).std() * 2) 

    df = df.loc[(df['date'] >= str(start_date)) & (df['date'] <= str(end_date))]
    df.index = pd.to_datetime(df["date"])

    df = df.copy()
    
    x_values = df.index
    
    ## Creating desired plots, based on requested plot elements
    data = []
    trace = go.Scatter(x = x_values, y = df["adjusted"], mode = "lines", name = 'Adjusted Close Price')
    data.append(trace)

    if "MA8" in plot_content:
        trace1 = go.Scatter(x = x_values, y = df["MA8"], mode = "lines", name = "Moving Average 8")
        data.append(trace1)

    if "MA21" in plot_content:
        trace2 = go.Scatter(x = x_values, y = df["MA21"], mode = "lines", name = "Moving Average 21")
        data.append(trace2)

    if "Candlestick" in plot_content: 
        trace3 = go.Candlestick(x = x_values, open = df['open'], high = df['high'], 
                                low = df['low'], close = df['adjusted'], name = "Candlestick")
        data.append(trace3)

    if "Bollinger Bands" in plot_content:
        trace4 = go.Scatter(x = x_values, y = df["Upper_band"], mode = "lines", name = "Upper Band")
        trace5 = go.Scatter(x = x_values, y = df["MA21"], mode = "lines", name = "MA 21 Band")
        trace6 = go.Scatter(x = x_values, y = df["Lower_band"], mode = "lines", name = "Lower Band")
        data.append(trace4)
        data.append(trace5)
        data.append(trace6)

    layout = go.Layout(title = ticker, xaxis_rangeslider_visible=False)
    fig = go.Figure(data = data, layout = layout)

    return fig


################################################################################################### Measures functions ########################################################################

## Measures dataset
df_measures = measures.create_data(90, conn)

@app.callback(

    [Output("ma_buy_sell_table", "columns"), 
    Output("ma_buy_sell_table", "data")], 

    [Input('ma_buy_sell_type', 'value')]
    
    )
def fill_ma_table(ma_buy_sell_type):


    if ma_buy_sell_type == 'BUY':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM ma_buy", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ma_buy_sell_type == 'SELL':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM ma_sell", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    else:
        pass

    return (columns, data)

@app.callback(

    [Output("ndays_measure_table", "columns"), 
    Output("ndays_measure_table", "data")], 

    [Input('ndays_measure_type', 'value')]
    
    )
def fill_measures(ndays_measure_type):

    if ndays_measure_type == 'MAX_PCT_CHANGE_POSITIVE':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM max_pct_change", conn)
        df_measures_extracted = df_measures_extracted.head(20)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'MAX_PCT_CHANGE_NEGATIVE':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM max_pct_change", conn)
        df_measures_extracted = df_measures_extracted.tail(20)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')
    
    elif ndays_measure_type == 'CONSTANT_PRICE_DROP_7_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM min_price_consecutive_7", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'CONSTANT_PRICE_DROP_4_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, industry, adjusted, pct_change FROM min_price_consecutive_4", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')
    
    elif ndays_measure_type == 'BIGGEST_NEGATIVE_CHANGE_IN_7_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, industry, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_negative_change_in_7_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'BIGGEST_NEGATIVE_CHANGE_IN_14_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, industry, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_negative_change_in_14_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'SHARPE_RATIO_LAST_14_DAYS_DATA':
        df_measures_extracted = pd.read_sql_query("""
                                                    SELECT 
                                                    ticker, 
                                                    sharpe_ratio_last_14_days, 
                                                    mean_log_returns_last_14_days,
                                                    volatility_last_14_days 
                                                    FROM sharpe_ratio_last_14_days""", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')
    
    elif ndays_measure_type == 'SHARPE_RATIO_LAST_30_DAYS_DATA':
        df_measures_extracted = pd.read_sql_query("""
                                                    SELECT ticker, 
                                                    sharpe_ratio_last_30_days, 
                                                    mean_log_returns_last_30_days, 
                                                    volatility_last_30_days 
                                                    FROM sharpe_ratio_last_30_days""", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    else:
        columns = None
        data = None

    return (columns, data)

if __name__ == '__main__':
    
    app.run_server()