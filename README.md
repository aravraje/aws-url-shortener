
# AWS URL Shortener

This is a simple URL shortening/unshortening solution built using AWS Services. The UI for the solution is hosted on S3 and served via CloudFront. The shortening/unshortening is done via API Gateway backed by a custom Lambda function. DynamoDB is used for storing the URLs as well as to keep track of an atomic counter used for generating the short URLs.


## Architecture

<image src="images/architecture.jpeg">


## How to deploy?

#### Prerequisites:

* Python >= 3.7
  * https://www.python.org/downloads/

* Node.js >= 10.3.0 (required for the AWS CDK Toolkit)
  * https://nodejs.org/en/download

* AWS CLI with at least the "default" profile configured
  * https://docs.aws.amazon.com/cli/latest/userguide/install-cliv1.html
  * https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#cli-quick-configuration

* AWS CDK
  * https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install


#### Steps:

1. Clone the project

```
$ git clone https://github.com/aravraje/aws-url-shortener.git
```

2. Navigate to the project folder and activate the Python virtualenv

```
$ source .env/bin/activate
```

If you are on a Windows platform, you can activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

3. Once the virtualenv is activated, install the required dependencies

```
$ pip install -r requirements.txt
```

4. At this point, you can deploy the solution using the below CDK CLI command

```
$ cdk deploy [--profile aws_cli_profile]
```
> NOTE: This is an environment-agnostic stack and when using cdk deploy to deploy environment-agnostic stacks, the AWS CDK CLI uses the specified AWS CLI profile (or the default profile, if none is specified) to determine the AWS Account and Region for deploying the stack.