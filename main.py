import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta 
import os
import logging
import boto3

# Define today and one week ago (calculated per run)
today = datetime.now().strftime("%d/%m/%Y") + " 11:59:59 PM"
one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y") + " 12:00:00 AM"


# Get ENV variables
host = os.environ.get('HOST')
clientID = os.environ.get('CLIENTID')
clientSecret = os.environ.get('CLIENTSECRET')
bucket = os.environ.get('BUCKET')
path = os.environ.get('PATH', "")  # Path should look like "loggingPathHere/", this defaults to be empty if you want to archive files at the root of S3 bucket

# Define S3 client
s3 = boto3.client("s3")

# Initialise logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Define function to get a token from the PBX API. Each token lasts only 30 minutes so this must be done on every run (assuming archives are happening at least 30 minutes apart)
def getToken(host, clientID, clientSecret):

    # Define authorization parameters
    auth = {'username': clientID, 'password': clientSecret}

    # Define headers
    headers = {"Content-Type": "application/json", "User-Agent": "OpenAPI"}

    # Define endpoint based on host
    endpoint = f"{host}/openapi/v1.0/get_token"

    # Convert payload to JSON bytes
    data = json.dumps(auth).encode("utf-8")

    # Create request
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers=headers,
        method="POST"
    )

    # Make request
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_text = response.read().decode()
            token = json.loads(response_text)['access_token']

    # Attempts to load 'access_token' from response. If this fails it implies an error has occurred, and so we print out the result of the request for logging
    except Exception as e:
        logger.error(f"Error getting token: {e}")
        try:
            logger.error(response_text)
        except:
            pass
        raise

    return token


def searchCDR(host, token):
    endpoint = f"{host}/openapi/v1.0/cdr/search"


    payload = {
        "start_time": one_week_ago,
        "end_time": today,
        "access_token": token
    }

    # Encode query parameters
    query_string = urllib.parse.urlencode(payload)
    url = f"{endpoint}?{query_string}"

    req = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_text = response.read().decode()
            results = json.loads(response_text)

    except Exception as e:
        logger.error(f"Error fetching CDR: {e}")
        raise

    return results


def upload_to_s3(bucket, key, content):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType="application/json"
    )


def lambda_handler(event, context):

    # Get token
    token = getToken(host, clientID, clientSecret)
    logger.info("Token acquired")

    # Get CDR data
    cdrData = searchCDR(host, token)

    # Convert into human-readable JSON with indentation
    pretty_json = json.dumps(cdrData, indent=4)

    # Define full S3 path
    fullPath = f"{path}cdr-archive_{one_week_ago.replace("/","-")}-{today.replace("/","-")}.json"

    try:
        # Upload JSON string (NOT dict)
        upload_to_s3(bucket, key=fullPath, content=pretty_json)

        logger.info(f"Archiving successful: {fullPath}")

        return {
            "statusCode": 200,
            "body": f"Uploaded to {fullPath}"
        }

    except Exception as ex:
        logger.error(f"Error: {ex}")

        return {
            "statusCode": 500,
            "body": str(ex)
        }
