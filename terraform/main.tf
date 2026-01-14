terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # --- NEW: Remote Backend ---
  backend "s3" {
    bucket = "finance-tfstate-aryan-2026"
    key    = "finance-project/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. The Raw Data Bucket (Where user uploads go)
resource "aws_s3_bucket" "raw_bucket" {
  # We use a prefix because bucket names must be globally unique
  bucket_prefix = "finance-raw-"
  force_destroy = true
}

# 2. The Processed Data Bucket (Where the clean parquet files go)
resource "aws_s3_bucket" "processed_bucket" {
  bucket_prefix = "finance-processed-"
  force_destroy = true
}

# Output the names so we can see what AWS created
output "raw_bucket_name" {
  value = aws_s3_bucket.raw_bucket.bucket
}

output "processed_bucket_name" {
  value = aws_s3_bucket.processed_bucket.bucket
}

# --- IAM ROLE (The Security Pass) ---
# This allows the Lambda to talk to other AWS services
resource "aws_iam_role" "lambda_role" {
  name = "finance_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Add basic permissions (Logging + S3 Access)
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_read" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# --- THE LAMBDA FUNCTION (The Computer) ---
# 1. Zip up your Python code so AWS can read it
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "../src/processor/lambda_function.py"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "processor_lambda" {
  filename      = "lambda_function.zip"
  function_name = "finance-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  timeout       = 10

  # The layer you added earlier
  layers = ["arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:5"]

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # --- ADD THIS NEW SECTION ---
  environment {
    variables = {
      PROCESSED_BUCKET_NAME = aws_s3_bucket.processed_bucket.bucket
    }
  }
}

# --- THE TRIGGER (The Connection) ---
# Tell S3 to notify Lambda when a file is added
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.raw_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# Give S3 permission to call the Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_bucket.arn
}

# --- ATHENA (The SQL Engine) ---

# 1. Bucket to store query results (Athena requires this)
resource "aws_s3_bucket" "athena_results" {
  bucket_prefix = "finance-athena-results-"
  force_destroy = true
}

# 2. The Workgroup (Settings for the engine)
resource "aws_athena_workgroup" "finance_workgroup" {
  name = "finance_workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/"
    }
  }
}

# 3. The Database (Logical container)
resource "aws_athena_database" "finance_db" {
  name   = "finance_db"
  bucket = aws_s3_bucket.processed_bucket.bucket
}

# 4. The Table (Schema definition)
resource "aws_glue_catalog_table" "transactions" {
  database_name = aws_athena_database.finance_db.name
  name          = "transactions"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.processed_bucket.bucket}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "my-stream"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      parameters = {
        "serialization.format" = "1"
      }
    }

    # These match the clean names from Python
    columns {
      name = "transaction_id"
      type = "string"
    }
    columns {
      name = "date"
      type = "string"
    }
    columns {
      name = "description"
      type = "string"
    }
    columns {
      name = "category"
      type = "string"
    }
    columns {
      name = "amount"
      type = "double"
    }
    columns {
      name = "type"
      type = "string"
    }
    columns {
      name = "city"
      type = "string"
    }
    columns {
      name = "state"
      type = "string"
    }
    columns {
      name = "running_balance"
      type = "double"
    }
  }
}