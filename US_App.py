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
all_tickers.sort()

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
                        html.Div([
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
                                {'label': 'MAX_PCT_CHANGE', 'value': 'MAX_PCT_CHANGE'}, 
                                {'label': 'CONSTANT_PRICE_DROP_7_DAYS', 'value': 'CONSTANT_PRICE_DROP_7_DAYS'}, 
                                {'label': 'CONSTANT_PRICE_DROP_4_DAYS', 'value': 'CONSTANT_PRICE_DROP_4_DAYS'}, 
                                {'label': 'BIGGEST_NEGATIVE_CHANGE_IN_14_DAYS', 'value': 'BIGGEST_NEGATIVE_CHANGE_IN_14_DAYS'}, 
                                {'label': 'BIGGEST_POSITIVE_CHANGE_IN_14_DAYS', 'value': 'BIGGEST_POSITIVE_CHANGE_IN_14_DAYS'}, 
                                {'label': 'BIGGEST_NEGATIVE_CHANGE_IN_7_DAYS', 'value': 'BIGGEST_NEGATIVE_CHANGE_IN_7_DAYS'}, 
                                {'label': 'BIGGEST_POSITIVE_CHANGE_IN_7_DAYS', 'value': 'BIGGEST_POSITIVE_CHANGE_IN_7_DAYS'}],
                                value = "MAX_PCT_CHANGE"
                                ), 

                                dash_table.DataTable(
                                id='ndays_measure_table',
                                columns=None,
                                data=None)

                            ], id = 'table-right')

                        ]  , id = "tables")
                        
                    
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
        return{'display':'block', 'padding-top':'15px', 'padding-bottom':'15px'}
    else:
        return{'display':'none'}

## Printing values selected through price range slider
@app.callback(
    [Output('slider_output', 'children'),
    Output('slider_output', 'style')],
    [Input('Market', 'value'),
    Input('stock_value_slider', 'value')])
def update_output(market_choice, stock_values):

    # Printing field can be only seen when prices range is selected. In such a case css styling is applied. 
    if market_choice == 'Prices Range':
        display = {'display':'block',  'padding-bottom':'15px', 'color':'white', 'font-weight':'bold', 'font-size':'150%', 'text-align':'center'}
        value1 = stock_values[0]
        value2 = stock_values[1]
        str_to_ret = 'Tickers with last day prices between {} and {}'.format(value1, value2)
        to_return = [str_to_ret, display]
    else:
        display = {'display':'none'}
        to_return = ["", display]

    return to_return

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
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, adjusted, pct_change FROM ma_buy", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ma_buy_sell_type == 'SELL':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, adjusted, pct_change FROM ma_sell", conn)
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

    if ndays_measure_type == 'MAX_PCT_CHANGE':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, adjusted, pct_change FROM max_pct_change", conn)
        df_measures_extracted = df_measures_extracted.head(20)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'CONSTANT_PRICE_DROP_7_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, adjusted, pct_change FROM min_price_consecutive_7", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'CONSTANT_PRICE_DROP_4_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, date, adjusted, pct_change FROM min_price_consecutive_4", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'BIGGEST_NEGATIVE_CHANGE_IN_14_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_negative_change_in_14_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'BIGGEST_POSITIVE_CHANGE_IN_14_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_positive_change_in_14_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'BIGGEST_NEGATIVE_CHANGE_IN_7_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_negative_change_in_7_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    elif ndays_measure_type == 'BIGGEST_POSITIVE_CHANGE_IN_7_DAYS':
        df_measures_extracted = pd.read_sql_query("SELECT ticker, most_recent_date, most_recent_price, historical_price, price_change FROM biggest_positive_change_in_7_days", conn)
        columns=[{"name": i, "id": i} for i in df_measures_extracted.columns]
        data=df_measures_extracted.to_dict('records')

    else:
        pass

    return (columns, data)

if __name__ == '__main__':
    
    app.run_server()