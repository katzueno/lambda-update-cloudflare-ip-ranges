# Lambda: Automatically update AWS resources with Cloudflare IP Ranges

This project creates Lambda function that automatically create or update AWS resource with Cloudflare service's IP v4 ranges from the [ip-ranges.json](https://www.cloudflare.com/en-gb/ips/) file, then update your custom VPC prefix list.


## Overview

1. EventBridge to execute an Lambda function daily
2. Lambda function to fetch Cloudflare IPs from API and update the managed prefix list.


```
                             +-----------------+ 
                             | Lambda          | 
                             | Execution Role  | 
                             +--------+--------+ 
                                   |          
                                   |                     +-------------------+
+-----------------------+    +--------+--------+         |                   |
|EventBridge            +--->+ Lambda function +----+--->+AWS VPC Prefix List|
|e.g.,cron(0 0 * * ? *) |    +--------+--------+         |                   |
+-----------------------+             |                  +-------------------+
                                      |             
                           (WIP)      v             
                             +--------+--------+ 
                             | CloudWatch Logs |
                             +-----------------+
```

## Supported resources

It supports to create or update the following resource:
* VPC Prefix List

## TBA

- Cloudformation or CDK

We welcome your PR.

## Setup

These are the overall steps to deploy:

### 1. Create a Lambda executable IAM role

- Create the following IAM Role for Lambda.
  - e.g.) `lambda-update-cloudflare-managedprefixlist`
- Remember the name of IAM role

(Please confirm and correct me!)

ToDo: changing it more strict only to allow modifying to the specific prefix (PR is welcome!)

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:DescribeTags",
                "ec2:DescribeManagedPrefixLists"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "ec2:GetManagedPrefixListEntries",
                "ec2:ModifyManagedPrefixList",
                "ec2:CreateTags"
            ],
            "Resource": "*",
            "Effect": "Allow"
        }
    ]
}
```

### 2. Create an empty managed prefix list 

- Create an empty managed VPC prefix list in your desired region
    - Predfix list name: e.g..) `cloudflare-ips`
    - Max entries: As of July 2023, Cloudflare has 15 IP range items. Set to 100 if possible, otherwise set it 30.
    - Note: Security groups by default have a limit of 60 rules for inbound and outbound. If you set the prefix max entries to above 60 you will need to raise your quota or you will encounter an error when creating a security group using the prefix list. 
- Copy and memo the prefix list ID (e.g., `pl-XXXXXXXXXXXXXXXXXXX`)

### 3. Create an lambda function

Create a Lambda funciton

- Function Name: anything (e.g., `UpdateCloudflarePrefixListIps`)
- Runtime: `Python 3.10`
- Architecture: either x86_64 or arm64 (I've tested with x86_64)
- Permmission: `Use an existing role` and select what you previously made

You don't need to turn on any additional `Advanced settings`

### 4. Change the python code & modify it to your environment

- Download the copy of `lambda/update_cloudflare_ip_ranges.py`
- Change `BASE_REGION` to your region
- Change `PREFIX_ID` to your prefix ID

### 5. Upload the code to Lambda and test

- Copy and paste via Lambda dashboard or create a zip file to upload to Lambda
- Test run the code to check if the list is updated

### 6. Add a trigger

- Go back to your lambda function
- In Function overview, click `Add trigger`
- Select `EventBridge (CloudWatch Events)`
- For Rule, select `Create a new rule`
- Name `Rule name` accordingly (e.g., `daily-lambda-update-clouflare-ip`)
- Add `Description` accordingly (e.g., `Run Cloudflare IP managed prefix list update daily`)
- For Rule type, select `Scehdule expression`
- Set the schedule accordingly
    - To run at every day at 0am (UTC): `cron(0 0 * * ? *)`
    - Cloudflare rarely update their IPv4 range. So I would say to update daily.
    - If you experience error, Cloudflare may update IP range a lot, if so, you must run Lambda immediately

### 7. Assign the managed prefix list to your ALB or EC2

- Assign the managed prefix list to your EC2 or ALB  80 and 443 HTTP(S) ports security groups.
- Make sure that you are not seeing any error message


Done!


## Troubleshooting

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

# Credit

GitHub @katzueno
Macareux Digital, Inc.

# Release History

## July 25, 2023: v0.9.0

- Initial release of working copy but not fully tested

# Special Thanks

- [Reference prefix lists in your AWS resources](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists-referencing.html).
- [AWS管理のIPが更新された時にプレフィックスリストに登録しいているIPレンジを自動更新する](https://zenn.dev/nnydtmg/articles/aws-managed-prefixlist-update-lambda)
    - GitHub [@nnydtmg / aws-prefixlist-update-lambda](https://github.com/nnydtmg/aws-prefixlist-update-lambda)
