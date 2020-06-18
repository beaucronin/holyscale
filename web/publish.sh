#!/bin/bash

export WEBSITE_BUCKET="www.holyscale.cloud"
cd static
aws s3 cp --recursive . s3://$WEBSITE_BUCKET/