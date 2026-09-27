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

```text

you need a centralized logging for multiple aws accounts in to a dedicated /secured logging account.How would you design it? 

Yes. For a centralized logging architecture across multiple AWS accounts, I would use a dedicated security/logging account and make the workload accounts send logs into it.

High-level design
                    AWS Organization
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Account A          Account B          Account C
   Prod               Dev                Security
        │                 │                 │
        │ CloudTrail      │ CloudTrail     │
        │ VPC Flow Logs   │ VPC Flow Logs  │
        │ ELB Logs        │ ELB Logs       │
        │ EKS Logs        │ EKS Logs       │
        │                 │                 │
        └────────────┬────┴─────────────────┘
                     │
                     ▼
             Dedicated Logging
               / Security
                 Account
                     │
              ┌──────┴──────┐
              │             │
          S3 Data Lake   CloudWatch
              │             │
              └──────┬──────┘
                     ▼
          OpenSearch / SIEM
                     │
                     ▼
              Security Team

```

```text
1. Create a dedicated logging/security account

I would have an AWS Organizations structure similar to:

AWS Organization
│
├── Security OU
│   ├── Log Archive Account
│   └── Security Tooling Account
│
├── Production OU
│   ├── Prod Account 1
│   └── Prod Account 2
│
└── Non-Production OU
    ├── Dev Account
    └── Test Account

The Log Archive account should be highly restricted.

Application teams should not have permission to delete or modify centralized logs.
```

```text
2. Centralize CloudTrail

I would enable AWS Organizations CloudTrail as an organization trail.

Conceptually:

Account A ─┐
Account B ─┤
Account C ─┼──> Organization CloudTrail
Account D ─┘             │
                         ▼
                  Central S3 Bucket
                  in Log Archive

This gives you API activity such as:

Who created an EC2 instance?
Who modified an IAM policy?
Who deleted an S3 bucket?
Who changed a security group?

I would enable logging across all regions and include management events; depending on requirements, I would also configure relevant data events.
```
```text
3. Central S3 log archive

The primary long-term destination would be an S3 bucket in the dedicated logging account.

For example:

s3://central-security-logs/
│
├── cloudtrail/
│   ├── account-A/
│   ├── account-B/
│   └── account-C/
│
├── vpc-flow-logs/
│
├── alb-logs/
│
└── other-security-logs/

I would configure:

S3 Block Public Access
SSE-KMS encryption
restrictive bucket policies
versioning
lifecycle policies
Object Lock where regulatory/WORM requirements exist
CloudTrail data events for the log bucket
cross-region replication if required for resilience
```

```text
4. Protect the logs from the source accounts

This is particularly important.

I don't want an administrator in a workload account to be able to do:

delete centralized logs

Therefore, the destination bucket policy in the Log Archive account would allow only the required AWS services/accounts to write logs.

The workload accounts would have write-only access, while the security team gets controlled read access.

Conceptually:

Workload Account
      │
      │ WRITE
      ▼
Log Archive Account
      │
      │ READ
      ▼
Security Team / SIEM

This provides separation of duties.
```

```text
5. Centralize VPC Flow Logs

For network visibility:

VPC
 │
 └── VPC Flow Logs
          │
          ▼
     Central destination
          │
          ▼
     S3 / CloudWatch

I would capture flow logs from important VPCs/accounts and centralize them for investigation.

For example:

Source: 10.20.1.15
Destination: 10.30.2.25
Port: 443
Action: ACCEPT

This helps investigate:

unexpected communication
rejected traffic
security-group issues
suspicious network connections
```

```text
6. EKS/container logs

For EKS workloads, I would send application/container logs to a centralized logging platform.

One possible architecture:

EKS
 │
 ├── Application logs
 ├── Container logs
 └── Kubernetes audit/security logs
          │
          ▼
     Fluent Bit / ADOT
          │
          ▼
   CloudWatch / Kinesis
          │
          ▼
 Central logging account

For example, Fluent Bit running as a DaemonSet can collect container logs.

Depending on requirements, these can eventually be stored in:

S3
CloudWatch
OpenSearch
SIEM
```

```text
7. Security services

For a mature environment, I would also aggregate security findings.

For example:

GuardDuty
Security Hub
Inspector
Macie
IAM Access Analyzer
       │
       ▼
Security Account
       │
       ▼
Centralized findings

AWS Security Hub can aggregate security findings across accounts/regions, while GuardDuty provides threat detection.

```

```text
8. Real-time alerting

I wouldn't use S3 alone if the requirement includes real-time security monitoring.

I would have something like:

AWS Services
     │
     ▼
CloudWatch / EventBridge
     │
     ▼
Security Rules
     │
     ├──> SNS
     ├──> PagerDuty
     ├──> Slack/Teams
     └──> SIEM

For example:

Root user login
      ↓
EventBridge
      ↓
Security rule
      ↓
SNS/PagerDuty
      ↓
Security team
```

```text
9. SIEM / OpenSearch

For searching and investigation:

                ┌── CloudTrail
                │
                ├── VPC Flow Logs
                │
                ├── EKS logs
                │
                └── Security findings
                         │
                         ▼
                 Central pipeline
                         │
                         ▼
                 OpenSearch / SIEM
                         │
                         ▼
                  Security analysts

The choice depends on organizational requirements.

For example, an organization may already use:

Splunk
Microsoft Sentinel
Elastic
OpenSearch
another enterprise SIEM

I would avoid sending everything directly to the SIEM if retention costs are high. S3 can act as the durable, lower-cost log archive, with selected logs/findings forwarded to the SIEM for active analysis.
```

```text
10. Retention and lifecycle

I would define retention based on security/compliance requirements.

For example:

0–30 days
    ↓
Frequent access / investigation

30–180 days
    ↓
S3 Standard-IA

180+ days
    ↓
S3 Glacier

After retention period
    ↓
Deletion

The actual periods should come from the organization's compliance and incident-response requirements rather than being arbitrary.
```

```text
11. Encryption

I would use a KMS key owned by the Log Archive/Security account.

Logs
 │
 ▼
S3
 │
 └── SSE-KMS
        │
        ▼
Central KMS key

KMS permissions should be tightly controlled.

The application accounts should not have unrestricted access to the key.
```

```text
12. Important security controls

For the central logging account, I would implement: Account-level , MFA , restricted administrative access,SCPs
separate security roles
least privilege
centralized IAM/SSO
S3
Block Public Access
encryption
versioning
Object Lock where required
restrictive bucket policy
lifecycle policies
access logging/CloudTrail data events

Monitoring
CloudTrail
GuardDuty
Security Hub
Config
CloudWatch
EventBridge
```


```text
A concise answer would be:

"I would create a dedicated Log Archive/Security account within AWS Organizations. I would enable an organization-wide CloudTrail trail and centralize CloudTrail logs into an encrypted S3 bucket in the Log Archive account. VPC Flow Logs, ALB logs, EKS/container logs and security findings would also be centralized depending on the organization's requirements. The logging account would have strict cross-account bucket policies so workload accounts can write logs but cannot delete or modify the centralized archive. I would use KMS for encryption, S3 lifecycle policies and Object Lock where immutable retention is required. For real-time monitoring, I would integrate CloudWatch/EventBridge and security findings with a SIEM such as OpenSearch, Splunk or Sentinel. This gives us centralized visibility, separation of duties, tamper resistance and consistent retention across all AWS accounts."
```

```text
The key architecture to remember
             AWS ORGANIZATION
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Prod A        Prod B       Dev/Test
       │            │            │
       └────────────┼────────────┘
                    │
             CloudTrail
          VPC Flow Logs
             EKS Logs
            ALB Logs
                    │
                    ▼
        ┌─────────────────────┐
        │  LOG ARCHIVE ACCOUNT │
        │                     │
        │   S3 + KMS          │
        │   CloudWatch        │
        │   Security Hub      │
        └──────────┬──────────┘
                   │
                   ▼
             SIEM / SOC
                   │
                   ▼
          Alerts / Investigation

Interview keywords: AWS Organizations → Log Archive Account → Organization CloudTrail → S3 → KMS → cross-account bucket policy → Object Lock → VPC Flow Logs → EKS logs → Security Hub/GuardDuty → SIEM → least privilege/separation of duties.
```
