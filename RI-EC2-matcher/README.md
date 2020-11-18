# RI-EC2-matcher
* script to match the RI and EC2
  * non size flexibility RI: match by Count
  * size flexibility RI: match by Normalization Factor
* IAM policy for running this script
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DescribeInstances",
                "ec2:DescribeReservedInstances"
            ],
            "Resource": "*"
        }
    ]
}
```
* blog: TBD
