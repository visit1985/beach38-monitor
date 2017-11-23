# native libs
import boto3
from datetime import datetime, timedelta
import decimal
import json
import os

# custom libs
import requests
from BeautifulSoup import BeautifulSoup

# court booking url
# param 1: court type id (1 = indoor, 2 = outdoor)
# param 2: date (YYYY-MM-DD)
beach38_url = 'https://ssl.forumedia.eu/beach38-courtbuchung.de/reservations.php?action=showRevervations&type_id={}&date={}'

# forecast for n days in future
forecast = 7

# watched time ranges (string)
watched_ranges = ['17:00 - 19:00 Uhr', '19:00 - 21:00 Uhr']

# let the magic begin

dynamodb_table = os.environ['DYNAMODB_TABLE']
slack_url = os.environ['SLACK_URL']
slack_channel = os.environ['SLACK_CHANNEL']


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    dynamotable = dynamodb.Table(dynamodb_table)

    available_courts = []
    for i in range(forecast):
        date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=i+1)
        ttl = decimal.Decimal(date.strftime('%s'))

        for court_type in range(2):
            response = requests.get(beach38_url.format(court_type + 1, date.strftime('%Y-%m-%d')))
            html = BeautifulSoup(response.text)

            for table in html.body.findAll('table', attrs={'class': 'areaPeriods'}):
                court_name = table.find('th').text.encode('ascii', errors='ignore')

                for row in table.findAll('tr'):
                    cell = row.find('td')

                    if cell:
                        current_range = cell.text.encode('ascii', errors='ignore')

                        if current_range in watched_ranges:
                            court_status = dict(cell.attrs).get('class', '')

                            if court_status == 'avaliable':
                                available_courts.append(
                                    '{} {} on {} {}'.format(
                                        court_name,
                                        court_status,
                                        date.strftime('%d.%m.%Y'),
                                        current_range
                                    )
                                )

                            item = dynamotable.get_item(Key={
                                'court_name': court_name,
                                'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_range)
                            })

                            if 'Item' in item and item['Item']['court_state'] != court_status:
                                print "updating reservation", item['Item']['court_state']

                                dynamotable.update_item(
                                    Key={
                                        'court_name': court_name,
                                        'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_range)
                                    },
                                    UpdateExpression="set court_state = :s",
                                    ExpressionAttributeValues={
                                        ':s': court_status
                                    },
                                    ReturnValues="UPDATED_NEW"
                                )

                            else:
                                dynamotable.put_item(Item={
                                    'court_name': court_name,
                                    'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_range),
                                    'court_state': court_status,
                                    'retention': ttl
                                })

    print 'available courts:', available_courts

    if len(available_courts) > 0:
        slack_message = {
            'channel': slack_channel,
            'text': '\n'.join(available_courts)
        }

        print 'sending message to slack...'
        r = requests.post(slack_url, data=json.dumps(slack_message), headers={'Content-type': 'application/json'})
        print 'status code:', r.status_code
