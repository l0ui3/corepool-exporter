#!/usr/bin/python3

import logging
import pickle
from os import path
from time import sleep

import cloudscraper

import config

# Create logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def print_prometheus(metric, values):
    """Print metrics in Prometheus format.

    Args:
        metric (str): metric name
        values ([dict]): metric value in dict
    """
    print("# HELP corepool_%s CorePool metric for %s" % (metric, metric))
    print("# TYPE corepool_%s gauge" % (metric))
    for labels in values:
        if labels is None:
            print("corepool_%s %s" % (metric, values[labels]))
        else:
            print("corepool_%s{%s} %f" % (metric, labels, values[labels]))

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
    """Export scraper object to file with pickle

    Args:
        scraper (cloudscraper.CloudScraper): A cloudscraper object
        scraper_file (str, optional): file path to save scraper object.
    """
    with open(scraper_file, 'wb') as f:
        pickle.dump(scraper, f)

def generate_working_scraper(scraper_file='scraper.object'):
    while True:
        scraper = cloudscraper.create_scraper()
        url = "https://core-pool.com/"
        logger.info(f"[*] Trying to bypass with User-Agent: {scraper.headers['User-Agent']}")
        response = scraper.get(url)
        if response.status_code == 200:
            return scraper
        else:
            logger.info('[*] Failed to bypass CloudFlare, try again in 5 seconds...')
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
    logger.info('[*] Trying to login...')
    response = scraper.post(url, data=data)
    status_code = response.status_code
    if status_code != 200:
        logger.error('[-] Failed to login')
    else:
        logger.info('[+] Login successfully.')
        return scraper

def parse_homepage(response_text):
    return {
        "active_farmers": int(response_text.split('activeMinerCount"> ')[1].split(' </a>')[0].replace(',', '')),
        "farmer_plots": int(response_text.split('minerPlots"> ')[1].split(' </a>')[0].replace(',', '')),
        "total_pool_size_pib": float(response_text.split('totalPoolPlotSizeTB"> ')[1].split(' PiB </a>')[0])
    }

def parse_dashboard(response_text):
    return {
        "unpaid_balance": float(response_text.split('Your unpaid balance">')[1].split(' XCH')[0]),
        "plot_points": int(response_text.split('your plot count">')[1].split(' PlotPoints')[0]),
        "total_plots": int(response_text.split('Total Plot Count</div> <div class="h3">')[1].split(' </div>')[0]),
        "blocks_found": int(response_text.split('blocks earned today">')[1].split(' Block')[0])
    }

def main():
    # Get working scraper
    if path.exists('scraper.object'):
        logger.info('Found a scraper object, loading it.')
        scraper = import_scraper_object()
    else:
        logger.info('Creating a working scraper')
        scraper = generate_working_scraper()
        export_scraper_objects(scraper)

    # Import cookies if exists
    if path.exists('cookies.object'):
        logger.info('Found a cookies to use, importing it.')
        import_cookies(scraper)
    else:
        logger.info('No existing cookies found, getting one now...')
        scraper = get_login_session(scraper, config.CORE_POOL_USERNAME, config.CORE_POOL_PASSWORD)
        export_cookies(scraper.cookies)

    # Scrape dashboard
    url = 'https://core-pool.com/dashboard'
    response = scraper.get(url, allow_redirects=False)

    # If cookies is expired, then re-login and scrape again.
    if response.status_code == 302:
        scraper = get_login_session(scraper, config.CORE_POOL_USERNAME, config.CORE_POOL_PASSWORD)
        export_cookies(scraper.cookies)
        response = scraper.get('https://core-pool.com/dashboard')

    corepool_dashboard = parse_dashboard(response.text)
    response = scraper.get('https://core-pool.com/')
    corepool_homepage = parse_homepage(response.text)

    for key in corepool_dashboard.keys():
        print_prometheus(key, {None: corepool_dashboard[key]})
    for key in corepool_homepage.keys():
        print_prometheus(key, {None: corepool_homepage[key]})


if __name__ == '__main__':
    main()
