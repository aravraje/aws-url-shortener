#!/usr/bin/env python3

from aws_cdk import core

from aws_url_shortener.aws_url_shortener_stack import AwsUrlShortenerStack


app = core.App()
AwsUrlShortenerStack(app, "aws-url-shortener")

app.synth()
