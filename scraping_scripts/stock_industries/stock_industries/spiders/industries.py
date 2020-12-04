import scrapy
from scrapy_selenium import SeleniumRequest
from scrapy.selector import Selector
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import pandas as pd
import os
import sqlite3

class IndustriesSpider(scrapy.Spider):
    name = 'industries'
    

    def start_requests(self):

        current_directory = os.getcwd()
        root_directory = os.path.dirname(os.path.realpath(current_directory)).rsplit(os.sep, 1)[0]
        db_directory = root_directory + "\\stocks.db"
        
        
        conn = sqlite3.connect(db_directory)
        df = pd.read_sql("SELECT ticker FROM etoro_stocks", conn)
        conn.close()

        ticker_list = df['ticker'].to_list()
        ticker_list = ticker_list

        yield SeleniumRequest(
            url = "http://stockmarketmba.com/",
            wait_time = 3,
            screenshot = True, 
            callback = self.parse,
            meta={'ticker_list':ticker_list}
        )

    def parse(self, response):
        

        driver = response.meta['driver']
        
        ticker_list = response.meta['ticker_list']
        for ticker in ticker_list:
            try:
                symbol_input = driver.find_element_by_xpath("//div/input[@name='symbol']")
                symbol_input.send_keys(ticker)
                symbol_input.send_keys(Keys.ENTER)

                time.sleep(3)
                driver.set_window_size(1024, 768)


                html = driver.page_source
                html = html.encode("utf-8")
                resp = Selector(text=html)

                yield {

                    "ticker": ticker, 
                    "gics_sector": resp.xpath("//div[@class='col-sm-7']/br[3]/following-sibling::text()[1]").get().strip(), 
                    "industry": resp.xpath("//div[@class='col-sm-7']/br[4]/following-sibling::text()[1]").get().strip()

                }

            except:
                pass

