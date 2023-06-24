import json
import logging
import datetime
import boto3
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# import requests

load_dotenv()


def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except client.exceptions.ResourceNotFoundException:
        raise ValueError(f"Secret with name '{secret_name}' not found.")
    except client.exceptions.InvalidRequestException:
        raise ValueError("Invalid request to retrieve secret value.")
    except client.exceptions.ServiceException:
        raise ValueError("Error occurred on the server side.")
    except Exception as e:
        raise e

    # Retrieve the secret value
    secret_value = get_secret_value_response["SecretString"]
    return secret_value


def lambda_handler(event, context):
    try:
        # Retrieve the URL from Secrets Manager
        secret_name = "URL"
        region_name = "us-east-1"
        secret_value = get_secret(secret_name, region_name)
        bucket_name = "stagedata-af"
        # Extract the URL from the secret value
        secret_value_dict = json.loads(secret_value)
        url = secret_value_dict["EXCEL_URL"]

        # Set the headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
            "referer": "https://bancentral.gov.do/",
        }

        current_date = datetime.now().strftime("%Y%m%d")
        object_key = f"{current_date}/superfile.xlsx"

        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Check the response status
        if response.status_code == 200:
            excel_data = response.content

            # Save the Excel file to S3
            s3 = boto3.client("s3")
            s3.put_object(Body=excel_data, Bucket=bucket_name, Key=object_key)

            return {"statusCode": 200, "body": "Excel file downloaded and saved to S3"}
        else:
            return {
                "statusCode": response.status_code,
                "body": "Failed to download the Excel file",
            }

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
