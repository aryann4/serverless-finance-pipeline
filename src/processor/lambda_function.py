import json
import urllib.parse
import boto3
import pandas as pd
import io
import os

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    target_bucket = os.environ['PROCESSED_BUCKET_NAME']

    if not key.endswith('.csv'):
        print(f"Skipping non-CSV file: {key}")
        return {'statusCode': 200, 'body': 'Skipped'}

    try:
        print(f"Processing {key} from {source_bucket}...")

        response = s3_client.get_object(Bucket=source_bucket, Key=key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))

        # --- NEW STEP: CLEAN COLUMN NAMES ---
        # "Transaction ID" -> "transaction_id"
        df.columns = df.columns.str.replace(' ', '_').str.lower()
        print("Columns renamed:", df.columns.tolist())
        # ------------------------------------

        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)

        new_key = key.replace('.csv', '.parquet')
        s3_client.put_object(Bucket=target_bucket, Key=new_key, Body=parquet_buffer.getvalue())

        print(f"SUCCESS: Moved {key} to {target_bucket}/{new_key}")
        return {'statusCode': 200, 'body': json.dumps(f'Saved to {target_bucket}')}

    except Exception as e:
        print(f"Error: {e}")
        raise e