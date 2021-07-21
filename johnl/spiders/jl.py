from urllib import parse
import scrapy
from scrapy.http.request import Request
from selenium import webdriver
from bs4 import BeautifulSoup


class JlSpider(scrapy.Spider):
    name = 'jl'
    start_urls = ['https://www.johnlewis.com/brands']

    def __init__(self):
        self.driver = webdriver.Firefox()


    def parse(self, response ,**kwargs):
        links = self.get_brands_links(response)
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_product)


    def parse_product(self, response, **kwargs):
        products = self.get_selenium(response)
        soup=BeautifulSoup(products, 'html.parser')
        links = soup.find_all('a', class_= 'image_imageLink__1tBDW product-card_c-product-card__image__3CdTi product__image', href=True)
        for i in links:
            yield scrapy.Request(url="https://www.johnlewis.com{}".format(i['href']), callback=self.parse_description)
        next_page = response.xpath('//a[contains(@class, "Pagination_c-pagination__btn__2UzxY Pagination_c-pagination__next-btn__3g_DG")]/@href').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_product)


    def parse_description(self, response, **kwargs):
        name = self.get_name(response)
        price = self.get_price(response)
        description = self.get_description(response)
        category = self.get_category(response)
        subcategory = self.get_subcategory(response)
        img_src = self.get_img(response)
        yield{
           'name' : name,
        'price' : price,
        'desc' : description,
        'category' : category,
        'subcategory' : subcategory,
        'images_urls' : img_src
        }

    def get_category(self, response):
        return response.xpath('//ul[@class="breadcrumb-carousel__list"]//text()')[6].get()

    def get_subcategory(self, response):
        return response.xpath('//ul[@class="breadcrumb-carousel__list"]//text()')[10].get()

    def get_img(self, response):
        img1_principal = response.xpath('//div[@class="carousel u-centred"]//img/@src').get()
        img2_secundaria = response.xpath('//li[@class="product-media__item"]//img/@data-large-image').getall()
        if img1_principal == None:
            img2_secundaria = response.xpath('//div[@class="ProductImage_ProductImage__1aYqw zoom"]//img/@src').getall()
            img1_principal = response.xpath('//div[@id="image-print-container"]//img/@src').get()
        img2_secundaria.append(img1_principal)
        return img2_secundaria


    def get_selenium(self, response):
        self.driver.get(response.url)
        self.driver.implicitly_wait(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.driver.implicitly_wait(3)
        return self.driver.page_source

    def get_price(self, response):
        return response.xpath('//jl-store-stock//@skuprice').get()

    def get_name(self, response):
        return response.xpath('//jl-store-stock//@productname').get()

    def get_description(self, response):
        description = response.xpath('//ul[@class="ProductSpecification_ul__84skI"]//text()').getall()
        if description == []:
            desc_dt = response.xpath('//dt[@class="product-specification-list__label"]')
            desc_dd = response.xpath('//dd[@class="product-specification-list__value"]')
            a_dd = []
            a_dt = []
            for i in desc_dd:
                dd = i.xpath('.//text()').get()
                a_dd.append(str(dd).strip())
            for i in desc_dt:
                dt = i.xpath('.//text()').get()
                a_dt.append(str(dt).strip())
            for i in range(len(a_dd)):
                frase = "{}={}".format(a_dt[i], a_dd[i])
                description.append(frase)
        return description

    def get_brands_links(self, response):
        return response.xpath('//ul[@class="brands__values"]//li/a[re:test(@href, "/brand")]/@href').getall()
