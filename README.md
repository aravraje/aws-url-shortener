
# AWS URL Shortener

This is a simple, serverless URL shortening/unshortening solution built using AWS Services. The UI for the solution is hosted on S3 and served via CloudFront. The shortening/unshortening is done via API Gateway backed by a custom Lambda function. DynamoDB is used for storing the URLs as well as to keep track of an atomic counter used for generating the short URLs.


## Architecture

<image src="images/architecture.jpeg">


## How to deploy?

#### Prerequisites

* Python >= 3.7
  * https://www.python.org/downloads/
  * Installing on EC2 Linux - https://docs.aws.amazon.com/cli/latest/userguide/install-linux-python.html

* Node.js >= 10.3.0 (required for the AWS CDK Toolkit)
  * https://nodejs.org/en/download
  * Installing on EC2 Linux - https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/setting-up-node-on-ec2-instance.html#setting-up-node-on-ec2-instance-procedure

* AWS CLI with at least the "default" profile configured
  * https://docs.aws.amazon.com/cli/latest/userguide/install-cliv1.html
  * https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#cli-quick-configuration

* AWS CDK
  * https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install

* Git CLI
  * https://git-scm.com/downloads

#### Steps

1. Clone the project

```
$ git clone https://github.com/aravraje/aws-url-shortener.git
```

2. Navigate to the project folder and create a Python virtualenv (assuming that there is a python3 (or python for Windows) executable in your path with access to the venv package)

```
$ python3 -m venv .env
```

3. Activate the Python virtualenv

```
$ source .env/bin/activate
```

  - If you are on a Windows platform, you can activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

4. Once the virtualenv is activated, install the required dependencies

```
$ pip install -r requirements.txt
```

5. At this point, you can deploy the solution using "cdk deploy" CDK CLI command

> NOTE: If this is your first time deploying a CDK app in the given AWS Account and Region, you must bootstrap your AWS environment for CDK by invoking "cdk bootstrap" CDK CLI command before running the "cdk deploy" command.

```
$ cdk deploy [--profile aws_cli_profile]
```
  - This is an environment-agnostic solution and when using "cdk deploy" to deploy environment-agnostic solutions, the AWS CDK CLI uses the specified AWS CLI profile (or the "default" profile, if none is specified) to determine the AWS Account and Region for deploying the solution.

6. Once the solution gets successfully deployed, you can access the URL Shortener website using the CloudFront endpoint present under "URLShortenerWebsite" parameter in the CFN Outputs.


## Future Enhancements

- Support for user-friendly Custom alias (ex: https://xxxx.cloudfront.net/cpu-utilization).
- Dashboard to track the API usage.