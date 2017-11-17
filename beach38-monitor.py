# native libs
from datetime import datetime, timedelta
import json
import requests
import os

# custom libs
from BeautifulSoup import BeautifulSoup

# court booking url
# param 1: court type id (1 = indoor, 2 = outdoor)
# param 2: date (YYYY-MM-DD)
beach38_url = 'https://ssl.forumedia.eu/beach38-courtbuchung.de/reservations.php?action=showRevervations&type_id={}&date={}'

# forcast for n days in future
forecast = 7

# watched time ranges (string)
watched_ranges = ['17:00 - 19:00 Uhr', '19:00 - 21:00 Uhr']

# let the magic begin
slack_url = os.environ['SLACK_URL']
slack_channel = os.environ['SLACK_CHANNEL']
def lambda_handler(event, context):
    available_courts = []
    for i in range(forecast):
        date = datetime.now() + timedelta(days=i+1)
        for court_type in range(2):
            response = requests.get(beach38_url.format(court_type + 1, date.strftime('%Y-%m-%d')))
            html = BeautifulSoup(response.text)
            for table in html.body.findAll('table', attrs={'class':'areaPeriods'}):
                court_name = table.find('th').text.encode('ascii',errors='ignore')
                for row in table.findAll('tr'):
                    cell = row.find('td')
                    if cell:
                        current_range = cell.text.encode('ascii',errors='ignore')
                        if current_range in watched_ranges:
                            court_status = dict(cell.attrs).get('class','')
                            if court_status == 'avaliable':
                                available_courts.append(
                                    '{} {} on {} {}'.format(
                                        court_name,
                                        court_status,
                                        date.strftime('%d.%m.%Y'),
                                        current_range
                                    )
                                )

    slack_message = {
        'channel': slack_channel,
        'text': '\n'.join(available_courts)
    }

    requests.post(slack_url, json=json.dumps(slack_message))

