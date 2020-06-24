#!/bin/bash

export WEBSITE_BUCKET="www.holyscale.cloud"
export SRC_DIR="./src"
export WEBFLOW_DIR="/Users/beau/Downloads/holy-scale.webflow"

mkdir -p static/css
mkdir -p static/js
mkdir -p static/images

cp $WEBFLOW_DIR/*.html ./static
cp $WEBFLOW_DIR/css/*.css ./static/css
cp ./src/css/*.css ./static/css
cp $WEBFLOW_DIR/js/*.js ./static/js
cp ./src/js/*.js ./static/js
cp $WEBFLOW_DIR/images/* ./static/images
cp ./src/images/* ./static/images

# Get html files and remove the file suffix
cd static
for nam in *.html
do
    newname=${nam%.html}
    mv $nam $newname
    aws s3 cp $newname s3://$WEBSITE_BUCKET/ --content-type=text/html
done

cd css
for nam in *.css
do
    aws s3 cp $nam s3://$WEBSITE_BUCKET/css/
done

cd ../js
for nam in *.js
do
    aws s3 cp $nam s3://$WEBSITE_BUCKET/js/
done


cd ../images
for nam in *
do
    aws s3 cp $nam s3://$WEBSITE_BUCKET/images/
done
