from selenium import webdriver
import time
import pandas as pd

def get_tickers_by_market(driver, market):
    
    driver.get("https://www.etoro.com/discover/markets/stocks/exchange/{}".format(market))
    time.sleep(5)
    
    stock_tickers = []
    
    cont = True
    
    while cont == True:
        
       
        
        print('working')
        
        stocks_table = driver.find_elements_by_class_name("symbol")
        stocks_names = [stock.text for stock in stocks_table]
        stock_tickers.append(stocks_names.copy())
        
        try:
            to_stop = driver.find_element_by_xpath("//a[@class='menu-item-button ng-star-inserted disabled']")
            cont = False
            break
        except:
            pass
        
        try:
            right_arrow = driver.find_element_by_xpath("//a[@automation-id='discover-market-next-button']")
            right_arrow.click()
        except:
            cont = False
            break
            
        time.sleep(5)
        
    return stock_tickers


def get_tickers_by_industry(driver):
    
    industries = ['basicmaterials', 'conglomerates', 'consumergoods', 'financial', 'healthcare', 
                 'industrialgoods', 'services', 'technology', 'utilities']
    
    stock_tickers = {}
    
    for industry in industries:
      
        # First we need to overpass login page, which loads for all links except markets (such as nasdaq)
        driver.get("https://www.etoro.com/discover/markets/stocks/exchange/{}".format('nasdaq'))
        driver.maximize_window()
        
        time.sleep(5)
        markets_button = driver.find_element_by_xpath("//a[@href='/discover/markets']")
        markets_button.click()
        
        time.sleep(2)
        menu_stocks = driver.find_element_by_xpath("//a[@id='menu-list-stocks']")
        menu_stocks.click()
        
        time.sleep(2)
        industry_list = driver.find_element_by_xpath("//div[contains(text(),'Industry')]")
        industry_list.click()
        
        time.sleep(2)
        industry_href_link = "/discover/markets/stocks/industry/{}".format(industry)
        get_to_industry = driver.find_element_by_xpath("//a[@href='{}']".format(industry_href_link))
        get_to_industry.click()
    
        print("\n", industry)
        time.sleep(5)

        

        cont = True

        while cont == True:

            print('working')

            stocks_table = driver.find_elements_by_class_name("symbol")
            stocks_names = [stock.text for stock in stocks_table]
            
            try:
                stock_tickers[industry].append(stocks_names.copy())
            except:
                stock_tickers[industry] = []
                stock_tickers[industry].append(stocks_names.copy())
            
            try:
                to_stop = driver.find_element_by_xpath("//a[@class='menu-item-button ng-star-inserted disabled']")
                cont = False
                break
            except:
                pass
            
            
            try:
                right_arrow = driver.find_element_by_xpath("//a[@automation-id='discover-market-next-button']")
                right_arrow.click()
            except:
                cont = False
                break

            time.sleep(5)
        
    return stock_tickers


def get_final_etoro_list():
    
    driver = webdriver.Chrome()
    
    ## Getting stocks based on market origin
    stocks_nasdaq = get_tickers_by_market(driver, 'nasdaq')
    stocks_nasdaq = [(x, "NASDAQ") for y in stocks_nasdaq for x in y]
    
    stocks_nyse = get_tickers_by_market(driver, 'nyse')
    stocks_nyse = [(x, "NYSE") for y in stocks_nyse for x in y]
    
    
    stocks_markets = stocks_nasdaq + stocks_nyse
    df_stocks_markets = pd.DataFrame(stocks_markets, columns = ['ticker', 'market'])
    
    ## Getting industries for tickers
    industry_tickers = get_tickers_by_industry(driver)    
    
    industry_tickers_flat = []
    for k in industry_tickers.keys():

        inds = industry_tickers[k]
        inds = [(x, k) for y in inds for x in y]

        industry_tickers_flat.append(inds.copy())

    industry_tickers_flat = [x for y in industry_tickers_flat for x in y]
    
    df_industry = pd.DataFrame(industry_tickers_flat, columns = ['ticker', 'industry'])
    
    
    df_final = df_stocks_markets.merge(df_industry, how = 'left', on = 'ticker')
    
    df_final.to_excel('etoro_stocks.xlsx', index = False)

get_final_etoro_list()
