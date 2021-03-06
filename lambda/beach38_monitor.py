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
forecast = 10

# watched time ranges (string)
watched_timeslots = ['19:00 - 21:00 Uhr']

# watched week days (string)
watched_weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

# let the magic begin

dynamodb_table = os.environ['DYNAMODB_TABLE']
slack_url = os.environ['SLACK_URL']
slack_channel = os.environ['SLACK_CHANNEL']


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    dynamotable = dynamodb.Table(dynamodb_table)

    notifications = []
    for i in range(forecast):
        date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=i+1)

        if date.strftime('%a') in watched_weekdays:
            ttl = decimal.Decimal(date.strftime('%s'))

            for court_type in range(2):
                response = requests.get(beach38_url.format(court_type + 1, date.strftime('%Y-%m-%d')))
                html = BeautifulSoup(response.text)

                for table in html.body.findAll('table', attrs={'class': 'areaPeriods'}):
                    court_name = table.find('th').text.encode('ascii', errors='ignore')

                    for row in table.findAll('tr'):
                        cell = row.find('td')

                        if cell:
                            current_timeslot = cell.text.encode('ascii', errors='ignore')

                            if current_timeslot in watched_timeslots:
                                court_state = dict(cell.attrs).get('class', '')

                                # see if we already stored this combination of court_name and reservation_time
                                item = dynamotable.get_item(Key={
                                    'court_name': court_name,
                                    'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_timeslot)
                                })

                                # build the notification string
                                notification = '{} {} on {} {}'.format(
                                    court_name,
                                    court_state,
                                    date.strftime('%a, %d.%m.%Y'),
                                    current_timeslot
                                )

                                if court_state == 'avaliable':
                                    if 'Item' not in item or item['Item']['court_state'] != 'avaliable':
                                        # either the court reservation was never stored and is available,
                                        # or the courts status changed to available
                                        notifications.append(notification)

                                if 'Item' in item and item['Item']['court_state'] == 'avaliable' and court_state != 'avaliable':
                                    # or the courts status changed from available to something else
                                    notifications.append(notification)

                                if 'Item' in item:
                                    if item['Item']['court_state'] != court_state:
                                        # if the status changed update it in our dynamodb table
                                        print "update:", date.strftime('%d.%m.%Y'), current_timeslot, court_name, court_state
                                        dynamotable.update_item(
                                            Key={
                                                'court_name': court_name,
                                                'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_timeslot)
                                            },
                                            UpdateExpression="set court_state = :s",
                                            ExpressionAttributeValues={
                                                ':s': court_state
                                            },
                                            ReturnValues="UPDATED_NEW"
                                        )

                                else:
                                    # if it doesn't exist already, insert the court reservation into our dynamodb table
                                    print "insert:", court_name, date.strftime('%d.%m.%Y'), current_timeslot, court_state
                                    dynamotable.put_item(Item={
                                        'court_name': court_name,
                                        'reservation_time': '{} {}'.format(date.strftime('%d.%m.%Y'), current_timeslot),
                                        'court_state': court_state,
                                        'retention': ttl
                                    })

    print 'notifications:', notifications

    if len(notifications) > 0:
        slack_message = {
            'channel': slack_channel,
            'text': '\n'.join(notifications)
        }

        print 'sending notifications to slack...'
        r = requests.post(slack_url, data=json.dumps(slack_message), headers={'Content-type': 'application/json'})
        print 'return code:', r.status_code
