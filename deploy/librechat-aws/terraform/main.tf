# AWS Terraform configuration for LibreChat
# Domain: chat.tersona.terpedia.com

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile
}

variable "aws_profile" {
  type        = string
  default     = "terpedia"
  description = "AWS profile to use"
}

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region"
}

variable "domain" {
  type        = string
  default     = "chat.tersona.terpedia.com"
  description = "Domain for LibreChat"
}

variable "instance_type" {
  type        = string
  default     = "t3.xlarge"
  description = "EC2 instance type (4 vCPU, 16 GB RAM)"
}

variable "key_name" {
  type        = string
  default     = "librechat-key"
  description = "SSH key pair name"
}

# Data source for latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "librechat-vpc"
  }
}

# Public subnets (2 for ALB in different AZs)
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "librechat-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "librechat-public-b"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "librechat-igw"
  }
}

# Route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "librechat-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# Security group for EC2
resource "aws_security_group" "librechat" {
  name        = "librechat-sg"
  description = "Security group for LibreChat EC2 instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH"
  }

  ingress {
    from_port       = 3080
    to_port         = 3080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "LibreChat from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "librechat-sg"
  }
}

# Security group for ALB
resource "aws_security_group" "alb" {
  name        = "librechat-alb-sg"
  description = "Security group for LibreChat ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "librechat-alb-sg"
  }
}

# IAM role for EC2 (for accessing AWS services)
resource "aws_iam_role" "librechat" {
  name = "librechat-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "librechat" {
  name = "librechat-instance-profile"
  role = aws_iam_role.librechat.name
}

# EC2 instance
resource "aws_instance" "librechat" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name
  subnet_id     = aws_subnet.public_a.id

  vpc_security_group_ids = [aws_security_group.librechat.id]
  iam_instance_profile   = aws_iam_instance_profile.librechat.name

  root_block_device {
    volume_size = 100
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              set -e
              apt-get update
              apt-get install -y docker.io
              systemctl enable docker
              systemctl start docker
              
              # Install Docker Compose
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
              
              # Create app directory
              mkdir -p /opt/librechat
              EOF

  tags = {
    Name = "librechat"
  }
}

output "instance_id" {
  value = aws_instance.librechat.id
}

output "instance_public_ip" {
  value = aws_instance.librechat.public_ip
}

output "instance_private_ip" {
  value = aws_instance.librechat.private_ip
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_instance.librechat.public_ip}"
}
