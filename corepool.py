#!/usr/bin/python3

import logging
import pickle
from os import path
from time import sleep

import cloudscraper
from bs4 import BeautifulSoup, BeautifulStoneSoup
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

import config

# Create logger
logging.basicConfig(format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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

def generate_scraper():
    """Generate a working cloudflare scraper

    Returns:
        CloudScraper: cloudscraper object
    """
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
    def html_table_to_dict(html):
        """Parse HTML tables to a list of dictionary.

        Args:
            html (str): a whole HTML contain tables.

        Returns:
            list: A list of dictionary parsed from html table
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        results = []
        for table in tables:
            table_headers = [header.text for header in table.find('thead').find_all('th')]
            table_body = []
            for row in table.find('tbody').find_all('tr'):
                row_dict = {}
                for i, cell in enumerate(row.find_all('td')):
                    row_dict[table_headers[i]] = cell.text
                table_body.append(row_dict)
            results.append(table_body)
        return results

    farmer_table = html_table_to_dict(response_text)[0]

    return {
        "unpaid_balance": float(response_text.split('Your unpaid balance">')[1].split(' XCH')[0]),
        "plot_points": int(response_text.split('your plot count">')[1].split(' PlotPoints')[0]),
        "total_plots": int(response_text.split('Total Plot Count</div> <div class="h3">')[1].split(' </div>')[0]),
        "blocks_found": int(response_text.split('blocks earned today">')[1].split(' Block')[0]),
        'farmers': farmer_table
    }

def main():
    registry = CollectorRegistry()
    unpaid_balance_gauge = Gauge('corepool_unpaid_balance', 'unpaid XCH balance', registry=registry)
    plot_points_gauge = Gauge('corepool_plot_points', 'current accumulate plot points', registry=registry)
    total_plots_gauge = Gauge('corepool_total_plots', 'account total plots', registry=registry)
    blocks_found_gauge = Gauge('corepool_blocks_found', 'current accumulate blocks found', registry=registry)
    farmer_status_gauge = Gauge('corepool_farmer_status', '1 if the farmer is online', ['farmer'], registry=registry)
    active_farmers_gauge = Gauge('corepool_active_farmers', 'pool total active farmers', registry=registry)
    farmer_plots_gauge = Gauge('corepool_farmer_plots', 'pool total plot count', registry=registry)
    total_pool_size_pib_gauge = Gauge('corepool_total_pool_size_pib', 'pool total plot size in PiB', registry=registry)
    
    # Get a working scraper
    if path.exists('scraper.object'):
        logger.info('Found a scraper object, loading it.')
        scraper = import_scraper_object()
    else:
        logger.info('Creating a working scraper')
        scraper = generate_scraper()
        export_scraper_objects(scraper)

    # Import cookies if exists
    if path.exists('cookies.object'):
        logger.info('Found a cookies to use, importing it.')
        import_cookies(scraper)
    else:
        logger.info('No existing cookies found, getting one now...')
        scraper = get_login_session(scraper, config.CORE_POOL_USERNAME, config.CORE_POOL_PASSWORD)
        export_cookies(scraper.cookies)

    # Scrape dashboard for account info
    url = 'https://core-pool.com/dashboard'
    response = scraper.get(url, allow_redirects=False)

    # If cookies is expired, then re-login and scrape again.
    if response.status_code == 302:
        scraper = get_login_session(scraper, config.CORE_POOL_USERNAME, config.CORE_POOL_PASSWORD)
        export_cookies(scraper.cookies)
        response = scraper.get('https://core-pool.com/dashboard')
    corepool_dashboard = parse_dashboard(response.text)

    # Scrape homepage for pool info
    response = scraper.get('https://core-pool.com/')
    corepool_homepage = parse_homepage(response.text)

    # Set metrics
    active_farmers_gauge.set(corepool_homepage['active_farmers'])
    farmer_plots_gauge.set(corepool_homepage['farmer_plots'])
    total_pool_size_pib_gauge.set(corepool_homepage['total_pool_size_pib'])

    unpaid_balance_gauge.set(corepool_dashboard['unpaid_balance'])
    plot_points_gauge.set(corepool_dashboard['plot_points'])
    total_plots_gauge.set(corepool_dashboard['total_plots'])
    blocks_found_gauge.set(corepool_dashboard['blocks_found'])
    for farmer in corepool_dashboard['farmers']:
        if farmer['Status'] == ' Offline ':
            farmer_status_gauge.labels(farmer['Name']).set(0)
        elif farmer['Status'] == ' Online ':
            farmer_status_gauge.labels(farmer['Name']).set(1)

    write_to_textfile(config.METRICS_FILE_PATH, registry)

if __name__ == '__main__':
    main()
