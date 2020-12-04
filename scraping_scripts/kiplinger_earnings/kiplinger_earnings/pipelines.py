# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import os

class StockIndustriesPipeline:
    def process_item(self, item, spider):
        return item


class SQLitePipeline(object):


    def open_spider(self, spider):
        
        current_directory = os.getcwd()
        root_directory = os.path.dirname(os.path.realpath(current_directory)).rsplit(os.sep, 1)[0]

        db_directory = root_directory + "\\stocks.db"
        self.conn = sqlite3.connect(db_directory)
        self.c = self.conn.cursor()
        
        try:
            self.c.execute("DROP TABLE earnings")
        except:
            pass

        self.c.execute("""
                    
                    CREATE TABLE earnings(

                        ticker TEXT, 
                        full_name TEXT, 
                        week_day TEXT, 
                        earnings_estimate TEXT
                    ) 
        """)

        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        self.c.execute("""
                
                    INSERT INTO earnings VALUES (?, ?, ?, ?)
        
        """, (
            item.get('ticker'), 
            item.get('company'), 
            item.get('day'), 
            item.get('earnings_estimate')
        ))

        self.conn.commit()