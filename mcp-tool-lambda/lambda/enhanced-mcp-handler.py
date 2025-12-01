import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EnhancedAWSHandler:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.lambda_client = boto3.client('lambda')
        self.rds = boto3.client('rds')
        self.s3 = boto3.client('s3')
        self.iam = boto3.client('iam')
        self.sts = boto3.client('sts')
        
    def handle_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced handler for AWS operations with Easy/Customize modes"""
        try:
            if tool_name.startswith('create_'):
                return self._handle_create_operation(tool_name, parameters)
            elif tool_name.startswith('manage_'):
                return self._handle_manage_operation(tool_name, parameters)
            elif tool_name.endswith('_read_operations'):
                return self._handle_read_operation(tool_name, parameters)
            elif tool_name == 'comprehensive_aws_query':
                return self._handle_comprehensive_query(parameters)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error in {tool_name}: {str(e)}")
            return {"error": str(e)}
    
    def _handle_create_operation(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource creation with Easy/Customize modes"""
        resource_type = tool_name.replace('create_', '')
        
        if resource_type == 'ec2_instance':
            return self._create_ec2_instance(parameters)
        elif resource_type == 'lambda_function':
            return self._create_lambda_function(parameters)
        elif resource_type == 'rds_database':
            return self._create_rds_database(parameters)
        elif resource_type == 's3_bucket':
            return self._create_s3_bucket(parameters)
        else:
            return {"error": f"Resource type {resource_type} not supported"}
    
    def _create_ec2_instance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create EC2 instance with smart defaults or custom config"""
        mode = parameters.get('mode', 'easy')
        
        if mode == 'easy':
            purpose = parameters.get('purpose', 'general')
            defaults = {
                'web_server': {'InstanceType': 't3.medium', 'ImageId': 'ami-0abcdef1234567890'},
                'database': {'InstanceType': 'm5.large', 'ImageId': 'ami-0abcdef1234567890'},
                'development': {'InstanceType': 't3.small', 'ImageId': 'ami-0abcdef1234567890'},
                'general': {'InstanceType': 't3.micro', 'ImageId': 'ami-0abcdef1234567890'}
            }
            config = defaults.get(purpose, defaults['general'])
        else:
            config = {
                'InstanceType': parameters.get('instance_type', 't3.micro'),
                'ImageId': parameters.get('ami_id', 'ami-0abcdef1234567890')
            }
        
        try:
            response = self.ec2.run_instances(
                MinCount=1,
                MaxCount=1,
                **config,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f"aws-ops-{datetime.now().strftime('%Y%m%d')}"},
                        {'Key': 'CreatedBy', 'Value': 'AWS-Operations-Agent'}
                    ]
                }]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            return {
                "success": True,
                "message": f"✅ Created EC2 instance: {instance_id}",
                "instance_id": instance_id,
                "instance_type": config['InstanceType']
            }
            
        except Exception as e:
            return {"error": f"Failed to create EC2 instance: {str(e)}"}
    
    def _create_lambda_function(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lambda function with auto-generated code"""
        function_name = parameters.get('function_name', f"aws-ops-function-{datetime.now().strftime('%Y%m%d')}")
        purpose = parameters.get('purpose', 'general')
        
        # Generate code based on purpose
        code = self._generate_lambda_code(purpose, parameters)
        
        # Create execution role
        role_arn = self._create_lambda_role(function_name)
        
        try:
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': code.encode()},
                MemorySize=512,
                Timeout=60,
                Tags={'CreatedBy': 'AWS-Operations-Agent'}
            )
            
            return {
                "success": True,
                "message": f"✅ Created Lambda function: {function_name}",
                "function_arn": response['FunctionArn']
            }
            
        except Exception as e:
            return {"error": f"Failed to create Lambda function: {str(e)}"}
    
    def _generate_lambda_code(self, purpose: str, parameters: Dict[str, Any]) -> str:
        """Generate Lambda code based on purpose"""
        templates = {
            'api_endpoint': '''
import json
from datetime import datetime

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'Hello from Lambda API!',
            'timestamp': str(datetime.now())
        })
    }
''',
            'general': '''
import json
from datetime import datetime

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Function executed successfully!',
            'timestamp': str(datetime.now())
        })
    }
'''
        }
        return templates.get(purpose, templates['general'])
    
    def _create_lambda_role(self, function_name: str) -> str:
        """Create IAM role for Lambda function"""
        role_name = f'{function_name}-role'
        account_id = self.sts.get_caller_identity()['Account']
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        try:
            self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            return f'arn:aws:iam::{account_id}:role/{role_name}'
        except:
            return f'arn:aws:iam::{account_id}:role/lambda-execution-role'
    
    def _handle_comprehensive_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive AWS queries"""
        query = parameters.get('query', '')
        
        # Simple query routing based on keywords
        if 'ec2' in query.lower() or 'instance' in query.lower():
            return self._query_ec2_resources(query)
        elif 'lambda' in query.lower() or 'function' in query.lower():
            return self._query_lambda_resources(query)
        else:
            return self._query_general_resources(query)
    
    def _query_ec2_resources(self, query: str) -> Dict[str, Any]:
        """Query EC2 resources"""
        try:
            response = self.ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': str(instance['LaunchTime'])
                    })
            
            return {
                "success": True,
                "message": f"Found {len(instances)} EC2 instances",
                "data": instances
            }
            
        except Exception as e:
            return {"error": f"Failed to query EC2: {str(e)}"}

def lambda_handler(event, context):
    """Main Lambda handler"""
    handler = EnhancedAWSHandler()
    
    try:
        tool_name = event.get('tool_name', '')
        parameters = event.get('parameters', {})
        
        logger.info(f"Processing tool: {tool_name}")
        
        result = handler.handle_request(tool_name, parameters)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }