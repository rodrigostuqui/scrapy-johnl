from urllib import parse
import scrapy
from scrapy.http.request import Request
from selenium import webdriver
from bs4 import BeautifulSoup
import time

class JlSpider(scrapy.Spider):
    name = 'jl'
    start_urls = ['https://www.johnlewis.com/brands']

    def __init__(self):
        self.driver = webdriver.Firefox()


    def parse(self, response ,**kwargs):
        links = response.xpath('//li/a[re:test(@href, "/brand")]/@href').getall()
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_product)


    def parse_product(self, response, **kwargs):
        self.driver.get(response.url)
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        products = self.driver.page_source
        soup=BeautifulSoup(products, 'html.parser')
        links = soup.find_all('a', class_= 'image_imageLink__1tBDW product-card_c-product-card__image__3CdTi product__image', href=True)
        for i in links:
            yield scrapy.Request(url="https://www.johnlewis.com{}".format(i['href']), callback=self.parse_description)
        next_page = response.xpath('//a[contains(@class, "Pagination_c-pagination__btn__2UzxY Pagination_c-pagination__next-btn__3g_DG")]/@href').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_product)


    def parse_description(self, response, **kwargs):
        name = response.xpath('//jl-store-stock//@productname').get()
        price = response.xpath('//jl-store-stock//@skuprice').get()
        yield{
            'name' : name,
        'price' : price
        }