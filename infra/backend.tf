# Remote state template — copy into each environment's main.tf and fill in the blanks.
# Never use local state for staging or prod.
#
# terraform {
#   backend "s3" {
#     bucket         = "disciplineos-tf-state-<ACCOUNT_ID>"
#     key            = "<ENV>/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "disciplineos-tf-locks"
#     encrypt        = true
#     kms_key_id     = "alias/disciplineos-tf-state-<ENV>"
#   }
# }
#
# Pre-requisites (created once per AWS account, outside Terraform):
#   aws s3api create-bucket --bucket disciplineos-tf-state-<ACCOUNT_ID> \
#       --region us-east-1 --create-bucket-configuration LocationConstraint=us-east-1
#   aws s3api put-bucket-versioning --bucket disciplineos-tf-state-<ACCOUNT_ID> \
#       --versioning-configuration Status=Enabled
#   aws dynamodb create-table --table-name disciplineos-tf-locks \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST \
#       --region us-east-1
