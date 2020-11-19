import boto3
import json

REGION = 'cn-northwest-1'
# https://docs.aws.amazon.com/whitepapers/latest/cost-optimization-reservation-models/maximizing-utilization-with-size-flexibility-in-regional-reserved-instances.html
'''
 * Limitations for instance size flexibility
Instance size flexibility does not apply to the following Reserved Instances:
 ** Reserved Instances that are purchased for a specific Availability Zone (zonal Reserved Instances)
 ** Reserved Instances with dedicated tenancy
 ** Reserved Instances for Windows Server, Windows Server with SQL Standard, Windows Server with SQL Server Enterprise, Windows Server with SQL Server Web, RHEL, and SUSE Linux Enterprise Server
 ** Reserved Instances for G4 instances.
'''
# Normalization Factor
NF = {
        'nano': 0.25,
        'micro': 0.5,
        'small': 1,
        'medium': 2,
        'large': 4,
        'xlarge': 8,
        '2xlarge': 16,
        '4xlarge': 32,
        '8xlarge': 64,
        '9xlarge': 72,
        '10xlarge': 80,
        '12xlarge': 96,
        '16xlarge': 128,
        '24xlarge': 192,
        '32xlarge': 256
        }
NF_METAL = {
        'a1': 32,
        'c5': 192,
        'c5d': 192,
        'c5n': 144,
        'i3': 128,
        'i3en': 192,
        'm5': 192,
        'm5d': 192,
        'm6g': 128,
        'r5': 192,
        'r5d': 192,
        'z1d': 96
        }


def get_ri_status(client):

    reserved_instances = client.describe_reserved_instances(
            Filters=[ {
                'Name': 'state',
                'Values': [ 'active' ]
                } ]
            )

    ri_sf = {}
    ri_nsf = {}
    for ri in reserved_instances['ReservedInstances']:
        # print ri records
        #print(ri['InstanceCount'], ri['InstanceType'], ri['ProductDescription'], ri['InstanceTenancy'],  ri['Scope'])
        if ri['ProductDescription'] != 'Linux/UNIX' \
                or ri['InstanceTenancy'] != 'default' \
                or ri['Scope'] != 'Region' \
                or ri['InstanceType'].startswith('g4'):
                    # Count of non size flexibility RI
            key = ri['InstanceType'] + '-' + ri['ProductDescription'] + '-' + ri['InstanceTenancy']
            if key in ri_nsf:
                if ri['Scope'] in ri_nsf[key]:
                    ri_nsf[key][ri['Scope']] += ri['InstanceCount']
                else:
                    ri_nsf[key][ri['Scope']] = ri['InstanceCount']
            else:
                ri_nsf[key] = { ri['Scope']: ri['InstanceCount'] }
        else:
            # Normalization Score of size flexibility RI
            ec2_type, ec2_size = ri['InstanceType'].split('.')
            if ec2_size == 'metal':
                if ec2_type in ri_sf:
                    ri_sf[ec2_type] += NF_METAL[ec2_type] * ri['InstanceCount']
                else:
                    ri_sf[ec2_type] = NF_METAL[ec2_type] * ri['InstanceCount']
            else:
                if ec2_type in ri_sf:
                    ri_sf[ec2_type] += NF[ec2_size] * ri['InstanceCount']
                else:
                    ri_sf[ec2_type] = NF[ec2_size] * ri['InstanceCount']

    return [ri_sf, ri_nsf]


def get_ec2_status(client):

    instances = client.describe_instances(
            Filters=[ {
                'Name': 'instance-state-name',
                'Values': [ 'running' ]
                } ]
            )

    ins_cnt = {}
    ins_total = 0
    img_platform = {}
    for grp in instances['Reservations']:
        for ins in grp['Instances']:
            ins_total += 1
            name = ins['InstanceId']
            for tag in ins['Tags']:
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            # lookup platform through AMI
            platform = 'Linux/UNIX'
            if ins['ImageId'] in img_platform:
                # use dict for cache
                platform = img_platform[ins['ImageId']]
            else:
                img = client.describe_images(ImageIds = [ins['ImageId']])
                if img['Images']:
                    platform = img['Images'][0]['PlatformDetails']
                elif 'Platform' in ins:
                    platform = ins['Platform'].capitalize()
                img_platform[ins['ImageId']] = platform
            # print ec2 list
            #print(name, ins['InstanceType'], platform, ins['Placement']['AvailabilityZone'], ins['Placement']['Tenancy'])
            # output by AZ
            key = ins['InstanceType'] + '-' + platform + '-' + ins['Placement']['Tenancy']
            if key in ins_cnt:
                if ins['Placement']['AvailabilityZone'] in ins_cnt[key]:
                    ins_cnt[key][ins['Placement']['AvailabilityZone']] += 1
                else:
                    ins_cnt[key][ins['Placement']['AvailabilityZone']] = 1
            else:
                ins_cnt[key] = { ins['Placement']['AvailabilityZone']: 1 }

    return [ins_cnt, ins_total]


def match_nsf_ri(ri_nsf, ins_cnt):

    print("** Try matching non size flexibility RI:")
    for key in sorted(ri_nsf.keys()):
        if key in ins_cnt:
            for region in sorted(ins_cnt[key].keys()):
                if region in ri_nsf[key]:
                    # matching zonal RI
                    i = min(ri_nsf[key][region], ins_cnt[key][region])
                    ri_nsf[key][region] -= i
                    ins_cnt[key][region] -= i
                    if ri_nsf[key][region] == 0:
                        del ri_nsf[key][region]

                if 'Region' in ri_nsf[key] and ins_cnt[key][region] > 0 :
                    # matching regional RI
                    j = min(ri_nsf[key]['Region'], ins_cnt[key][region])
                    ri_nsf[key]['Region'] -= j
                    ins_cnt[key][region] -= j
                    if ri_nsf[key]['Region'] == 0:
                        del ri_nsf[key]['Region']

                if ins_cnt[key][region] == 0:
                    del ins_cnt[key][region]

            if ri_nsf[key] == {}:
                del ri_nsf[key]
            if ins_cnt[key] == {}:
                del ins_cnt[key]

    return [ri_nsf, ins_cnt]


def match_sf_ri(ri_sf, ins_cnt):

    print("** Try matching size flexibility RI:")
    for key in sorted(ins_cnt.keys()):
        ec2_ins, platform, tenancy = key.split('-')
        if platform != 'Linux/UNIX' \
                or tenancy != 'default' \
                or ec2_ins.startswith('g4'):
                    # non size flexibility instance
            continue
        ec2_type, ec2_size = ec2_ins.split('.')
        if ec2_type in ri_sf:
            for region in sorted(ins_cnt[key].keys()):
                if ec2_size == 'metal':
                    factor = NF_METAL[ec2_type]
                else:
                    factor = NF[ec2_size]

                i = min(ri_sf[ec2_type] // factor, ins_cnt[key][region])
                ri_sf[ec2_type] -= factor * i
                ins_cnt[key][region] -= i

                if ri_sf[ec2_type] == 0:
                    del ri_sf[ec2_type]

                if ins_cnt[key][region] == 0:
                    del ins_cnt[key][region]

            if ins_cnt[key] == {}:
                del ins_cnt[key]

    return [ri_sf, ins_cnt]


def lambda_handler(event, context):

    client = boto3.client('ec2',
            region_name = REGION)

    [ri_sf, ri_nsf] = get_ri_status(client)
    print("* Count of non size flexibility RI:", json.dumps(ri_nsf, indent = 4, sort_keys = True))
    print("* Normalization Score of size flexibility RI:", json.dumps(ri_sf, indent = 4, sort_keys = True))

    [ins_cnt, ins_total] = get_ec2_status(client)
    print("* Count of running EC2 (total:", ins_total, "):", json.dumps(ins_cnt, indent = 4, sort_keys = True))

    [ri_nsf, ins_cnt] = match_nsf_ri(ri_nsf, ins_cnt)
    print("*** Count of unmatched RI:", json.dumps(ri_nsf, indent = 4, sort_keys = True))

    [ri_sf, ins_cnt] = match_sf_ri(ri_nsf, ins_cnt)
    print("*** Normalization Score of unmatched RI:", json.dumps(ri_sf, indent = 4, sort_keys = True))
    print("*** Count of unmatched EC2:", json.dumps(ins_cnt, indent = 4, sort_keys = True))

    return {
        'statusCode': 200
    }

