## Introduction

Welcome to my Python powered web application designed for technical analysis of US market equities. 

When I graduated from my Master's in Data Science in July 2020, I instantly started thinking on how to further develop my analytical skills. I'm learning a lot on daily basis working as a data analyst at Citi. However, there are so many things one can learn, that it would be a huge loss for me not to explore other opportunities. 
                            
To grow in the analytical area one needs to get some data to practice at. Hence, the first question I had to ask myself before starting the project was: “Where to look for easily accessible and interesting data?”. The answer was straightforward – US stock market. Why was it so obvious for me? Well, I’ve been interested in the big finance world since childhood but never tried investing. I felt it was the right time to get into a trading path. To be honest, I got so excited about this idea that I couldn’t really resist myself from doing my first transaction. I bought 1 Apple stock through my Polish brokerage account (7$ fee for each foreign investment!!!) and quickly lost tens of bucks. After I closed the position it became clear that impulsive investing is not the best way to make money on a stock market. I switched to a more reasonable strategy. First, build a technical analysis application, then start making deals based on it. 

## Data Sources
This app has been created for trading on eToro platform. To keep things simple I've focused only on NYSE and NASDAQ equities. The data utilized comes from multiple sources, many of which were parsed with web scraping techniques. Please find the list of sources of specific data attributes below (link to a scraping script attached, if applicable):
* NYSE/NASDAQ Tickers available to trade on eToro – [eToro Selenium scraping script](https://github.com/GIKroch/Stocks/blob/main/scraping_scripts/get_etoro_tickers.py)
* Stock Prices – Obtained from yahoofinance through Pandas Datareader package. 
* Industrial classification [Scrapy + Selenium scraping script of stockmarketmba.com](https://github.com/GIKroch/Stocks/tree/main/scraping_scripts/stock_industries)
* List of companies publishing earning report on a specific week [Scrapy scraping script of kiplinger.com](https://github.com/GIKroch/Stocks/tree/main/scraping_scripts/kiplinger_earnings/kiplinger_earnings)

## Functionalities 
### Current
* Interactive plots of  equities selected based on industry and price range.
* Statistics 
    - price changes 
    - moving average trend reversal
    - sharpe ratio
* List of companies publishing earning reports this week. 
### Future
* Monte Carlo Simulation. 
* Sentiment analysis of stock-related news. Leveraging Twitter and financial sources (Yahoo Finance etc.) scraping. 
* Machine Learning for prediction of prices. 

## How does it work? 
The app presented here, on Heroku, is based on a snapshot of a database (3rd of December 2020). Due to a size-limitation, the data covers records starting from 1st of January 2018. The app's code repository is available at [GitHub](https://github.com/GIKroch/Stocks). The repository is bonded with Heroku. 

At my private desktop the app's database is updated daily during a working week. The update process is handled by my Raspberry Pi 4, which serves also as a network drive. Therefore, when the app is run from my desktop it can always access the most recent data. 

## Technology
The app has been created in Python, the packages used: 
* Backend:
    * Dash – Web interface
    * Plotly – Plotting interface
    * Sqlite3 – Database -> Planned migration to Postgresql
* Computations: 
    * Pandas 
    * Numpy 
* Web scraping:
    * Selenium 
    * Scrapy

## Useful links
* [App Github Repository](https://github.com/GIKroch/Stocks)
* [My LinkedIn](https://www.linkedin.com/in/grzegorz-krochmal-bb33691ab/)