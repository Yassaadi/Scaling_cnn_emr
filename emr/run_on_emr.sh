#!/bin/bash
# Create a transient EMR cluster that runs the feature extraction job and terminates itself.
#
#   BUCKET=my-bucket ./emr/run_on_emr.sh
#
# Prerequisites: AWS CLI configured, default EMR roles (aws emr create-default-roles),
# and the images uploaded to s3://$BUCKET/images/<class>/*.jpg
set -euo pipefail

: "${BUCKET:?Set BUCKET to the S3 bucket name}"
REGION="${REGION:-eu-west-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-m5.xlarge}"
CORE_NODES="${CORE_NODES:-2}"

aws s3 cp emr/bootstrap.sh "s3://$BUCKET/code/bootstrap.sh"
aws s3 cp src/extract_features.py "s3://$BUCKET/code/extract_features.py"

aws emr create-cluster \
  --region "$REGION" \
  --name "fruit-image-features" \
  --release-label emr-7.5.0 \
  --applications Name=Spark \
  --use-default-roles \
  --instance-groups \
    InstanceGroupType=MASTER,InstanceCount=1,InstanceType="$INSTANCE_TYPE" \
    InstanceGroupType=CORE,InstanceCount="$CORE_NODES",InstanceType="$INSTANCE_TYPE" \
  --bootstrap-actions Path="s3://$BUCKET/code/bootstrap.sh",Name=install-python-deps \
  --log-uri "s3://$BUCKET/logs/" \
  --steps Type=Spark,Name=extract-features,ActionOnFailure=TERMINATE_CLUSTER,Args=[\
--deploy-mode,cluster,\
s3://$BUCKET/code/extract_features.py,\
--input,s3://$BUCKET/images,\
--output,s3://$BUCKET/results,\
--pca-k,20] \
  --auto-terminate
