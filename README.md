# Museum Visitor Interaction ETL Pipeline

Real-time ETL pipeline that processes visitor engagement data from museum exhibition sites, streaming from Kafka to PostgreSQL, deployed on AWS, with interactive Tableau analytics.

**Tech Stack:** Python | Kafka | PostgreSQL | AWS (EC2, RDS) | Terraform | Tableau

## What This Project Does

- **Extracts** visitor interactions from Kafka in real-time
- **Transforms** and validates data (timestamps, ranges, type mapping)
- **Loads** clean data into PostgreSQL
- **Visualizes** engagement metrics via Tableau dashboards
- **Deploys** to AWS with infrastructure as code

Built for a pilot study tracking visitor button presses (ratings, assistance, emergency) across 6 exhibition sites.

## Architecture
Kafka → Python ETL (EC2) → PostgreSQL (RDS) → Tableau


## Prerequisites

- Python 3.9+
- AWS account with CLI configured
- Terraform 1.0+
- Kafka cluster access
- Tableau Desktop (optional, for dashboards)

## Installation

### 1. Clone and Setup

```
bash
git clone https://github.com/yourusername/museum-visitor-etl-pipeline.git
cd museum-visitor-etl-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### 2. Configure Environment
Create .env file:
```
# Kafka
BOOTSTRAP_SERVERS=your-kafka-servers
SECURITY_PROTOCOL=SASL_SSL
SASL_MECHANISM=PLAIN
USERNAME=your-kafka-username
PASSWORD=your-kafka-password
GROUP=your-consumer-group
TOPIC=lmnh

# Database
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_USER=postgres
DB_PASSWORD=your-db-password
```

⚠️ Never commit .env to version control

### 3. Setup Database Schema

```psql -h <RDS_ENDPOINT> -U postgres -d museum -f schema.sql```
Running Locally
```python3 etl.py```
Monitor logs:
```
  tail -f consumer_success.log  # Successful processing
  tail -f consumer_error.log    # Errors and validation failures
```

## AWS Deployment

**Deploy Infrastructure**
```
  cd terraform
  terraform init
  terraform apply
```
Creates: EC2 instance, RDS database, security groups, SSH key pair

**Deploy ETL to EC2**
* Get EC2 IP
```terraform output ec2_public_ip```

* Upload code
```scp -i c22-jess-etl-key.pem etl.py validations.py database.py ec2-user@<EC2_IP>:~```

* SSH into EC2
```ssh -i c22-jess-etl-key.pem ec2-user@<EC2_IP>```

* Create .env on EC2
```nano .env  # Paste environment variables```

* Run in background
```nohup python3 etl.py > etl.log 2>&1 &```

* Verify running
```ps aux | grep etl.py```
* Testing
```
  python3 -m pytest test_etl.py -v
```

### Database Management

* Reset Database
Clears visitor_interactions while preserving reference tables:
```./reset_db.sh```
* Access Database
```
psql -h <RDS_ENDPOINT> -U postgres -d museum
```
* Useful queries:
```
SELECT COUNT(*) FROM visitor_interactions;
SELECT * FROM visitor_interactions ORDER BY at DESC LIMIT 10;
```

## Tableau Dashboard
### Connect to Database
Tableau Desktop → Connect → PostgreSQL
Server: <RDS_ENDPOINT>, Port: 5432, Database: museum
Enable "Require SSL"
### Dashboard Components
Total Interactions - Overall engagement metric
Interactions Over Time - Trend analysis
Rating Distribution - Visitor satisfaction
Exhibition Engagement - Interactions by location
Button Type Breakdown - Request proportions
Filters: Exhibition, Date Range, Button Type

## Data Validation
Message Format:
```
{
  "at": "2024-02-24T17:27:01+00:00",
  "site": "3",
  "val": 2,
  "type": null
}
```
Rules:
  at: ISO 8601 timestamp ≤ now (UTC)
  site: [0-5]
  val: [-1, 4]
  type: Only when val=-1 (0=assistance, 1=emergency)
  Button Mapping: | val | type | Meaning | |-----|------|------------| | -1 | 0 | Assistance | | -1 | 1 | Emergency | | 0-4 | None | Rating |

### Project Structure
museum-visitor-etl-pipeline/
├── etl.py                   # Main ETL script
├── validations.py           # Validation functions
├── database.py              # Database operations
├── schema.sql               # Database schema
├── test_etl.py              # Unit tests
├── reset_db.sh              # Database reset script
├── requirements.txt
├── .env                     # Environment variables (not committed)
├── README.md
└── terraform/
    ├── main.tf              # Infrastructure config
    └── terraform.tfvars     # Variables (not committed)
    
### Error Handling
Validation errors: Skip message, log details, continue processing
Database errors: Stop pipeline (fail-fast to prevent data loss)
Logs:
consumer_success.log - Successful processing
consumer_error.log - Errors with full message data

#### Troubleshooting**
**Module not found:**
```
source .venv/bin/activate
pip install -r requirements.txt
```
**Database timeout:**
Verify RDS running
Check security group allows your IP (port 5432)
**Kafka errors:**
Verify credentials in .env
Check topic exists
**EC2 SSH fails:**
Check instance running
Security group allows SSH (port 22)
Correct key: c22-jess-etl-key.pem
License
Internal project for museum pilot study.

Presentations:
https://drive.google.com/drive/folders/0AAx-tHgKbSNpUk9PVA
^ May need permission to view
