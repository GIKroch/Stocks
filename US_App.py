import sqlite3
import pandas as pd
import pandas_datareader.data as web
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
conn = sqlite3.connect("stocks.db", check_same_thread = False)
c = conn.cursor()
## Running an update_data script - all conditions whether the data should be updated are not, are resolved in a script itself


############################################################################################################# Loading info about tickers #######################################################################

################################ Tickers 
all_tickers = list(c.execute("SELECT DISTINCT ticker FROM stocks"))
all_tickers = [ticker[0] for ticker in all_tickers]

nasdaq_tickers = list(c.execute("SELECT DISTINCT ticker FROM stocks WHERE market = 'NASDAQ'"))
nasdaq_tickers = [ticker[0] for ticker in nasdaq_tickers]

nyse_tickers = list(c.execute("SELECT DISTINCT ticker FROM stocks WHERE market = 'NYSE'"))
nyse_tickers = [ticker[0] for ticker in nyse_tickers]

number_of_dates = len(list(c.execute("SELECT DISTINCT date FROM stocks")))

############################## Dates
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

############################################################################################################## Dash App ########################################################################################

app = dash.Dash(__name__)
app.layout = html.Div([

                        ## Creating separeted tabs 
                        dcc.Tabs(id='tabs', value='tab-1', children=[
                            dcc.Tab(id = "Dashboard_Tab", label='Dashboard', value='tab-1'),
                            dcc.Tab(id = "Portfolio_Tab", label='My Portfolio', value='tab-2'),
                        ]), 
                        html.Div(id='tabs_content') 
    ])

## Tab selection
@app.callback(Output('tabs_content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
                        dcc.Dropdown(
                            id = "Market", 
                            options = [
                                {'label':"ALL", "value": "ALL"}, 
                                {'label':"NYSE", "value": "NYSE"}, 
                                {'label': "NASDAQ", "value":"NASDAQ"}, 
                                {'label': 'Prices Range', "value":"Prices Range"}
                            ], 
                            value = "ALL"
                        ),  

                        ## Element is hidden by default, if Price Range option from dropdown is chosen, then it becomes unhidden
                        html.Div([
                            dcc.RangeSlider(
                            id = 'stock_value_slider',
                            min = 0,
                            max= 1000,
                            step = 1,
                            value = [0,30]
                            ),
                            
                        ], style = {'display': 'block'}
                        ), 
                        
                        html.Div(id='slider_output', style = {'display': 'block'}), 
                        

                        dcc.Dropdown(
                        id = 'Ticker',
                        value = all_tickers[0]
                        ),

                        dcc.DatePickerRange(
                        id='date_range',
                        display_format = "D/M/YYYY",
                        first_day_of_week = 1,
                        min_date_allowed=date(2010, 1, 1),
                        max_date_allowed = date(max_year, max_month, max_day) + timedelta(1),
                        start_date=date(last_week_year, last_week_month, last_week_day),
                        end_date=date(max_year, max_month, max_day) + timedelta(1)
                        ),

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
    
                        dcc.Dropdown(id = 'measure_type', 
                                        options = [
                                {'label':"BUY", "value": "BUY"}, 
                                {'label':"SELL", "value": "SELL"}, 
                                {'label': 'MAX_PCT_CHANGE', 'value': 'MAX_PCT_CHANGE'}, 
                                {'label': 'LOWEST_PRICE_IN_7_DAYS', 'value': 'LOWEST_PRICE_IN_7_DAYS'}, 
                                {'label': 'LOWEST_PRICE_IN_3_DAYS', 'value': 'LOWEST_PRICE_IN_3_DAYS'}],
                                value = "BUY"
                            ),
                       dash_table.DataTable(
                            id='table-1',
                            columns=None,
                            data=None)
                    
        ]) 

    elif tab == 'tab-2':
        return html.Div([
            html.H3('Tab content 2')
        ])
            
########################################################################################## Dashboard functions ######################################################################################

## Showing/Hiding stock_value_slider based on a choice from first Dropdown
@app.callback(
    dash.dependencies.Output('stock_value_slider', 'style'), 
    [dash.dependencies.Input("Market", 'value')]
)
def show_hide_stock_value_slider(market_choice):

    if market_choice == 'Prices Range':
        return{'display':'block'}
    else:
        return{'display':'none'}

## Showing/Hiding stock_value_slider print on a choice from first Dropdown
@app.callback(
    Output('slider_output', 'style'), 
    [Input("Market", 'value')]
)
def show_hide_stock_value_slider(market_choice):

    if market_choice == 'Prices Range':
        return{'display':'block'}
    else:
        return{'display':'none'}

## Printing values selected through price range slider
@app.callback(
    Output('slider_output', 'children'),
    [Input('stock_value_slider', 'value')])
def update_output(value):
    value1 = value[0]
    value2 = value[1]
    return 'Select tickers with last day prices between {} and {}'.format(value1, value2)

## Filtering tickers based on choice from first dropdown list
@app.callback(
    Output("Ticker", "options"), 
    [
        Input("Market", "value"), 
        Input("stock_value_slider", "value")
    ]
)
def get_tickers(market, stock_value_prices):

    if market == "ALL":
        options = [{"label": ticker, "value": ticker} for ticker in all_tickers]
    
    elif market == "NYSE":
        options = [{"label": ticker, "value": ticker} for ticker in nyse_tickers]

    elif market == "NASDAQ":
        options = [{"label": ticker, "value": ticker} for ticker in nasdaq_tickers]

    else:
        lower_bound = stock_value_prices[0]
        higher_bound = stock_value_prices[1]

        ## Choosing tickers based on their prices from last available day
        price_tickers = list(c.execute("""SELECT ticker 
                               FROM stocks 
                               WHERE adjusted >= ? and adjusted <= ?
                               AND date IN (SELECT MAX(date) FROM stocks)""", (lower_bound, higher_bound)))
        
        price_tickers = [ticker[0] for ticker in price_tickers]
        options = [{"label": ticker, "value": ticker} for ticker in price_tickers]
        

        
    return options

@app.callback(
    Output('stock_series', 'figure'),
    [
     Input('Ticker', 'value'),
    Input("date_range", "start_date"), 
    Input("date_range", "end_date"), 
    Input("plot_content", "value")
     
     ])
def get_plot(ticker, start_date, end_date, plot_content):

    print(end_date)
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

    [Output("table-1", "columns"), 
    Output("table-1", "data")], 

    [Input('measure_type', 'value')]
    
    )
def fill_table(measure_type):

    if measure_type == 'MAX_PCT_CHANGE':
        df_measures_extracted = df_measures.loc[df_measures['date'] == df_measures['date'].max()].copy()
        df_measures_extracted.sort_values("pct_change", ascending = False, inplace = True)
        df_measures_extracted = df_measures_extracted.head(20)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif measure_type == 'BUY':
        df_measures_extracted = measures.buy_sell_ma_rule(df_measures, measure_type)
        df_measures_extracted.loc[:,['ticker', 'date', 'adjusted', 'pct_change']]
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif measure_type == 'SELL':
        df_measures_extracted = measures.buy_sell_ma_rule(df_measures, measure_type)
        df_measures_extracted.loc[:,['ticker', 'date', 'adjusted', 'pct_change']]
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif measure_type == 'LOWEST_PRICE_IN_7_DAYS':
        df_measures_extracted = measures.lowest_price_in_ndays(df_measures, 7)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif measure_type == 'LOWEST_PRICE_IN_3_DAYS':
        df_measures_extracted = measures.lowest_price_in_ndays(df_measures, 3)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')
    else:
        pass

    return (columns, data)

if __name__ == '__main__':
    
    app.run_server()