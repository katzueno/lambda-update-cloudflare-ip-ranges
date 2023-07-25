## Automatically update AWS resources with Cloudflare IP Ranges

This project creates Lambda function that automatically create or update AWS resource with Cloudflare service's IP ranges from the [ip-ranges.json](https://www.cloudflare.com/en-gb/ips/) file, then update your custom VPC prefix list.

The resources are created or updated in the region where the CloudFormation stack is created.


> **NOTE**  
> The idea was taken from the repository below which originally set AWS IP ranges. But made it very simple
> https://github.com/aws-samples/update-cloudflare-ip-ranges


## Overview

The CloudFormation template `cloudformation/template.yml` creates a stack with the following resources:

1. AWS Lambda function with customizable config file called `services.json`. The function's code is in `lambda/update_cloudflare_ip_ranges.py` and is written in Python compatible with version 3.9.
1. Lambda function's execution role.
1. SNS subscription and Lambda invocation permissions for the `arn:aws:sns:us-east-1:806199016981:AmazonIpSpaceChanged` SNS topic.

```
                          +-----------------+ 
                          | Lambda          | 
                          | Execution Role  | 
                          +--------+--------+ 
                                   |          
(WIP)                              |                  +-------------------+
+--------------------+    +--------+--------+         |                   |
|SNS Topic           +--->+ Lambda function +----+--->+AWS VPC Prefix List|
|AmazonIpSpaceChanged|    +--------+--------+         |                   |
+--------------------+             |                  +-------------------+
                                   |             
                        (WIP)      v             
                          +--------+--------+ 
                          | CloudWatch Logs |
                          +-----------------+
```

## Supported resources

It supports to create or update the following resource:
* VPC Prefix List




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

For VPC Prefix List, see [Reference prefix lists in your AWS resources](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists-referencing.html).

## Troubleshooting

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
