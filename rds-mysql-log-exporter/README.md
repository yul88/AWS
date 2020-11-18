# rds-mysql-log-exporter
* Lambda to export RDS mysql logs to S3
* IAM policy for this lambda function
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBLogFiles",
                "rds:DownloadDBLogFilePortion"
            ],
            "Resource": "*"
        }
    ]
}
```
* Blog: https://aws.amazon.com/cn/blogs/china/log-management-of-rds-mysql/
