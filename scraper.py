from bs4 import BeautifulSoup
import requests
import xlrd
import csv
import datetime
import json
import os

EIA_URLS = {
    "monthly": "http://www.eia.gov/dnav/ng/hist/rngwhhdm.htm",
    "daily": "http://www.eia.gov/dnav/ng/hist/rngwhhdD.htm",
    "weekly": "http://www.eia.gov/dnav/ng/hist/rngwhhdW.htm",
    "annual": "http://www.eia.gov/dnav/ng/hist/rngwhhdA.htm"
}
BASE_DOWNLOAD_URL = "http://www.eia.gov/dnav/ng/"
REQUEST_HEADERS = {
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0',
    'Referer': 'http://sportsbeta.ladbrokes.com/football',
}


def get_download_link(url):
    """
    Get a list of links to data files to download
    :return: list of links
    """
    soup = BeautifulSoup(
        requests.get(url, headers=REQUEST_HEADERS).content, 'lxml')
    links = [link.get('href') for link in soup.find_all('a')]
    download_link = [link for link in links if
                     'hist_xls' in link or str(link).endswith('.xls') or str(
                         link).endswith('.xlsx')]
    return download_link[0].replace('..', BASE_DOWNLOAD_URL)


def download_file(download_link):
    """
    Downloads files from list of links
    :return:
    """
    filename = download_link.split("/")[-1]
    try:
        result = requests.get(download_link)
        with open(filename, 'w') as out_file:
            out_file.write(result.content)
        return filename
    except:
        raise


def convert_to_csv(frequency, filename):
    workbook = xlrd.open_workbook(filename)
    data_sheet = workbook.sheet_by_index(1)
    csv_file_name = "{}_hub_gas_prices.csv".format(frequency)
    if not os.path.exists('data'):
        os.makedirs('data')
    with open("data/"+csv_file_name, 'w') as csv_file_obj:
        writer = csv.writer(csv_file_obj)
        writer.writerow(['Date', 'Price'])
        for row_idx in range(3, data_sheet.nrows):
            row = data_sheet.row_values(row_idx)
            row_date = datetime.datetime(*xlrd.xldate_as_tuple(row[0],
                                                               workbook.datemode))

            if frequency == 'monthly':
                row_date = row_date.replace(day=1)
            row[0] = row_date.strftime("%Y-%m-%d")
            writer.writerow(row)
    return csv_file_name


def create_data_package(resources):
    datapackage_json = {
        "name": "henry_hub_gas_prices",
        "title": "Henry Hub gas prices",
        "description": "Contains Henry Hub gas prices s for different frequencies",
        "sources": EIA_URLS,
        "resources": []

    }
    for resource in resources:
        datapackage_json['resources'].append({"path":"data/"+resource})
    json.dump(datapackage_json, open("data/datapackage.json", "w"))


def harvest_hub_gas_price_data():
    resources = []
    for frequency, url in EIA_URLS.iteritems():
        data_file = download_file(get_download_link(url))
        data_csv = convert_to_csv(frequency, data_file)
        resources.append(data_csv)
    create_data_package(resources)

harvest_hub_gas_price_data()
