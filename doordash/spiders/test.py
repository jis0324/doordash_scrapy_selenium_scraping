from bs4 import BeautifulSoup
from selenium import webdriver
import time

random_proxy_ip = "http://84dd43ea0c64481981ef0bf55bebf2c7:@proxy.crawlera.com:8010/"        
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
driver.get("https://www.doordash.com/store/pie-life-pizza-pasadena-366125/en-US")
page_source = driver.page_source
driver.quit()
result_dict = dict()
soup = BeautifulSoup(page_source, 'lxml')
if soup:
  rest_name = soup.select_one('div.sc-dcOKER h1.sc-lhGUXL')
  if rest_name:
    result_dict['RESTNAME'] = rest_name.text.strip()

  open_time = soup.select_one('div.sc-dcOKER span.hlXfBB')
  if open_time:
    result_dict['TIME'] = open_time.text.strip()
  
  location = soup.select_one('div.sc-nUItV')
  if location:
    result_dict['ADDRESS'] = location.text.strip()

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

        
    
print(result_dict)