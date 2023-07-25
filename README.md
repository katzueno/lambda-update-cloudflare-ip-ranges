## Automatically update AWS resources with Cloudflare IP Ranges

This project creates Lambda function that automatically create or update AWS resource with Cloudflare service's IP ranges from the [ip-ranges.json](https://www.cloudflare.com/en-gb/ips/) file.  
You can configure which service and region to get range. You can also configure to which resources you want to create or update with those ranges.  
Use cases include allowing CloudFront requests, API Gateway requests, Route53 health checker and EC2 IP range (which includes AWS Lambda and CloudWatch Synthetics).  
The resources are created or updated in the region where the CloudFormation stack is created.


> **NOTE**  
> This is an modified version of the repository below which originally set AWS IP ranges.  
> https://github.com/aws-samples/update-cloudflare-ip-ranges


## Overview

The CloudFormation template `cloudformation/template.yml` creates a stack with the following resources:

1. AWS Lambda function with customizable config file called `services.json`. The function's code is in `lambda/update_cloudflare_ip_ranges.py` and is written in Python compatible with version 3.9.
1. Lambda function's execution role.
1. SNS subscription and Lambda invocation permissions for the `arn:aws:sns:us-east-1:806199016981:AmazonIpSpaceChanged` SNS topic.

```
                          +-----------------+         +---------------------+
                          | Lambda          |         |                     |
                          | Execution Role  |    +--->+AWS WAF IPv4/IPv6 Set|
                          +--------+--------+    |    |                     |
                                   |             |    +---------------------+
                                   |             |
+--------------------+    +--------+--------+    |
|SNS Topic           +--->+ Lambda function +----+
|AmazonIpSpaceChanged|    +--------+--------+    |
+--------------------+             |             |    +-------------------+
                                   |             |    |                   |
                                   v             +--->+AWS VPC Prefix List|
                          +--------+--------+         |                   |
                          | CloudWatch Logs |         +-------------------+
                          +-----------------+
```

## Supported resources

It supports to create or update the following resource:
* WAF IPSet (only WAFv2, WAF Classic is not supported)
* VPC Prefix List


### Considerations

* Lambda code MUST have a config file called `services.json` in the root path. See below more details about its format.
* WAF IPSet will just be updated if there are entries to remove or to add.
* VPC Prefix List will just be updated if there are entries to remove or to add.
* When VPC Prefix List is created, the `max entries` configuration will be the length of current IP ranges for that service plus 10.
* When VPC Prefix List is updated, if current `max entries` configuration is lower than the length of current IP ranges for that service, it will change the `max entries` to the length of current IP ranges. If it fails to update, due to size restriction where Prefix List is used, it will NOT update the IP ranges.
* If it fails to create or update resource for any service, the code will not stop, it will continue to handle the other resource and services.
* It only creates resource for service and IP version if there is at least one IP range. Otherwise, it will not create.
* Resources are named as `cloudflare-ip-ranges-<SERVICE_NAME>-<IP_VERSION>`.  
Where:  
  * `<SERVICE_NAME>` is the service name inside `ip-ranges.json` file. Converted to lower case and replaced `_` with `-`.  
  * `<IP_VERSION>` is `ipv4` or `ipv6`.

Examples:
* `cloudflare-ip-ranges-api-gateway-ipv4`
* `cloudflare-ip-ranges-route53-healthchecks-ipv4`
* `cloudflare-ip-ranges-route53-healthchecks-ipv6`

> **NOTE ABOUT REGIONS DEPLOY**  
> There is no reason to deploy this solution twice inside the same region.  
> If you have a reason for doing it, please open an issue and let's talk about it.

## Lambda configuration

To configure which service lambda should handle IP ranges or which region, you need to change the file `services.json`.  

To see the list of possible service names inside `ip-ranges.json` file, run the command below:
```shell
curl -s 'https://api.cloudflare.com/client/v4/ips' | jq -r '.prefixes[] | .service' | sort -u
```

To see the list of possible region names inside `ip-ranges.json` file, run the command below:
```shell
curl -s 'https://api.cloudflare.com/client/v4/ips' | jq -r '.prefixes[] | .region' | sort -u
```

See below the file commented.

```shell
{
    "Services": [
        {
            # Service name. MUST match the service name inside ip-ranges.json file.
            # Case is sensitive.
            "Name": "API_GATEWAY",
            
            # Region name. It is an array, so you can specify more than one region. MUST match the region name inside ip-ranges.json file.
            # Case is sensitive.
            #
            # Please not that there is one region called GLOBAL inside ip-ranges.json file.
            # If you want to get IP ranges from all region keep the array empty.
            #
            # If you specify more than one region, or keep it empty, it will aggregate the IP ranges from those regions inside the resource at the region where Lambda function is running.
            # It will NOT create the resources on each region specified.
            "Regions": ["sa-east-1"],
            
            "PrefixList": {
                # Indicate if VPC Prefix List should be create for IP ranges from this service. It will be created in the same region where Lambda function is running.
                "Enable": true,
                # Indicate if VPC Prefix List IP ranges should be summarized or not for this specific service.
                "Summarize": true
            },
            
            "WafIPSet": {
                # Indicate if WAF IPSet should be create for IP ranges from this service. It will be created in the same region where Lambda function is running.
                "Enable": true,
                # Indicate if WAF IPSet IP ranges should be summarized or not for this specific service.
                "Summarize": true,
                # WAF IPSet scope to create or update resources. Possible values are ONLY "CLOUDFRONT" and "REGIONAL".
                # Case is sensitive.
                #
                # Note that "CLOUDFRONT" can ONLY be used in North Virginia (us-east-1) region. So, you MUST deploy it on North Virginia (us-east-1) region.
                "Scopes": ["CLOUDFRONT", "REGIONAL"]
            }
        }
    ]
}
```

Example:

```json
{
    "Services": [
        {
            "Name": "API_GATEWAY",
            "Regions": ["sa-east-1"],
            "PrefixList": {
                "Enable": true,
                "Summarize": true
            },
            "WafIPSet": {
                "Enable": true,
                "Summarize": true,
                "Scopes": ["REGIONAL"]
            }
        },
        {
            "Name": "CLOUDFRONT_ORIGIN_FACING",
            "Regions": [],
            "PrefixList": {
                "Enable": false,
                "Summarize": false
            },
            "WafIPSet": {
                "Enable": true,
                "Summarize": false,
                "Scopes": ["REGIONAL"]
            }
        },
        {
            "Name": "EC2_INSTANCE_CONNECT",
            "Regions": ["sa-east-1"],
            "PrefixList": {
                "Enable": true,
                "Summarize": false
            },
            "WafIPSet": {
                "Enable": true,
                "Summarize": false,
                "Scopes": ["REGIONAL"]
            }
        },
        {
            "Name": "ROUTE53_HEALTHCHECKS",
            "Regions": [],
            "PrefixList": {
                "Enable": true,
                "Summarize": false
            },
            "WafIPSet": {
                "Enable": true,
                "Summarize": false,
                "Scopes": ["REGIONAL"]
            }
        }
    ]
}
```

## Setup

These are the overall steps to deploy:

**Setup using CloudFormation**
1. Validate CloudFormation template file.
1. Create the CloudFormation stack.
1. Package the Lambda code into a `.zip` file.
1. Update Lambda function with the packaged code.

**Setup using Terraform**
1. Initialize Terraform state
1. Validate Terraform template.
1. Apply Terraform template.

**After setup**
1. Trigger a test Lambda invocation.
1. Reference resources
1. Clean-up





## Setup using CloudFormation
To simplify setup and deployment, assign the values to the following variables. Replace the values according to your deployment options.

```bash
export AWS_REGION="sa-east-1"
export CFN_STACK_NAME="update-cloudflare-ip-ranges"
```

> **IMPORTANT:** Please, use AWS CLI v2

### 1. Validate CloudFormation template

Ensure the CloudFormation template is valid before use it.

```bash
aws cloudformation validate-template --template-body file://cloudformation/template.yml
```

### 2. Create CloudFormation stack

At this point it will create Lambda function with a dummy code.  
You will update it later.

```bash
aws cloudformation create-stack --stack-name "${CFN_STACK_NAME}" \
  --capabilities CAPABILITY_IAM \
  --template-body file://cloudformation/template.yml && {
    ### Wait for stack to be created
    aws cloudformation wait stack-create-complete --stack-name "${CFN_STACK_NAME}"
}
```

If the stack creation fails, troubleshoot by reviewing the stack events. The typical failure reasons are insufficient IAM permissions.

### 3. Create the packaged code

Before you package it, please change `lambda/services.json` file according to your requirement. For more information read the section `Lambda configuration` above.

```bash
zip --junk-paths update_cloudflare_ip_ranges.zip lambda/update_cloudflare_ip_ranges.py lambda/services.json
```

### 4. Update lambda package code

```bash
FUNCTION_NAME=$(aws cloudformation describe-stack-resources --stack-name "${CFN_STACK_NAME}" --query "StackResources[?LogicalResourceId=='LambdaUpdateIPRanges'].PhysicalResourceId" --output text)
aws lambda update-function-code --function-name "${FUNCTION_NAME}" --zip-file fileb://update_cloudflare_ip_ranges.zip --publish
```

> **NOTE:** Every time you change Lambda function configuration file `services.json` you need to execute steps 3 and 4 again.





## Setup using Terraform

Terraform template uses the following providers:
* aws
* archive

> **IMPORTANT:** Please, use Terraform version 1.3.7 or higher

### 1. Initialize Terraform state
```bash
cd terraform/
terraform init
```

### 2. Validate Terraform template

Ensure Terraform template is valid before use it.

```bash
terraform validate
```

### 3. Apply Terraform template

Before you apply, please change `lambda/services.json` file according to your requirement. For more information read the section `Lambda configuration` above.

```bash
terraform apply
```

> **NOTE:** Every time you change Lambda function configuration file `services.json` you need to execute this step again.





## After setup

### 1a. Trigger a test Lambda invocation with the AWS CLI

After the stack is created, AWS resources are not created or updated until a new SNS message is received. To test the function and create or update AWS resources with the current IP ranges for the first time, do a test invocation with the AWS CLI command below:

**CloudFormation**
```bash
aws lambda invoke \
  --function-name "${FUNCTION_NAME}" \
  --cli-binary-format 'raw-in-base64-out' \
  --payload file://lambda/test_event.json lambda_return.json
```

**Terraform**
```bash
FUNCTION_NAME=$(terraform output | grep 'lambda_name' | cut -d ' ' -f 3 | tr -d '"')
aws lambda invoke \
  --function-name "${FUNCTION_NAME}" \
  --cli-binary-format 'raw-in-base64-out' \
  --payload file://lambda/test_event.json lambda_return.json
```

After successful invocation, you should receive the response below with no errors.

```json
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```

The content of the `lambda_return.json` will list all AWS resources created or updated by the Lambda function with IP ranges from configured services.

### 1b. Trigger a test Lambda invocation with the AWS Console

Alternatively, you can invoke the test event in the AWS Lambda console with sample event below. This event uses a `test-hash` md5 string that the function parses as a test event.

```json
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:EXAMPLE",
      "EventSource": "aws:sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "1970-01-01T00:00:00.000Z",
        "Signature": "EXAMPLE",
        "SigningCertUrl": "EXAMPLE",
        "MessageId": "12345678-1234-1234-1234-123456789012",
        "Message": "{\"create-time\": \"yyyy-mm-ddThh:mm:ss+00:00\", \"synctoken\": \"0123456789\", \"md5\": \"test-hash\", \"url\": \"https://api.cloudflare.com/client/v4/ips\"}",
        "Type": "Notification",
        "UnsubscribeUrl": "EXAMPLE",
        "TopicArn": "arn:aws:sns:EXAMPLE",
        "Subject": "TestInvoke"
      }
    }
  ]
}
```

### 2. Reference resources

For WAF IPSet, see [Using an IP set in a rule group or Web ACL](https://docs.aws.amazon.com/waf/latest/developerguide/waf-ip-set-using.html).  
For VPC Prefix List, see [Reference prefix lists in your AWS resources](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists-referencing.html).

### 3. Clean-up

Remove the temporary files, remove CloudFormation stack and destroy Terraform resources.

**CloudFormation**  
```bash
rm update_cloudflare_ip_ranges.zip
rm lambda_return.json
aws cloudformation delete-stack --stack-name "${CFN_STACK_NAME}"
unset AWS_REGION
unset CFN_STACK_NAME
```

**Terraform**  
```bash
rm lambda_return.json
terraform destroy
```


> **ATTENTION**  
> When you remove CloudFormation stack, or destroy Terraform resources, it will NOT remove WAF IPSet or VPC Prefix List created by this solution.  
> If you want to remove it, you need to do it manually.

## Lambda function customization

After the stack is created, you can customize the Lambda function's execution log level by editing the function's [environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html).

* `LOG_LEVEL`: **Optional**. Set log level to increase or reduce verbosity. The default value is `INFO`. Possible values are:
  * CRITICAL
  * ERROR
  * WARNING
  * INFO
  * DEBUG

## Troubleshooting

**Wrong WAF IPSet Scope**

> An error occurred (WAFInvalidParameterException) when calling the ListIPSets operation: Error reason: The scope is not valid., field: SCOPE_VALUE, parameter: CLOUDFRONT

Scope name `CLOUDFRONT` is correct, but it MUST be running on North Virginia (us-east-1) region. If it runs outside North Virginia, you will see the error above.  
Please make sure it is running on North Virginia (us-east-1) region.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
