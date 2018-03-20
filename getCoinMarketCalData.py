from imp import reload

from lxml import html

import numpy as np
import requests
import datetime
import time
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

reload(sys)
sys.setdefaultencoding('utf-8')

# Get Load Date
sysdate = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')

file_cal = open('coin_calendar.csv', 'r+b')

header_cal = ['event_date', 'name', 'symbol', 'added_on', 'description', 'report_date']

file_cal.write(','.join(str(e) for e in header_cal) + '\n')

# Coin Gecko Scores for Coins data
cal_data_url = 'https://coinmarketcal.com/?form%5Bfilter_by%5D=hot_events&form%5Bsubmit%5D=&page=1'
cal_page = requests.get(cal_data_url)
cal_tree = html.fromstring(cal_page.content)

cal_data = cal_tree.xpath(
    '//div[@class="content-box-general"]/h5/strong/text()|//div[@class="content-box-general"]/div[@class="content-box-info"]/p/text()')
page_data = cal_tree.xpath('//i[@class="fa fa-angle-double-right"]/../attribute::href')
page_base_url = "https://coinmarketcal.com/?form%5Bfilter_by%5D=hot_events&form%5Bsubmit%5D=&page="
cal_data_url = 'https://coinmarketcal.com/?form%5Bfilter_by%5D=hot_events&form%5Bsubmit%5D=&page='


def read_data_from_data_table(cal_data):
    cal_data_table = np.reshape(np.array(cal_data), (-1, 5))
    rows = []
    for data_cal in cal_data_table:
        event_date = datetime.datetime.strptime(data_cal[0], "%d %B %Y").date()
        added_date = datetime.datetime.strptime(
            data_cal[2].replace("\n", '').replace(',', '').replace('(Added ', '').replace(')', ''), "%d %B %Y").date()
        row_cal = [event_date,
                   data_cal[1].replace("\n", '').strip().split('(', 1)[0].strip(),
                   data_cal[1].replace("\n", '').split('(', 1)[1].split(')')[0],
                   added_date,
                   data_cal[3].replace("\n", '').replace("\r", '').strip().replace(",", '').replace('"', ''),
                   sysdate]
        rows.append(row_cal)

    return rows


def read_data_from_paginated_source(page_data, cal_data_url, cal_data):
    i = 2
    rows = []
    while i < int(page_data[0].split('=', -1)[3], 0):
        cal_data_url += str(i)
        cal_page = requests.get(cal_data_url)
        cal_tree = html.fromstring(cal_page.content)
        cal_data = cal_tree.xpath(
            '//div[@class="content-box-general"]/h5/strong/text()|//div[@class="content-box-general"]/div[@class="content-box-info"]/p/text()')
        cal_data_table = np.reshape(np.array(cal_data), (-1, 5))
        for data_cal in cal_data_table:
            event_date = datetime.datetime.strptime(data_cal[0], "%d %B %Y").date()
            added_date = datetime.datetime.strptime(
                data_cal[2].replace("\n", '').replace(',', '').replace('(Added ', '').replace(')', ''),
                "%d %B %Y").date()
            row_cal = [event_date,
                       data_cal[1].replace("\n", '').strip().split('(', 1)[0].strip(),
                       data_cal[1].replace("\n", '').split('(', 1)[1].split(')')[0],
                       added_date,
                       data_cal[3].replace("\n", '').replace("\r", '').strip().replace(",", '').replace('"', ''),
                       sysdate]
            rows.append(row_cal)
        i += 1
    return rows


def read_calendar_data():
    data_1 = read_data_from_data_table(cal_data)
    data_2 = read_data_from_paginated_source(page_data, cal_data_url, file_cal)
    merged_data = data_1+data_2
    all_data = ','.join(str(e) for e in merged_data) + '\n'
    return all_data


def write_date(data):
    file_cal.write(data)
    for line in file_cal:
        print line.rstrip()
    file_cal.close()


def main():
    data = read_calendar_data()
    write_date(data)

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("CryptoRadar.today").sheet1

    column_names = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                    'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA']

    cell_range = 'A1:' + str(column_names[len(data[0])]) + str(len(data))

    cells = wks.range(cell_range)

    for x in range(len(data)):
        cells[x].value = data[x].decode('utf-8')

    wks.update_cells(cells)


if __name__ == "__main__":
    main()
