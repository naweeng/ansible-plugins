#!/usr/bin/python
import boto.ec2

# Get Security Group Name if you have security group id and region.
def get_sg_name(region,NatSgId):
    if region == '':
        raise Exception("region value can't be empty")
    elif NatSgId == '':
        raise Exception("NatSgId value can't be empty")
    else:
        conn = boto.ec2.connect_to_region(region)
        rs = conn.get_all_security_groups()

        for i in rs:
            if i.id == NatSgId:
                return i.name

# Get the private ip of an instance if you have the instance name and region.
def get_instance_private_ip(region,instance_name):
    conn = boto.ec2.connect_to_region(region)
    reservations = conn.get_all_instances(filters={"tag:Name" : instance_name})
    instances = [i for r in reservations for i in r.instances]
    ip_addr = instances[0].private_ip_address
    return ip_addr

# Get the elastic Ip of an instance if you have the instance name and region.
def get_instance_elastic_ip(region,instance_name):
    conn = boto.ec2.connect_to_region(region)
    reservations = conn.get_all_instances(filters={"tag:Name" : instance_name})
    instances = [i for r in reservations for i in r.instances]
    instance_id = instances[0].id
    address = conn.get_all_addresses()
    for addr in address:
	    if addr.instance_id == instance_id:
            return addr.public_ip

# Get the starttime for an existing pipeline.
def fetch_starttime(region,pipelineName):
    conn = boto.datapipeline.connect_to_region(region)
    pipelineId = False
    pipelines = conn.list_pipelines()
    pipelinelist = pipelines['pipelineIdList']
    for p in pipelinelist:
        if p['name'] == pipelineName:
            pipelineId = p['id']

    object_id = ['Schedule']
    if not pipelineId:
        return False
    else:
        result = conn.describe_objects(object_id, pipelineId)
    	objectsList = result['pipelineObjects'][0]['fields']
    	refinedObjectList = filter(lambda objects: objects['key'] == 'startDateTime', objectsList)
    	for o in refinedObjectList:
    		return o['stringValue']

# Create a S3 lifecycle expiry rule
# Example for prefix : '/backup-script/*/*.sql'
def s3_expiration(region,bucket_name,days,prefix,rule_name):
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)

    expiry = Expiration(days=days)
    rule = Rule(rule_name, prefix, 'Enabled', expiration=expiry)
    lifecycle = Lifecycle()
    lifecycle.append(rule)

    output = bucket.configure_lifecycle(lifecycle)
    return output

def get_stopped_instances(aws_region):
    stopped_instance_list = []
    try:
        ec2 = boto3.resource('ec2', region_name=aws_region)
        instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
        for instance in instances:
            stopped_instance_list.append(instance.id)
    except Exception as e:
        print (e)
    return stopped_instance_list

def get_running_ips(aws_region):
    ##### Get all regions
    ec2 = boto3.client('ec2', region_name='us-east-1')
    regionList = []
    response = ec2.describe_regions()
    regions = response['Regions']
    for r in regions:
        regionList.append(r['RegionName'])

    ##### Get running IPs for all regions
    running_ips = []
    for region in regionList:
        ec2 = boto3.client('ec2', region_name=region)
        reservations = ec2.describe_instances()['Reservations']
        for reservation in reservations:
            for instance in reservation['Instances']:
                try:
                    if instance['State']['Name'] == 'running':
                        if 'VpcId' in instance:
                            running_ips.append(instance['PrivateIpAddress'])
                        else:
                            running_ips.append(instance['PublicIpAddress'])
                except:
                        pass

    return running_ips

class FilterModule(object):
    def filters(self):
        return {
            "get_sg_name": get_sg_name,
            "get_instance_private_ip": get_instance_private_ip,
            "get_instance_elastic_ip": get_instance_elastic_ip,
            "fetch_starttime": fetch_starttime,
            "s3_expiration": s3_expiration,
	    "get_stopped_instances": get_stopped_instances,
	    "get_running_ips": get_running_ips
        }
