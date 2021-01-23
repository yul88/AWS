import boto3
import csv
import io
import json
import os
import prettytable
import sqlite3
import zipfile

BUCKET = 'your-billing-report-bucket'
KEY = 'account-aws-billing-detailed-line-items-with-resources-and-tags-ACTS-region-yyyy-mm.csv.zip'
TMP = '/tmp/'
MY_SNS_TOPIC_ARN = 'arn:aws:sns:region:account:topic'

def lambda_handler(event, context):

	if os.path.exists(TMP + 'bill.db'):
		os.remove(TMP + 'bill.db')

	s3_resource = boto3.resource('s3')
	zip_obj = s3_resource.Object(bucket_name = BUCKET, key = KEY)

	conn = sqlite3.connect(TMP + 'bill.db')
	cur = conn.cursor()
	cur.executescript("""
		CREATE TABLE IF NOT EXISTS dbr(
			InvoiceID INTEGER,
			PayerAccountId INTEGER,
			LinkedAccountId INTEGER,
			RecordType TEXT,
			RecordId INTEGER,
			ProductName TEXT,
			RateId INTEGER,
			SubscriptionId INTEGER,
			PricingPlanId INTEGER,
			UsageType TEXT,
			Operation TEXT,
			AvailabilityZone TEXT,
			ReservedInstance TEXT,
			ItemDescription TEXT,
			UsageStartDate TEXT,
			UsageEndDate TEXT,
			UsageQuantity NUMERIC,
			BlendedRate NUMERIC,
			BlendedCost NUMERIC,
			UnBlendedRate NUMERIC,
			UnBlendedCost NUMERIC,
			ResourceId TEXT,
			'user:Environment' TEXT,
			'user:Name' TEXT,
			'user:application' TEXT,
			'user:department' TEXT,
			'user:project' TEXT
		);
		DELETE FROM dbr;
	""")
	conn.commit()

	buffer = io.BytesIO(zip_obj.get()["Body"].read())
	z = zipfile.ZipFile(buffer)
	for filename in z.namelist():
		reader = csv.reader(io.TextIOWrapper(z.open(filename)))
		header = next(reader)
		cur.executemany("INSERT INTO dbr VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", reader)
		conn.commit()

	cur.execute('select "user:department" as Department, round(sum(UnBlendedCost), 2) as Cost from dbr where RecordType = "LineItem" group by Department having Cost > 0 order by Cost desc;')

	str = "* Department View\n"
	x1 = prettytable.from_db_cursor(cur)
	x1.align = "l"
	x1.align["Cost"] = "r"
	str += x1.get_string()

	cur.execute('select ProductName, round(sum(UnBlendedCost), 2) as Cost from dbr where RecordType = "LineItem" group by ProductName having Cost > 0 order by Cost desc;')

	str += "\n\n* ProductName View\n"
	x2 = prettytable.from_db_cursor(cur)
	x2.align = "l"
	x2.align["Cost"] = "r"
	str += x2.get_string()

	cur.execute('select "user:department" as Department, ProductName, "user:Name" as Name, UsageType, cast(round(sum(UsageQuantity)) as int) as Quantity, cast(round(sum(UnBlendedCost)) as int) as Cost from dbr where RecordType = "LineItem" group by Department, ProductName, Name, UsageType having Cost > 100 order by Department, ProductName, Name, UsageType;')

	str += "\n\n* Department-ProductName-Name-UsageType View (filter: Cost>100)\n"
	x3 = prettytable.from_db_cursor(cur)
	x3.align = "l"
	x3.align["Cost"] = "r"
	str += x3.get_string()

	conn.close()

	sns_client = boto3.client('sns')
	sns_client.publish(
		TopicArn = MY_SNS_TOPIC_ARN,
		Subject = 'AWS DBR',
		Message = str
	)

	return {
		'statusCode': 200,
		'body': 'Finished'
	}

