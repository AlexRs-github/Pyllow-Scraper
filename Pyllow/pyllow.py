import os, pandas as pd, requests, lxml.html, re, json, datetime, time
from flatten_json import flatten
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


location = str(input("What is the location?\n"))


def zillow_total_pages():
    '''
    Returns the total number of pages as an int
    '''

    url = "https://www.zillow.com/homes/{}_rb/".format(location)

    r_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    }
    
    #create the GET Request
    r = requests.get(url, headers=r_headers)
    #get the html from that GET Request
    page = lxml.html.fromstring(r.content)
    #Get the text from the XPath li tag
    html_ls = page.xpath('//ol[@class="zsg-pagination"]')[0]
    #decode the return object as a unicode string
    total_string = lxml.html.tostring(html_ls, method='text', encoding='unicode')
    #regex the total_string to grab the number between '...' and 'Next'
    total_regex_1 = re.search(r'...\d+Next', total_string).group()
    total_regex_2 = re.search(r'\d+', total_regex_1).group()
    
    return int(total_regex_2)
    

def zillow_listings():
    '''
    Collect all of the zillow listings for the particular area
    '''

    print("Grabbing Zillow's data...")
    

    mega_list = []

    url = "https://www.zillow.com/homes/{}_rb/".format(location)

    r_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    }
    
    count = 0

    for page in range(0, zillow_total_pages()):
        new_url = url + '{}_p/'.format(page)
        r = requests.get(new_url, headers=r_headers)
        #Parse r.content using lxml.html.fromstring to retrieve list of top picks from zillow
        html = lxml.html.fromstring(r.content)
        ul_ls = html.xpath('//div[@class="minibubble template hide"]')
        for listing in ul_ls:
            count += 1
            div = lxml.html.tostring(listing, encoding='unicode')
            #Get rid of the div tags and the comment tags to get json
            comment = div.replace('<div class="minibubble template hide"><!--', '')
            comment_2 = re.sub(r':\s\\', ': ', comment)
            comment_3 = comment_2.replace('\\', '\\\\')
            json_str = comment_3.replace('--></div>', '')
            json_obj = '{"resultID":{"ID":' + str(count) + "," + '"homeInfo":' + json_str + "}}"
            json_dict = json.loads(json_obj)
            flat_json = flatten(json_dict)
            mega_list.append(flat_json)

    return mega_list


def zillow_csv(listings_list):
    '''
    Takes all of the dictionaries in a list and converts to csv
    '''
    if not os.path.exists('zillow-csv'):
        os.makedirs('zillow-csv')
    #YYYY-MM-DD-hh-mm-ss
    currdate = str(datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))
    pd.DataFrame(listings_list).to_csv('zillow-csv/zillow_' + currdate + '.csv')


def redfin_csv():
    '''
    Grabs all of the data from Redfin
    '''

    print('Grabbing Redfin\'s data...')
    #set the download directory
    options = Options()
    #set for headless mode
    options.headless = True

    '''
    options.set_preference(“browser.download.folderList”, 2);

    Values could be either 0, 1, or 2. Default value is ‘1’.

    0 – To save all files downloaded via the browser on the user’s desktop.
    1 – To save all files downloaded via the browser on the Downloads folder
    2 – To save all files downloaded via the browser on the location specified for the most recent download 
    '''

    options.set_preference("browser.download.folderList",2)

    '''
    options.set_preference(“browser.download.dir”,”/data”);

    The directory name to save the downloaded files.
    '''

    options.set_preference('browser.download.dir', os.getcwd() + "\\redfin-csv")
    #Stop the 'Save as...' dialog box when downloading all listings
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",'text/csv')
    driver = webdriver.Firefox(options=options)
    driver.get("http://redfin.com")
    driver.find_element_by_id('search-box-input').click()
    #u'\ue007' => unicode ENTER ... for some odd reason only worked?
    driver.find_element_by_id('search-box-input').send_keys(location+u'\ue007')
    #try waiting for page to load and anchor tag to become available on web page
    try:
        #time to wait before giving up
        delay = 5
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, "//a[@id='download-and-save']")))
        tags = driver.find_elements_by_xpath("//a[@id='download-and-save']")
        for tag in tags:
            driver.get(tag.get_attribute("href"))
            print("File Downloaded")
            '''
            YYYY-MM-DD-HH-MM-SS
            #general format: redfin_2019-03-22-15-15-49(2).csv

            1) wait for file to appear in downloads directory
                a) write a for loop that checks to see if file exist in directory
            2) close browser when done
                b) driver.close()
            '''
    except TimeoutException:
        print("Redfin took too long to load!")
    driver.close()


if __name__ == '__main__':
    start = time.time()
    zillow_csv(zillow_listings())
    redfin_csv()
    end = time.time()
    print("Total time: {}".format(end-start))