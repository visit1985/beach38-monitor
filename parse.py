from bs4 import BeautifulSoup
import requests
import datetime
from datetime import timedelta

def checkEntryForDate(date, time):
    response = requests.get('https://ssl.forumedia.eu/beach38-courtbuchung.de/reservations.php?action=showRevervations&type_id=1&date={}'.format(date))
    html = BeautifulSoup(response.text, "html.parser")
    print('Cheking date '+date)
    for table in html.body.findAll('table', attrs={'class':'areaPeriods'}):
        for row in table.findAll('tr'):
            cell = row.find('td')
            if cell:
                if time in cell.stripped_strings:
                    cellAttrs = dict(cell.attrs).get('class', '')
                    if 'avaliable' in cellAttrs:
                        print(date + ' ' + time + ' ' + table.find('th').text + ' is avaliable')
                        print('{} {} {} is available'.format(
                            date,
                            time,
                            table.find('th').text)
                        )
                        # print(table.find('th').text, dict(cell.attrs).get('class', ''))
                    # print(table.find('th').text.encode('ascii', errors='ignore'), dict(cell.attrs).get('class', ''))

# checkEntryForDate("{}-{}-{}".format(now.year, now.month, now.day), '19:00 - 21:00 Uhr')
#Execution start
now = datetime.datetime.now()
currentWeekDay = now.weekday()

for day in range(currentWeekDay, 5):
    # Current date in format '2017-10-26'
    checkEntryForDate("{}-{}-{}".format(now.year, now.month, now.day), '17:00 - 19:00 Uhr')
    now = now + timedelta(days=1)




