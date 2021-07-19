from urllib import parse
import scrapy
from scrapy.http.request import Request
from selenium import webdriver
import time

class JlSpider(scrapy.Spider):
    name = 'jl'
    start_urls = ['https://www.johnlewis.com/brands']

    def __init__(self):
        self.driver = webdriver.Chrome()

    def parse(self, response, **kwargs):
        category_value = response.xpath('//select[@class="brands__sort brands__sort--desktop pretty-select"]//option//@value').getall()

        for count, i in enumerate(category_value):
            if i!= '':
                yield scrapy.Request(url = "https://www.johnlewis.com/brands?deptId={}".format(i), callback=self.parse_category)


    def parse_category(self, response ,**kwargs):
        url = "https://www.johnlewis.com"
        links = response.xpath('//li/a[re:test(@href, "/brand")]/@href').getall()
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_product)


    def parse_product(self, response, **kwargs):
        category = response.xpath('//meta[@property="og:title"]//@content').get()
        self.driver.get(response.url)
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        products = self.driver.find_elements_by_class_name('GridColumn_col-sm-6__Ba6rz')
        for product in products:
            name = product.find_element_by_class_name('title_title__1MULs').text
            price = product.find_element_by_class_name('price_c-product-card__price__3NI9k').text
            yield {'category' : category,
            'name' : name,
            'price' : price}            

        next_page = response.xpath('//a[contains(@class, "Pagination_c-pagination__btn__2UzxY Pagination_c-pagination__next-btn__3g_DG")]/@href').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_product)
