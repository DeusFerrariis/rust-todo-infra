terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.33.0"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

resource "aws_s3_bucket" "user_site_bucket" {
  bucket_prefix = "user-site-bucket"
}


resource "aws_s3_bucket_website_configuration" "static_user_site" {
  bucket = aws_s3_bucket.user_site_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_object" "user_site_index" {
  bucket  = aws_s3_bucket.user_site_bucket.id
  key     = "index.html"
  content = "<h1>Hello World</h1>"
}

