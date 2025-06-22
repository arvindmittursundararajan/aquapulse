import boto3
import zipfile
import io
import time
import uuid
from datetime import datetime
import json
import os

# AWS credentials
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION', 'us-east-1')

def create_session():
    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

def cleanup_lambda_resources():
    """Clean up any existing Lambda test resources"""
    print("🧹 Cleaning up existing Lambda test resources...")
    
    session = create_session()
    lambda_client = session.client('lambda')
    iam = session.client('iam')
    
    try:
        # Clean up Lambda functions
        print("1. Cleaning up Lambda functions...")
        response = lambda_client.list_functions(MaxItems=100)
        functions = response.get('Functions', [])
        
        for function in functions:
            function_name = function['FunctionName']
            if function_name.startswith('demo-lambda-') or function_name == 'DemoLambdaFunction':
                try:
                    # Delete function
                    lambda_client.delete_function(FunctionName=function_name)
                    print(f"   🗑️  Deleted Lambda function: {function_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting Lambda function {function_name}: {e}")
        
        # Clean up IAM roles
        print("2. Cleaning up IAM roles...")
        response = iam.list_roles()
        roles = response.get('Roles', [])
        
        for role in roles:
            role_name = role['RoleName']
            if role_name.startswith('LambdaExecutionRole-') or role_name == 'YourLambdaExecutionRole':
                try:
                    # Detach policies first
                    attached_policies = iam.list_attached_role_policies(RoleName=role_name)
                    for policy in attached_policies.get('AttachedPolicies', []):
                        iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
                    
                    # Delete inline policies
                    inline_policies = iam.list_role_policies(RoleName=role_name)
                    for policy_name in inline_policies.get('PolicyNames', []):
                        iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                    
                    # Delete the role
                    iam.delete_role(RoleName=role_name)
                    print(f"   🗑️  Deleted IAM role: {role_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting IAM role {role_name}: {e}")
        
        print("✅ Lambda cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during Lambda cleanup: {e}")

def create_lambda_execution_role():
    """Create IAM role for Lambda execution"""
    print("\nCreating IAM role for Lambda execution...")
    
    session = create_session()
    iam = session.client('iam')
    
    # Generate unique role name
    timestamp = int(time.time())
    role_name = f"LambdaExecutionRole-{timestamp}"
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for Lambda function'
        )
        
        # Attach basic execution policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        print(f"✅ Created IAM role: {role_name}")
        
        # Wait for role propagation
        print("⏳ Waiting for IAM role propagation...")
        time.sleep(10)
        
        return role['Role']['Arn']
        
    except Exception as e:
        print(f"❌ Error creating IAM role: {e}")
        return None

def create_lambda_zip():
    """Create a deployment package (simple hello world)"""
    print("Creating Lambda deployment package...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as z:
        z.writestr('lambda_function.py', """
import json
import time

def lambda_handler(event, context):
    # Get current timestamp
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Create response
    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'Hello from Lambda!',
            'timestamp': current_time,
            'function_name': context.function_name,
            'request_id': context.aws_request_id,
            'event': event
        })
    }
    
    return response
""")
    zip_buffer.seek(0)
    return zip_buffer.read()

def create_lambda_function(function_name, role_arn):
    """Create Lambda function"""
    print(f"Creating Lambda function: {function_name}")
    
    session = create_session()
    lambda_client = session.client('lambda')
    
    zip_bytes = create_lambda_zip()
    
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_bytes},
            Description='Demo Lambda function for testing',
            Timeout=10,
            MemorySize=128,
            Publish=True
        )
        
        print(f"✅ Lambda function created: {response['FunctionArn']}")
        return response
        
    except Exception as e:
        print(f"❌ Error creating Lambda function: {e}")
        return None

def add_invoke_permission(function_name, statement_id, principal):
    """Add invoke permission to Lambda function"""
    print(f"Adding invoke permission for {principal}...")
    
    session = create_session()
    lambda_client = session.client('lambda')
    
    try:
        response = lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal=principal
        )
        
        print(f"✅ Invoke permission added: {response['Statement']}")
        return response
        
    except Exception as e:
        print(f"❌ Error adding invoke permission: {e}")
        return None

def invoke_lambda(function_name):
    """Invoke Lambda function"""
    print(f"Invoking Lambda function: {function_name}")
    
    session = create_session()
    lambda_client = session.client('lambda')
    
    try:
        # Test payload
        test_payload = {
            'message': 'Hello from test client!',
            'timestamp': time.time(),
            'test_data': {
                'user': 'test_user',
                'action': 'invoke_test'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Read and parse response
        payload = response['Payload'].read().decode('utf-8')
        print(f"✅ Lambda response:")
        print(f"   Status Code: {response['StatusCode']}")
        print(f"   Payload: {payload}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error invoking Lambda function: {e}")
        return None

def list_lambda_functions():
    """List existing Lambda functions"""
    print("\nExisting Lambda Functions:")
    print("-" * 40)
    
    session = create_session()
    lambda_client = session.client('lambda')
    
    try:
        response = lambda_client.list_functions(MaxItems=50)
        
        if response['Functions']:
            for function in response['Functions']:
                print(f"  - {function['FunctionName']}")
                print(f"    Runtime: {function['Runtime']}")
                print(f"    Handler: {function['Handler']}")
                print(f"    Memory: {function['MemorySize']} MB")
                print(f"    Timeout: {function['Timeout']} seconds")
                print(f"    Last Modified: {function['LastModified']}")
                print()
            return response['Functions']
        else:
            print("  No Lambda functions found.")
            return []
            
    except Exception as e:
        print(f"Error listing functions: {e}")
        return []

def show_lambda_info():
    """Show information about AWS Lambda"""
    print("\nAWS Lambda Information:")
    print("-" * 40)
    print("AWS Lambda is a serverless compute service that runs your code")
    print("in response to events and automatically manages the underlying compute resources.")
    print("\nKey Features:")
    print("  - Serverless execution")
    print("  - Automatic scaling")
    print("  - Pay-per-use pricing")
    print("  - Event-driven architecture")
    print("  - Multiple runtime support")
    print("\nCommon Use Cases:")
    print("  - API endpoints")
    print("  - Data processing")
    print("  - File processing")
    print("  - Scheduled tasks")
    print("  - Real-time stream processing")

def main():
    print("🚀 AWS Lambda - Serverless Computing")
    print("=" * 50)
    
    # List existing functions
    existing_functions = list_lambda_functions()
    
    # Show Lambda information
    show_lambda_info()
    
    # Create IAM role
    role_arn = create_lambda_execution_role()
    
    if not role_arn:
        print("❌ Failed to create IAM role. Cannot proceed.")
        return
    
    # Create Lambda function
    timestamp = int(time.time())
    function_name = f"demo-lambda-{timestamp}"
    
    create_resp = create_lambda_function(function_name, role_arn)
    
    if not create_resp:
        print("❌ Failed to create Lambda function.")
        return
    
    # Wait for function to be active
    print("⏳ Waiting for function to be active...")
    time.sleep(10)
    
    # Add invoke permission
    add_invoke_permission(function_name, 'AllowAll', 'lambda.amazonaws.com')
    
    # Invoke Lambda function
    print(f"\n" + "=" * 50)
    print("Testing Lambda function...")
    
    invoke_response = invoke_lambda(function_name)
    
    if invoke_response:
        print(f"✅ Lambda test completed successfully!")
    else:
        print(f"❌ Lambda test failed.")
    
    print(f"\n" + "=" * 50)
    print("Lambda testing completed!")

if __name__ == "__main__":
    import json
    cleanup_lambda_resources()
    main() 