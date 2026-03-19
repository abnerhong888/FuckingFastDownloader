import requests
import re
import time
import argparse
import yaml
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

def get_all_links(url):
    options = Options()
    options.add_argument("--headless=new")  # modern headless mode
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    
    time.sleep(2)
    
    # get full rendered page
    html = driver.page_source
    # print(html)
    # extract all URLs
    links = re.findall(r'<li><a href="(https?://[^"]+)"', html)

    driver.quit()

    return links

def get_true_download_link(link):
    response = requests.get(link)
    html = response.text
    # print(html)
    name = re.search(r'<title>(.*?)</title>', html).group(1)
    url = re.search(r'"(https?://fuckingfast\.co/[^"]+)"', html).group(1)
    return name, url
    
def read_yaml(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data if data is not None else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

def write_to_yaml(names, downloadlinks):
    lists = []
    for i in range(len(names)):
        lists.append({'name': names[i], 'url': downloadlinks[i]})

    data = {'data': lists}

    file_name = names[0].split('.')[0]
    with open(file_name + '.yaml', 'w') as f:
        yaml.dump(data, f, indent=4)

    print('written to ' + file_name + '.yaml')

def append_to_yaml(file_path, names, downloadlinks):
    data = read_yaml(file_path)
    for i in range(len(names)):
        data['data'].append({'name': names[i], 'url': downloadlinks[i]})
    with open(file_path, 'w') as f:
        yaml.dump(data, f, indent=4)

    print('appended to ' + file_path)

def argparses():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action=argparse.BooleanOptionalAction, default=False, help="list to download")
    parser.add_argument("-a", "--append", type=str, default=None, help="append to .yaml")
    parser.add_argument("-u", "--url", type=str, default=None, help="url page to download")
    args = parser.parse_args()
    return args
    
def main():
    args = argparses()

    links = []
    if(args.url == None):
        return -1

    if(args.list):
        links = get_all_links(args.url)
    else:
        links.append(args.url)

    names = []
    downloadlinks = []
    
    if(len(links) == 0):
        print('no links found')
        return -1

    print('processing ' + str(len(links)) + ' links')

    for i in tqdm(range(len(links))):
        name, url = get_true_download_link(links[i])
        names.append(name)
        downloadlinks.append(url)

    if(args.append):
        append_to_yaml(args.append, names, downloadlinks) 
    else:
        write_to_yaml(names, downloadlinks)
    
if __name__ == "__main__":
    main()