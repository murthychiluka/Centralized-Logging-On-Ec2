import boto3
import gzip
import json
import time

# AWS clients
logs_client = boto3.client('logs')
s3_client = boto3.client('s3')

# Configuration
S3_BUCKET_NAME = 'devtestes3cloud'   # Change bucket name
LOG_GROUP = 'LOG-FROM-EC2'           # Change log group name
TIME_WINDOW_HOURS = 24               # Lookback window


def lambda_handler(event, context):
    start_time = int((time.time() - TIME_WINDOW_HOURS * 3600) * 1000)
    end_time = int(time.time() * 1000)

    paginator = logs_client.get_paginator('describe_log_streams')
    page_iterator = paginator.paginate(logGroupName=LOG_GROUP)

    uploaded_files = []

    for page in page_iterator:
        for stream in page.get('logStreams', []):
            log_stream_name = stream['logStreamName']

            try:
                response = logs_client.get_log_events(
                    logGroupName=LOG_GROUP,
                    logStreamName=log_stream_name,
                    startTime=start_time,
                    endTime=end_time,
                    limit=10000
                )

                log_events = response.get('events', [])
                if not log_events:
                    continue

                log_data = json.dumps(log_events, default=str)
                compressed_log_data = gzip.compress(log_data.encode('utf-8'))

                timestamp = int(time.time())
                file_name = f'cloudwatch-logs/{log_stream_name}-{timestamp}.json.gz'

                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=file_name,
                    Body=compressed_log_data,
                    ContentType='application/gzip'
                )

                uploaded_files.append(file_name)

            except Exception as e:
                print(f"Error processing stream {log_stream_name}: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully uploaded {len(uploaded_files)} log files to S3.',
            'files': uploaded_files
        })
    }
