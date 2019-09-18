provider "aws" {
  region  = var.region
  version = "~> 2.0"
}

provider "archive" {
  version = "~> 1.0"
}

data "archive_file" "beach38_monitor" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/.target/beach38-monitor-lambda.zip"
}

resource "aws_lambda_function" "beach38_monitor" {
  function_name    = "beach38-monitor-lambda"
  handler          = "beach38_monitor.lambda_handler"
  role             = aws_iam_role.beach38_monitor.arn
  runtime          = "python2.7"
  timeout          = 60
  filename         = "${path.module}/.target/beach38-monitor-lambda.zip"
  source_code_hash = data.archive_file.beach38_monitor.output_base64sha256
  environment {
    variables = {
      SLACK_URL      = var.slack_url
      SLACK_CHANNEL  = var.slack_channel
      DYNAMODB_TABLE = aws_dynamodb_table.beach38_monitor.name
    }
  }
}

resource "aws_lambda_permission" "beach38_monitor" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.beach38_monitor.function_name
  principal     = "events.amazonaws.com"
  statement_id  = "AllowExecutionFromCloudWatch"
  source_arn    = aws_cloudwatch_event_rule.beach38_monitor.arn
}

resource "aws_cloudwatch_event_rule" "beach38_monitor" {
  name                = "beach38-monitor-trigger"
  description         = "triggers beach38-monitor-lambda"
  schedule_expression = "cron(10,25,40,55 07-23 * * ? *)"
}

resource "aws_cloudwatch_event_target" "beach38_monitor" {
  target_id = "beach38-monitor-lambda"
  rule      = aws_cloudwatch_event_rule.beach38_monitor.name
  arn       = aws_lambda_function.beach38_monitor.arn
}

resource "aws_cloudwatch_log_group" "beach38_monitor" {
  name              = "/aws/lambda/${aws_lambda_function.beach38_monitor.function_name}"
  retention_in_days = 30
}

resource "aws_iam_role" "beach38_monitor" {
  name               = "beach38-monitor-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.beach38_monitor_role_policy.json
}

data "aws_iam_policy_document" "beach38_monitor_role_policy" {
  statement {
    sid = "AllowAssumeRoleFromLambda"
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      identifiers = [
        "lambda.amazonaws.com",
      ]
      type = "Service"
    }
    effect = "Allow"
  }
}

resource "aws_iam_role_policy" "beach38_monitor_policy" {
  role   = aws_iam_role.beach38_monitor.id
  policy = data.aws_iam_policy_document.beach38_monitor_policy.json
}

data "aws_iam_policy_document" "beach38_monitor_policy" {
  statement {
    sid    = "AllowWriteToCloudWatch"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      aws_cloudwatch_log_group.beach38_monitor.arn,
    ]
  }
  statement {
    sid    = "AllowReadWriteToDynamoDB"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.beach38_monitor.arn,
    ]
  }
}

resource "aws_dynamodb_table" "beach38_monitor" {
  name = "beach38-monitor-table"

  attribute {
    name = "court_name"
    type = "S"
  }

  attribute {
    name = "reservation_time"
    type = "S"
  }

  hash_key  = "court_name"
  range_key = "reservation_time"

  ttl {
    enabled        = true
    attribute_name = "retention"
  }

  read_capacity  = 1
  write_capacity = 1
}

