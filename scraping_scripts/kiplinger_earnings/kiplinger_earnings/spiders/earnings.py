import scrapy


class EarningsSpider(scrapy.Spider):
    name = 'earnings'
    allowed_domains = ['www.kiplinger.com']
    start_urls = ['http://www.kiplinger.com/investing/stocks/17494/next-week-earnings-calendar-stocks/']

    def parse(self, response):
        
        week_days = response.xpath("//h3[@class='polaris__heading']/text()").getall()

        for day, table in zip(week_days, response.xpath("//div[@class='polaris__table']")):
            
            for tr in table.xpath("//tbody//tr[position()>1]"):

                yield {
                    'day': day, 
                    'company': tr.xpath(".//td[1]/text()").get(), 
                    'ticker': tr.xpath(".//td[2]/a/text()").get(),
                    'earnings_estimate': tr.xpath(".//td[3]/text()").get()
                }
            
