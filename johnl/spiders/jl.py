from urllib import parse
import scrapy
from scrapy.http.request import Request
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import random
import string
from selenium.webdriver.firefox.options import Options
import boto3


class JlSpider(scrapy.Spider):
    name = 'jl'
    start_urls = ['https://www.johnlewis.com/brands']
    
    def __init__(self):
        option = Options()
        option.headless = True
        self.driver = webdriver.Firefox(options=option)

    def parse(self, response ,**kwargs):
        links = self.get_brands_links(response)
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_product)

    def parse_product(self, response, **kwargs):
        try:
            count = str(response.xpath('//*[@id="js-plp-header"]/div/div/h1/span/span//text()').get()).strip("()")
            count = int(count)
            if count > 24:
                products = self.get_selenium(response)
            else:
                products = response.body
        except:
            products = self.get_selenium(response)
        soup=BeautifulSoup(products, 'html.parser')
        links = soup.find_all('a', class_= 'image_imageLink__RnFSY product-card_c-product-card__image__3TMre product__image', href=True)
        for i in links:
            yield scrapy.Request(url="https://www.johnlewis.com{}".format(i['href']), callback=self.parse_description)
        next_page = response.xpath('//a[contains(@class, "Pagination_c-pagination__btn__2UzxY Pagination_c-pagination__next-btn__3g_DG")]/@href').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_product)

    def parse_description(self, response, **kwargs): 
        serial_number = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        images = self.get_url_imgs(response)
        products = self.dictionary_items(response, serial_number)
        self.insert_dynamodb(products)
        yield{
            'serial_number' : serial_number,
        'image_urls' : images
        }

    def insert_dynamodb(self, products):
        dynamodb  = boto3.resource('dynamodb')
        table = dynamodb.Table('johnl-description')
        table.put_item(Item=products)

    def dictionary_items(self, response, serial_number):
        products = {
            'serial_number' : serial_number,
        'category' : self.get_category(response),
        'subcategory' : self.get_subcategory(response),
        'name' : self.get_name(response),
        'desc' : self.get_description(response)
        }
        return products

    def get_category(self, response):
        return response.xpath('//ul[@class="breadcrumb-carousel__list"]//text()')[6].get()

    def get_subcategory(self, response):
        return response.xpath('//ul[@class="breadcrumb-carousel__list"]//text()')[10].get()

    def get_url_imgs(self, response):
        main_img = response.xpath('//div[@class="carousel u-centred"]//img/@src').get()
        side_img = response.xpath('//li[@class="product-media__item"]//img/@data-large-image').getall()
        if main_img == None:
            side_img = response.xpath('//div[@class="ProductImage_ProductImage__1aYqw zoom"]//img/@src').getall()
            main_img = response.xpath('//div[@id="image-print-container"]//img/@src').get()
        side_img.append(main_img)
        images = list()
        for img in side_img:
            images.append(response.urljoin(img))
        return images

    def get_selenium(self, response):
        self.driver.get(response.url)
        self.driver.implicitly_wait(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        return self.driver.page_source

    def get_name(self, response):
        return response.xpath('//jl-store-stock//@productname').get()

    def get_description(self, response):
        description = response.xpath('//*[@id="3"]/div/div/ul//text()')[2:].getall()
        formatted_description = list()
        count = 0 
        if description == []:
            description_label = response.xpath('//dt[@class="product-specification-list__label"]')
            description_value = response.xpath('//dd[@class="product-specification-list__value"]')
            for i in range(len(description_label)):
                value = description_value[i].xpath('.//text()').get()
                label = description_label[i].xpath('.//text()').get()
                phrase = "{} = {}".format(str(label).strip(), str(value).strip())
                formatted_description.append(phrase)
        else:
            while count < len(description)-2:
                phrase = "{} = {}".format(str(description[count]), str(description[count+2]))
                formatted_description.append(phrase)
                count = count + 3
        return formatted_description

    def get_brands_links(self, response):
        return response.xpath('//ul[@class="brands__values"]//li/a[re:test(@href, "/brand")]/@href').getall()
