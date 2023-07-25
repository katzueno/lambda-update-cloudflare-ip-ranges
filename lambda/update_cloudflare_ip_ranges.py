import boto3
import json
import urllib.request
import logging

# BASIC CONFIG
URL = 'https://api.cloudflare.com/client/v4/ips'
# BASE_REGION = 'prefix_list_region'
BASE_REGION = 'us-east-1'
# PREFIX_NAME = 'prefix_name'
PREFIX_NAME = 'pl-0d32cc0ea748f6950'

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2', region_name=BASE_REGION)

def lambda_handler(event, context):
    try:

        ## Get IPs From Managed Prefix List
        try:
            ec2client = boto3.client('ec2')
            prefix_list = ec2client.get_managed_prefix_list_entries(
                PrefixListId=PREFIX_NAME,
            )
        except Exception as e:
            print(e)
            exit(1)

        # Fetch JSON data from URL
        # response = requests.get('https://api.cloudflare.com/client/v4/ips')
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req) as res:
        jsondata = json.load(res)

        # Extract new IPv4 CIDRs
        new_ipv4_cidrs = set(jsondata['result']['ipv4_cidrs'])

        # Extract existing IPv4 CIDRs
        existing_ipv4_cidrs = set(entry['Cidr'] for entry in prefix_list.entries)

        # Find CIDRs to add and delete
        cidrs_to_add = list(new_ipv4_cidrs - existing_ipv4_cidrs)
        cidrs_to_delete = list(existing_ipv4_cidrs - new_ipv4_cidrs)

        # Log the CIDRs to add and delete
        logger.info(f'CIDRs to add: {cidrs_to_add}')
        logger.info(f'CIDRs to delete: {cidrs_to_delete}')

        # Update the prefix list
        for i in range(0, len(cidrs_to_add), 100):
            prefix_list.modify(
                AddEntries=[
                    {
                        'Cidr': cidr,
                        'Description': 'Updated CIDR'
                    }
                    for cidr in cidrs_to_add[i:i+100]
                ]
            )

        for i in range(0, len(cidrs_to_delete), 100):
            prefix_list.modify(
                RemoveEntries=[
                    {
                        'Cidr': cidr
                    }
                    for cidr in cidrs_to_delete[i:i+100]
                ]
            )

        return {
            'statusCode': 200,
            'body': json.dumps('Prefix list updated successfully!')
        }

    except Exception as e:
        # Log the error
        logger.error(f'An error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred, please check the logs for more details.')
        }
