# Beach38° Court Reservations Monitor Lambda

Zip the content of this folder and deploy it as an AWS Lambda with the following parameters:

* Runtime: Python 2.7
* Handler: beach38-monitor.lambda\_handler
* Timeout: 30 sec
* Environment variables:
    * SLACK\_URL
    * SLACK\_CHANNEL

To schedule the Lambda for periodic execution, create a CloudWatch Event Rule with an appropriate [cron expression](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) (e.g. `cron(0 8 ? * MON-FRI *)`).

