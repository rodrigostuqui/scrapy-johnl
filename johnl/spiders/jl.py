from urllib import parse
import scrapy
from scrapy.http.request import Request

class JlSpider(scrapy.Spider):
    name = 'jl'
    start_urls = ['https://www.johnlewis.com/brands']


    def parse(self, response, **kwargs):
        category_value = response.xpath('//select[@class="brands__sort brands__sort--desktop pretty-select"]//option//@value').getall()
        for count, i in enumerate(category_value):
            if i!= '':
                yield scrapy.Request(url = "https://www.johnlewis.com/brands?deptId={}".format(i), callback=self.parse_category)


    def parse_category(self, response ,**kwargs):
        links = response.xpath('//li/a[re:test(@href, "/brand")]/@href').getall()
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_product)


    def parse_product(self, response, **kwargs):
        category = response.xpath('//meta[@property="og:title"]//@content').get()
        for i in response.xpath('//div[@class="GridColumn_col-sm-6__Ba6rz GridColumn_col-md-4__2vhmE GridColumn_col-lg-3__38Mp8 GridColumn_product-grid-column__C4TI0 GridColumn_shouldAnimate__2Aj_B"]'):
            name = i.xpath('.//h2[@class="cls"]//text()').get()
            price = i.xpath('.//em[@class]//text()')[3:].getall()
            if price == []:
                price = i.xpath('.//div[@class="info-section_c-product-card__section__2D2D- price_c-product-card__price__3NI9k"]//text()')[1].get()
            yield{
                'category' : category,
            'name' : name,
            'price' : price
            }
        next_page = response.xpath('//a[contains(@class, "Pagination_c-pagination__btn__2UzxY Pagination_c-pagination__next-btn__3g_DG")]/@href').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_product)