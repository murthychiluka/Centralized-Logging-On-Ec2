# Centralized Logging on EC2 using CloudWatch, S3 & Log Rotation

## Introduction

This project demonstrates a **centralized logging architecture** on AWS EC2 using **CloudWatch**, **Amazon S3**, and **Linux logrotate**.

In this setup:

* EC2 instances generate system and application logs
* CloudWatch Agent collects and sends logs to CloudWatch Logs
* AWS Lambda periodically archives logs from CloudWatch to S3
* Logrotate manages local disk usage on EC2

This design ensures **observability, cost efficiency, and disk safety**.


## Architecture Overview

To help visualize the centralized logging flow on EC2:

![Centralized Logging on EC2](https://github.com/aniljadhavmca/Centralized-Logging-On-Ec2/blob/main/Centralized%20Logging%20on%20EC2%20using%20CloudWatch%2C%20S3%20%26%20Log%20Rotation.png?raw=true)

> EC2 logs → CloudWatch Agent → CloudWatch Logs → EventBridge → Lambda → S3


---

## Objective of This Setup

* Collect all EC2 system and application logs
* Centralize logs in CloudWatch Logs
* Archive logs to Amazon S3 for long-term retention
* Rotate logs locally to avoid disk full issues
* Automate log archival using Lambda + EventBridge

---

## Services Used

* Amazon EC2 (Amazon Linux)
* CloudWatch Agent
* CloudWatch Logs
* AWS Lambda
* Amazon S3
* Amazon EventBridge (Scheduler)
* Linux logrotate

---

## Step-by-Step Implementation

### Step 1: Attach IAM Role to EC2

Attach an IAM role to the EC2 instance with the following managed policy:

* `CloudWatchAgentServerPolicy`

This allows the EC2 instance to push logs to CloudWatch.

### If you want more details steps use the documents attached Multicloud with devops by veera nareshit.
### Same for Log Rotations steps we have attcheed Naresh IT document

---

### Step 2: Install CloudWatch Agent on EC2

```bash
sudo yum install amazon-cloudwatch-agent -y
```

---

### Step 3: Configure CloudWatch Agent (Collect All Logs)

Create the configuration file:

```bash
sudo vi /opt/aws/amazon-cloudwatch-agent/bin/config.json
```

Paste the following configuration:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/*",
            "log_group_name": "ec2-all-logs",
            "log_stream_name": "{instance_id}-all-logs"
          }
        ]
      }
    }
  }
}
```

**Explanation**:

* `/var/log/*` → Collects OS and application logs
* `ec2-all-logs` → Central CloudWatch log group
* `{instance_id}` → Unique stream per EC2 instance

---

### Step 4: Start CloudWatch Agent

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
-a fetch-config -m ec2 \
-c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json -s
```

* Fetches configuration
* Starts the agent
* Begins sending logs to CloudWatch

---

### Step 5: Verify Logs in CloudWatch

```
ec2-all-logs
└── i-xxxxxxxx-all-logs
```

---

### Step 6: Generate Logs (Testing)

Install and start Apache:

```bash
sudo yum install httpd -y
sudo systemctl start httpd
```

Generated logs:

* `/var/log/httpd/access_log`
* `/var/log/httpd/error_log`

---

## Archiving Logs from CloudWatch to S3

### Why S3?

* Low-cost storage
* Long-term retention
* Compliance and audit readiness

---

### Step 7: Lambda Function (CloudWatch → S3)

**Lambda Responsibilities**:

* Read logs from CloudWatch log group
* Convert logs to JSON
* Compress logs using GZIP
* Upload archives to S3

**S3 Output Structure**:

```
s3://<bucket-name>/cloudwatch-logs/
└── i-xxxx-all-logs-<timestamp>.json.gz
```

---

### Step 8: Schedule Lambda using EventBridge

For testing:

```text
rate(10 minutes)
```

* `rate()` is ideal for testing
* Use `cron()` for fixed production schedules

---

## Local Log Rotation on EC2 (Disk Management)

### Step 9: Install logrotate

```bash
sudo yum install logrotate -y
```

---

### Step 10: Configure logrotate

```bash
sudo vi /etc/logrotate.d/myapp
```

```conf
/var/log/myapp/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ec2-user ec2-user
}
```

**Meaning**:

* Daily rotation
* Retain last 7 logs
* GZIP compression
* FIFO retention

---

### Step 11: logrotate Scheduling

```bash
systemctl list-timers | grep logrotate
```

* `logrotate.timer` runs daily at **00:00 UTC**

---

## Log Rotation Behavior (FIFO)

```
Day 1 → app.log.1
Day 2 → app.log.2
...
Day 7 → app.log.7
Day 8 → app.log.7 deleted
```

---

## Final End-to-End Flow

**EC2 logs → CloudWatch Agent → CloudWatch Logs → Lambda → S3**

---

## AWS EC2 Logging Summary

* EC2 generates logs in `/var/log/*`
* logrotate prevents disk exhaustion
* CloudWatch Agent ships logs securely
* CloudWatch Logs centralizes data
* EventBridge triggers Lambda
* Lambda compresses logs
* S3 stores logs long-term
