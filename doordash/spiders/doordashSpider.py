# -*- coding: utf-8 -*-
import os
import time
import random
import json
import scrapy
from selenium import webdriver
from doordash.items import DoordashItem
import traceback
from scrapy.http import Request
import requests
from bs4 import BeautifulSoup
from . import cities
base_dir = os.path.dirname(os.path.abspath(__file__))

class DoordashspiderSpider(scrapy.Spider):
    name = 'doordashSpider'
    allowed_domains = ['doordash.com']

    def __init__(self, *args, **kwargs):
        self.url = 'https://www.doordash.com/'
        self.proxy_list = [
            "http://68621db5fccd4d04aabac3f424b0673b:@proxy.crawlera.com:8010/",
            "http://84dd43ea0c64481981ef0bf55bebf2c7:@proxy.crawlera.com:8010/",
        ]
        self.cities = cities.cities_list

    def get_random_proxy(self):
        random_idx = random.randint(0, len(self.proxy_list)-1)
        proxy_ip = self.proxy_list[random_idx]
        return proxy_ip

    def set_driver(self):
        random_proxy_ip = self.get_random_proxy()        
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy":random_proxy_ip,
            "ftpProxy":random_proxy_ip,
            "sslProxy":random_proxy_ip,
            "proxyType":"MANUAL",
        }    
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/80.0.3987.132 Safari/537.36'
        chrome_option = webdriver.ChromeOptions()
        chrome_option.add_argument('--no-sandbox')
        chrome_option.add_argument('--disable-dev-shm-usage')
        chrome_option.add_argument('--ignore-certificate-errors')
        chrome_option.add_argument("--disable-blink-features=AutomationControlled")
        chrome_option.add_argument(f'user-agent={user_agent}')
        chrome_option.headless = True
        
        driver = webdriver.Chrome(options = chrome_option)
        return driver

    def start_requests(self):
        
        for city in self.cities:
            try:
                # city = 'portland'
                lst = []
                
                url_driver = self.set_driver()
                url_driver.get(self.url)
                time.sleep(10)
                
                input_ = url_driver.find_element_by_xpath("//input[@aria-label='Your delivery address']")
                input_.send_keys(city.strip())
                time.sleep(5)

                url_driver.find_element_by_xpath("//button[@aria-label='Find Restaurants']").click()
                time.sleep(15)

                max_height = url_driver.execute_script("return document.body.scrollHeight")
                max_height_flag = 0

                while True:
                    # scroll down
                    url_driver.execute_script("window.scrollTo(0, " + str(max_height) + ");")
                    time.sleep(20)
                    # get current document height
                    current_height = url_driver.execute_script("return document.body.scrollHeight")

                    if current_height > max_height:
                        max_height = current_height
                    else:
                        max_height_flag += 1
                        if max_height_flag > 3:
                            max_height_flag = 0
                            break
                    continue

                nodes = url_driver.find_elements_by_xpath("//a[@data-anchor-id='StoreCard']")

                for node in nodes:
                    rest_url = node.get_attribute('href')
                    if rest_url:
                        lst.append(rest_url)
                
                url_driver.quit()

                yield Request("http://testscript.com/", callback=self.parse, meta={'rest_url':lst, 'city':city.strip()})

            except:
                print(traceback.print_exc())
                print("element not found..")
                continue
            
    def parse(self, response):
        rest_url_list = response.meta.get('rest_url')
        city = response.meta.get('city')

        for rest_url in rest_url_list:
            try:
                menu_driver = self.set_driver()
                menu_driver.get(rest_url)
                time.sleep(10)
                page_source = menu_driver.page_source
                menu_driver.quit()

                result_dict = {
                    "RESTNAME" : "",
                    "TIME" : "",
                    "RATINGS" : "",
                    "ADDRESS" : "",
                    "MENU" : [],
                }

                soup = BeautifulSoup(page_source, 'lxml')
                if soup:
                    rest_name = soup.select_one('div.sc-dcOKER h1.sc-lhGUXL')
                    if rest_name:
                        result_dict["RESTNAME"] = rest_name.text.strip()

                    open_time = soup.select_one('div.sc-dcOKER span.hlXfBB')
                    if open_time:
                        result_dict["TIME"] = open_time.text.strip()

                    location = soup.select_one('div.sc-nUItV')
                    if location:
                        result_dict["ADDRESS"] = location.text.strip()

                    ratings = soup.select_one('div.sc-dcOKER span.xdlgy')
                    if ratings:
                        rating = ratings.text.strip()
                        temp_dict = dict()
                        temp_dict["AVERAGE"] = rating.split('(')[0].strip()
                        temp_dict["VOLUME"] = rating.split('(')[1].split('Ratings')[0].strip()
                        popular_sec = soup.select_one('div.sc-lccPpP div.sc-cunDIC:nth-of-type(1)')
                        popular_items = list()
                        for popular_item in popular_sec.select('div.sc-gsxalj'):
                            popular_item_dict = dict()
                            pop_menu_name = popular_item.select_one('div.sc-fsPSfr div.sc-bECiaU')
                            if pop_menu_name:
                                popular_item_dict["POP_NAME"] = pop_menu_name.text.strip()
                            
                            pop_menu_desc = popular_item.select_one('div.sc-fsPSfr span.sc-hfsWMF')
                            if pop_menu_desc:
                                popular_item_dict["POP_DESCRIPTION"] = pop_menu_desc.text.strip()

                            pop_menu_price = popular_item.select_one('div.sc-fsPSfr span.hpbvJT')
                            if pop_menu_price:
                                popular_item_dict["POP_PRICE"] = pop_menu_price.text.strip()

                            popular_items.append(popular_item_dict)
                            temp_dict["POPULAR_ITEMS"] = popular_items
                            result_dict['RATINGS'] = temp_dict

                    menu_items = soup.select('div.sc-gsxalj')
                    for menu_item in menu_items:
                        menu_dict = dict()
                        menu_name = menu_item.select_one('div.sc-fsPSfr div.sc-bECiaU')
                        if menu_name:
                            menu_dict["NAME"] = menu_name.text.strip()
                        
                        menu_desc = menu_item.select_one('div.sc-fsPSfr span.sc-hfsWMF')
                        if menu_desc:
                            menu_dict["DESCRIPTION"] = menu_desc.text.strip()

                        menu_price = menu_item.select_one('div.sc-fsPSfr span.hpbvJT')
                        if menu_price:
                            menu_dict["PRICE"] = menu_price.text.strip()

                        menu_img = menu_item.select_one('div.sc-eLpfTy img')
                        if menu_img:
                            menu_dict["IMAGE"] = menu_img["src"].strip()

                        result_dict["MENU"].append(menu_dict)
            
                if result_dict["RESTNAME"]:        
                    with open(base_dir + '/output/' + city + '_' + result_dict["RESTNAME"] + '.json', 'w', encoding='utf-8', errors='ignore') as result_json:
                        result_json.write(json.dumps(result_dict))

                    yield result_dict
            except:
                continue
