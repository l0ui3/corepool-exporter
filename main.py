#!/usr/bin/python3

import pickle
from logging import raiseExceptions
from os import path
from time import sleep

import cloudscraper

import config


def import_scraper_object(scraper_file='scraper.object'):
    """Import scraper object from file

    Args:
        scraper_file (str, optional): scraper object saved with pickle.

    Returns:
        Obj: a cloudscraper object
    """
    if not path.exists(scraper_file):
        raise(f"[-] Couldn't find scraper file on {path.abspath(scraper_file)}")
    with open(scraper_file, 'rb') as f:
        return pickle.load(f)

def export_scraper_objects(scraper, scraper_file='scraper.object'):
    with open(scraper_file, 'wb') as f:
        pickle.dump(scraper, f)

def generate_working_scraper(scraper_file='scraper.object'):
    while True:
        scraper = cloudscraper.create_scraper()
        url = "https://core-pool.com/"
        print(f"[*] Trying to bypass with User-Agent: {scraper.headers['User-Agent']}")
        response = scraper.get(url)
        if response.status_code == 200:
            return scraper
        else:
            print('[*] Failed to bypass CloudFlare, try again in 5 seconds...')
            sleep(5)

def export_cookies(cookies):
    with open('cookies.object', 'wb') as f:
        pickle.dump(cookies, f)

def import_cookies(scraper, cookies_file='cookies.object') -> None:
    with open(cookies_file, 'rb') as f:
        scraper.cookies.update(pickle.load(f))

def get_login_session(scraper, username, password):
    url = 'https://core-pool.com/login'
    data = {
        'username': username,
        'password': password,
        'remember_password': 'on'
    }
    status_code = None
    print('[*] Trying to login...')
    response = scraper.post(url, data=data)
    status_code = response.status_code
    if status_code != 200:
        print('[-] Failed to login')
    else:
        print('[+] Login successfully.')
        return scraper

def parse_homepage(response_text):
    return {
        "active_farmers": int(response_text.split('activeMinerCount"> ')[1].split(' </a>')[0].replace(',', '')),
        "farmer_plots": int(response_text.split('minerPlots"> ')[1].split(' </a>')[0].replace(',', '')),
        "total_pool_size_pib": float(response_text.split('totalPoolPlotSizeTB"> ')[1].split(' PiB </a>')[0])
    }

def parse_dashboard(response_text):
    return {
        "unpaid_balance": response_text.split('Your unpaid balance">')[1].split(' XCH')[0],
        "plot_points": response_text.split('your plot count">')[1].split(' PlotPoints')[0],
        "total_plots": response_text.split('Total Plot Count</div> <div class="h3">')[1].split(' </div>')[0],
        "blocks_found": response_text.split('blocks earned today">')[1].split(' Block')[0]
    }

def scrape_homepage(scraper):
    url = "https://core-pool.com/"
    return scraper.get(url) 

def scrape_dashboard(scraper):
    url = 'https://core-pool.com/dashboard'
    return scraper.get(url)
    

# Get working scraper
if path.exists('scraper.object'):
    print('Found a scraper object, loading it.')
    scraper = import_scraper_object()
else:
    print('Creating a working scraper')
    scraper = generate_working_scraper()
    export_scraper_objects(scraper)

# Import cookies if exists
if path.exists('cookies.object'):
    print('Found a cookies to use, importing it.')
    import_cookies(scraper)
else:
    print('No existing cookies found, getting one now...')
    scraper = get_login_session(scraper, config.CORE_POOL_USERNAME, config.CORE_POOL_PASSWORD)
    export_cookies(scraper.cookies)

response = scrape_dashboard(scraper)
print(parse_dashboard(response.text))
response = scrape_homepage(scraper)
print(parse_homepage(response.text))
