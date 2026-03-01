
provider "aws" {
    region = "eu-west-2"
}

# === Security Groups ===
# Security Group for RDS
resource "aws_security_group" "c22-jess-rds-sg" {
  name        = "c22-jess-rds-sg"
  description = "Allow PostgreSQL access"
  vpc_id      = "vpc-03f0d39570fbaa750" 

  # SSH access from your IP
  ingress {
    description = "PostgreSQL from my IP"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.ip_allowlist
  }

  # Allow all outbound (for Kafka, RDS, package downloads)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c22-jess-rds-sg"
  }
}
# Security Group for EC2
resource "aws_security_group" "c22-jess-ec2-sg" {
  name        = "c22-jess-ec2-sg"
  description = "Allow SSH and outbound traffic for ETL pipeline"
  vpc_id      = "vpc-03f0d39570fbaa750"

  # SSH access from your IP
  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ip_allowlist
  }

  # Allow all outbound (for Kafka, RDS, package downloads)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c22-jess-ec2-sg"
  }
}
# Update RDS security group to allow EC2 access
resource "aws_security_group_rule" "rds_from_ec2" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.c22-jess-rds-sg.id
  source_security_group_id = aws_security_group.c22-jess-ec2-sg.id
  description              = "PostgreSQL from EC2"
}

# === DB Subnet Group
resource "aws_db_subnet_group" "c22-jess-db-subnet-group" {
  name       = "c22-jess-db-subnet-group"
  subnet_ids = ["subnet-046ec8b4e41d59ea8", "subnet-0cfeaca0e941dea5b"]

  tags = {
    Name = "c22-jess-db-subnet-group"
  }
}

# === RDS PostgreSQL Instance
resource "aws_db_instance" "c22-jess-postgres-db" {
  identifier           = "c22-jess-postgres-db"
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  
  db_name              = "museum"
  username             = "postgres"
  password             = var.db_password
  
  db_subnet_group_name = aws_db_subnet_group.c22-jess-db-subnet-group.name
  vpc_security_group_ids = [aws_security_group.c22-jess-rds-sg.id]
  publicly_accessible    = true
  
  
  skip_final_snapshot  = true
  tags = {
    Name = "c22-jess-postgres-db"
  }
}

# === EC2 Instance for ETL Pipeline
resource "aws_instance" "c22-jess-etl-pipeline" {
  ami           = "ami-0c76bd4bd302b30ec"  # Amazon Linux 2023 in eu-west-2
  instance_type = "t3.micro"
  
  key_name = "c22-jess-etl-key" 
  vpc_security_group_ids = [aws_security_group.c22-jess-ec2-sg.id]
  subnet_id              = "subnet-046ec8b4e41d59ea8"
  associate_public_ip_address = true # Auto-assign public IP for direct access
  
  # User data script to install Python and dependencies
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y python3.11 python3-pip git
              pip3 install confluent-kafka psycopg2-binary python-dotenv
              EOF

  tags = {
    Name = "c22-jess-etl-pipeline"
  }
}
# Output the EC2 public IP
output "ec2_public_ip" {
  value       = aws_instance.c22-jess-etl-pipeline.public_ip
  description = "Public IP of ETL pipeline EC2 instance"
}


variable "db_password" {
  type      = string
  sensitive = true
}

variable "ip_allowlist" {
  type = list(string)
  sensitive = true
}