# Beach38° Court Reservations Monitor Lambda

## Deployment via Terraform

Create and adapt `variables.tf` from `variables.tf.example` in the root directory of this project.
Then, run [terraform](https://www.terraform.io) from the root directory of this project.

## Manual Deployment

Zip the content of the lambda folder and deploy it as an AWS Lambda with the following parameters:

* **Runtime:** `Python 2.7`
* **Handler:** `beach38_monitor.lambda_handler`
* **Timeout:** `30 sec`
* **Environment variables:**
    * `SLACK_URL`
    * `SLACK_CHANNEL`

To schedule the Lambda for periodic execution, create a CloudWatch Event Rule with an appropriate [cron expression](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) e.g. `cron(0 8 ? * MON-FRI *)`.
