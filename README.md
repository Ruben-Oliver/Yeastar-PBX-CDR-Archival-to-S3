# Yeastar P-Series PBX: Archive CDR logs to S3 Bucket


This code is designed to be run from an Amazon Lambda service, and requires an S3 bucket to be set up for archival.

The script is intended to be ran weekly using EventBridge, and so it gathers logs from the last week. You can easily alter this behaviour by changing the time delta in line 11 of the script.

It is also assumed that your S3 bucket lives in the same account as your Lambda function, if this is not the case you will need to alter the script and inline policy to access external buckets.

# Instructions

### Lambda Function
1. Create S3 bucket for CDR archives, or get S3 bucket name from existing bucket
2. Enable API in Yeastar PBX - Ensure that the system datetime format is set to 12-hour, or modify the scripts `searchCDR` function to use a 24-hour format
3. Take note of client ID and secret
4. Create Lambda function with `main.py`.
5. Set environment variables:
	- `BUCKET` - S3 bucket name
	- `CLIENTID` - Client ID for Yeastar PBX API
	- `CLIENTSECRET` - Client Secret for Yeastar PBX API
	- `HOST` - Hostname of Yeastar PBX (e.g `https://example.au.ycmcloud.com`)
	- `PATH` - Path/key for the S3 bucket object to upload. This defaults to be empty if not set, in the case that you want the CDR logs stored at the root of the bucket.


6. Under Configuration -> Permissions, click on the link under "Role Name". Then click Add Permissions -> Create Inline Policy. Use the `inlinePolicyTemplate.json` with your target bucket name. These permissions allow the Lambda function to use `PutObject` on the target S3 bucket, and nothing else.


### EventBridge

Create a new schedule with any sort of frequency you need, and point the target at your Lambda function. My test implementation used a once-a-week cron schedule (`0 0 ? * FRI *`) to run at midnight every Friday. If you make your schedule longer than a week between archives, make sure you change the script to account for it or you'll lose logs!
