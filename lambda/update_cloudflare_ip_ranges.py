import boto3
import urllib.request
import json
import logging

# ToBeAdded
# SNS_TOPIC_ARN = 'arn:aws:sns:<region_name>:<account_id>:<topic_name>'

# BASE_REGION = 'prefix_list_region'
BASE_REGION = 'us-east-1'
# PREFIX_ID = 'prefix_ID'
PREFIX_ID = 'pl-xxxxxxxxxxx'

CloudflareIps = 'https://api.cloudflare.com/client/v4/ips'
ec2 = boto3.client('ec2', region_name=BASE_REGION)
sns = boto3.client('sns', region_name=BASE_REGION)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def update_ips(cidrs_to_add, cidrs_to_delete, version):
    # Update the prefix list
    add_entries_list = []
    del_entries_list = []

    try:
        if cidrs_to_delete:
            for del_item in cidrs_to_delete:
                del_entry_dist = {
                    "Cidr":del_item
                }
                del_entries_list.append(del_entry_dist)
        if cidrs_to_add:
            for add_item in cidrs_to_add:
                add_entry_dist = {
                    "Cidr":add_item,
                    "Description":"Cloudflare IPs"
                }
                add_entries_list.append(add_entry_dist)

        ec2.modify_managed_prefix_list(
            PrefixListId=PREFIX_ID,
            AddEntries = add_entries_list,
            RemoveEntries = del_entries_list,
            CurrentVersion = version
        )
    except Exception as e:
        # Log the error
        logger.error(f'An error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred, while changing prefix list, please check the logs for more details.')
        }
    return

def lambda_handler(event, context):
    ## Get current version of Prefix List 
    try:
        prefix_list_version = ec2.describe_managed_prefix_lists(
            PrefixListIds=[
                PREFIX_ID,
            ]
        )
    except Exception as e:
        print(e)
        exit(1)

    current_version = prefix_list_version["PrefixLists"][0]["Version"]
    logger.info(f'Current Version: {current_version}')

    ## Get IPs From Managed Prefix List
    try:
        prefix_list =  ec2.get_managed_prefix_list_entries(
            PrefixListId=PREFIX_ID
        )
        existing_ipv4_cidrs = set(entry['Cidr'] for entry in prefix_list["Entries"])
    except Exception as e:
        logger.error(f'An error occurred while getting current prefix list: {e}')
        exit(1)
 
    ## Get Cloudflare IPs
    try:
        # Fetch JSON data from URL
        webURL = urllib.request.urlopen(CloudflareIps)
        rawdata = webURL.read()
        encoding = webURL.info().get_content_charset('utf-8')
        new_cloudflareips = json.loads(rawdata.decode(encoding))

        # Extract new IPv4 CIDRs
        new_ipv4_cidrs = set(new_cloudflareips['result']['ipv4_cidrs'])
    except Exception as e:
        logger.error(f'An error occurred while getting Cloudflare IPs: {e}')
        exit(1)
    try:
        # Find CIDRs to add and delete
        cidrs_to_add = list(new_ipv4_cidrs - existing_ipv4_cidrs)
        cidrs_to_delete = list(existing_ipv4_cidrs - new_ipv4_cidrs)

        # Log the CIDRs to add and delete
        logger.info(f'CIDRs to add: {cidrs_to_add}')
        logger.info(f'CIDRs to delete: {cidrs_to_delete}')

        if cidrs_to_add or cidrs_to_delete:
            update_ips(cidrs_to_add, cidrs_to_delete, current_version)
        else:
            logger.info(f'Nothing to change. Skipping')

        return {
            'statusCode': 200,
            'body': json.dumps('Prefix list updated successfully!')
        }

    except Exception as e:
        # Log the error
        logger.error(f'An error occurred while updating prefix list: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred, please check the logs for more details.')
        }
