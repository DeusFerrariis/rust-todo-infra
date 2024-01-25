terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.33.0"
    }
  }
  backend "s3" {
    bucket = "rust-todo-infra-tf"
    key    = "dev/terraform.tfstate"
    region = "us-east-1"
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

resource "aws_s3_bucket_public_access_block" "bucket_access_block" {
  bucket = aws_s3_bucket.user_site_bucket.id

  block_public_acls   = false
  block_public_policy = false
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.user_site_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.user_site_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_s3_object" "user_site_index" {
  bucket  = aws_s3_bucket.user_site_bucket.id
  key     = "index.html"
  content = "<h1>Hello World</h1>"
}

