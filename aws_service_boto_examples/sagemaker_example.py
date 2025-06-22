import boto3
import json
import time
import os
import uuid
from datetime import datetime

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

def cleanup_existing_sagemaker_resources():
    """Clean up all existing SageMaker resources before starting"""
    print("🧹 Cleaning up existing SageMaker resources...")
    
    session = create_session()
    sagemaker = session.client('sagemaker')
    iam = session.client('iam')
    
    resources_cleaned = []
    
    try:
        # 1. Delete all endpoints
        print("1. Cleaning up endpoints...")
        response = sagemaker.list_endpoints(MaxResults=100)
        endpoints = response.get('Endpoints', [])
        for endpoint in endpoints:
            endpoint_name = endpoint['EndpointName']
            try:
                if endpoint['EndpointStatus'] not in ['Deleting', 'Failed']:
                    sagemaker.delete_endpoint(EndpointName=endpoint_name)
                    print(f"   🗑️  Deleted endpoint: {endpoint_name}")
                    resources_cleaned.append(f"endpoint:{endpoint_name}")
                else:
                    print(f"   ⚠️  Endpoint {endpoint_name} is in {endpoint['EndpointStatus']} state, skipping")
            except Exception as e:
                print(f"   ⚠️  Error deleting endpoint {endpoint_name}: {e}")
        
        # 2. Delete all endpoint configurations
        print("2. Cleaning up endpoint configurations...")
        response = sagemaker.list_endpoint_configs(MaxResults=100)
        configs = response.get('EndpointConfigs', [])
        for config in configs:
            config_name = config['EndpointConfigName']
            try:
                sagemaker.delete_endpoint_config(EndpointConfigName=config_name)
                print(f"   🗑️  Deleted endpoint config: {config_name}")
                resources_cleaned.append(f"endpoint_config:{config_name}")
            except Exception as e:
                print(f"   ⚠️  Error deleting endpoint config {config_name}: {e}")
        
        # 3. Delete all models
        print("3. Cleaning up models...")
        response = sagemaker.list_models(MaxResults=100)
        models = response.get('Models', [])
        for model in models:
            model_name = model['ModelName']
            try:
                sagemaker.delete_model(ModelName=model_name)
                print(f"   🗑️  Deleted model: {model_name}")
                resources_cleaned.append(f"model:{model_name}")
            except Exception as e:
                print(f"   ⚠️  Error deleting model {model_name}: {e}")
        
        # 4. Delete all notebook instances
        print("4. Cleaning up notebook instances...")
        response = sagemaker.list_notebook_instances(MaxResults=100)
        notebooks = response.get('NotebookInstances', [])
        for notebook in notebooks:
            notebook_name = notebook['NotebookInstanceName']
            try:
                if notebook['NotebookInstanceStatus'] not in ['Deleting', 'Failed']:
                    sagemaker.delete_notebook_instance(NotebookInstanceName=notebook_name)
                    print(f"   🗑️  Deleted notebook instance: {notebook_name}")
                    resources_cleaned.append(f"notebook:{notebook_name}")
                else:
                    print(f"   ⚠️  Notebook {notebook_name} is in {notebook['NotebookInstanceStatus']} state, skipping")
            except Exception as e:
                print(f"   ⚠️  Error deleting notebook instance {notebook_name}: {e}")
        
        # 5. Delete all training jobs (if any are still running)
        print("5. Checking training jobs...")
        response = sagemaker.list_training_jobs(MaxResults=100)
        jobs = response.get('TrainingJobSummaries', [])
        for job in jobs:
            job_name = job['TrainingJobName']
            status = job['TrainingJobStatus']
            if status in ['InProgress', 'Stopping']:
                try:
                    sagemaker.stop_training_job(TrainingJobName=job_name)
                    print(f"   🛑 Stopped training job: {job_name}")
                    resources_cleaned.append(f"training_job:{job_name}")
                except Exception as e:
                    print(f"   ⚠️  Error stopping training job {job_name}: {e}")
            else:
                print(f"   ℹ️  Training job {job_name} is in {status} state")
        
        # 6. Clean up SageMaker IAM roles
        print("6. Cleaning up SageMaker IAM roles...")
        response = iam.list_roles()
        roles = response.get('Roles', [])
        for role in roles:
            role_name = role['RoleName']
            if 'SageMaker' in role_name or 'sagemaker' in role_name.lower():
                try:
                    # Delete inline policies first
                    policies = iam.list_role_policies(RoleName=role_name)
                    for policy in policies['PolicyNames']:
                        iam.delete_role_policy(RoleName=role_name, PolicyName=policy)
                    
                    # Delete the role
                    iam.delete_role(RoleName=role_name)
                    print(f"   🗑️  Deleted IAM role: {role_name}")
                    resources_cleaned.append(f"iam_role:{role_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting IAM role {role_name}: {e}")
        
        # 7. Clean up S3 buckets with SageMaker in the name
        print("7. Cleaning up SageMaker S3 buckets...")
        s3 = session.client('s3')
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
        for bucket in buckets:
            bucket_name = bucket['Name']
            if 'sagemaker' in bucket_name.lower():
                try:
                    # Delete all objects in bucket
                    objects = s3.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in objects:
                        for obj in objects['Contents']:
                            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    
                    # Delete bucket
                    s3.delete_bucket(Bucket=bucket_name)
                    print(f"   🗑️  Deleted S3 bucket: {bucket_name}")
                    resources_cleaned.append(f"s3_bucket:{bucket_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting S3 bucket {bucket_name}: {e}")
        
        if resources_cleaned:
            print(f"\n✅ Cleanup completed! Deleted {len(resources_cleaned)} resources:")
            for resource in resources_cleaned:
                print(f"   - {resource}")
        else:
            print("\n✅ No existing SageMaker resources found to clean up.")
        
        # Wait a moment for deletions to complete
        print("⏳ Waiting for cleanup to complete...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def create_s3_bucket():
    """Create an S3 bucket for SageMaker artifacts"""
    print("Creating S3 bucket for SageMaker artifacts...")
    
    session = create_session()
    s3 = session.client('s3')
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    bucket_name = f"sagemaker-ultra-{timestamp}-{unique_id}"
    
    try:
        s3.create_bucket(Bucket=bucket_name)
        s3.get_waiter('bucket_exists').wait(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return None

def create_sagemaker_role():
    """Create a SageMaker execution role with proper permissions"""
    print(f"\nCreating SageMaker execution role...")
    
    session = create_session()
    iam = session.client('iam')
    
    # Generate unique role name
    timestamp = int(time.time())
    role_name = f"SageMakerExecutionRole-{timestamp}"
    
    # Trust policy for SageMaker
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sagemaker.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Permission policy for SageMaker
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::*",
                    "arn:aws:s3:::*/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }
    
    try:
        # Create the role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="SageMaker execution role for demo"
        )
        
        role_arn = response['Role']['Arn']
        print(f"✅ Created role: {role_name}")
        
        # Attach the permission policy
        policy_name = f"SageMakerPolicy-{timestamp}"
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permission_policy)
        )
        
        print(f"✅ Attached permissions to role")
        
        # Wait a moment for the role to propagate
        print("⏳ Waiting for role to propagate...")
        time.sleep(15)
        
        return role_arn, role_name, policy_name
        
    except Exception as e:
        print(f"❌ Error creating SageMaker role: {e}")
        return None, None, None

def create_training_data(bucket_name):
    """Create sample training data for demonstration"""
    print(f"\nCreating sample training data...")
    
    session = create_session()
    s3 = session.client('s3')
    
    # Create sample data for a simple classification task
    training_data = """label,feature1,feature2,feature3
0,1.2,3.4,5.6
1,2.3,4.5,6.7
0,0.8,2.1,4.3
1,3.1,5.2,7.8
0,1.5,3.7,5.9
1,2.8,4.9,7.1
0,0.9,2.3,4.5
1,3.2,5.4,7.6
0,1.1,3.3,5.5
1,2.5,4.7,6.9"""
    
    # Save locally and upload to S3
    local_file = "training_data.csv"
    with open(local_file, 'w') as f:
        f.write(training_data)
    
    try:
        s3.upload_file(local_file, bucket_name, "data/training_data.csv")
        print(f"✅ Uploaded training data to s3://{bucket_name}/data/training_data.csv")
        
        # Clean up local file
        os.remove(local_file)
        
        return f"s3://{bucket_name}/data/training_data.csv"
        
    except Exception as e:
        print(f"❌ Error uploading training data: {e}")
        return None

def list_sagemaker_algorithms():
    """List available SageMaker algorithms"""
    print(f"\nListing available SageMaker algorithms...")
    
    session = create_session()
    sagemaker = session.client('sagemaker')
    
    try:
        response = sagemaker.list_algorithms()
        algorithms = response.get('AlgorithmSummaryList', [])
        
        print(f"✅ Found {len(algorithms)} algorithms:")
        for i, algo in enumerate(algorithms[:5], 1):  # Show first 5
            print(f"  {i}. {algo.get('AlgorithmName', 'Unknown')}")
            print(f"     Description: {algo.get('AlgorithmDescription', 'No description')[:100]}...")
        
        return algorithms
        
    except Exception as e:
        print(f"❌ Error listing algorithms: {e}")
        return []

def test_sagemaker_basic_operations():
    """Test basic SageMaker operations without creating resources"""
    print(f"\nTesting basic SageMaker operations...")
    
    session = create_session()
    sagemaker = session.client('sagemaker')
    
    try:
        # Test 1: List training jobs
        print("1. Listing training jobs...")
        response = sagemaker.list_training_jobs(MaxResults=5)
        jobs = response.get('TrainingJobSummaries', [])
        print(f"   Found {len(jobs)} training jobs")
        
        # Test 2: List models
        print("2. Listing models...")
        response = sagemaker.list_models(MaxResults=5)
        models = response.get('Models', [])
        print(f"   Found {len(models)} models")
        
        # Test 3: List endpoints
        print("3. Listing endpoints...")
        response = sagemaker.list_endpoints(MaxResults=5)
        endpoints = response.get('Endpoints', [])
        print(f"   Found {len(endpoints)} endpoints")
        
        # Test 4: List notebook instances
        print("4. Listing notebook instances...")
        response = sagemaker.list_notebook_instances(MaxResults=5)
        notebooks = response.get('NotebookInstances', [])
        print(f"   Found {len(notebooks)} notebook instances")
        
        print("✅ All basic SageMaker operations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SageMaker operations: {e}")
        return False

def create_simple_notebook_instance(bucket_name, role_arn):
    """Create a simple notebook instance for demonstration"""
    print(f"\nCreating SageMaker notebook instance...")
    
    session = create_session()
    sagemaker = session.client('sagemaker')
    
    timestamp = int(time.time())
    notebook_name = f"demo-notebook-{timestamp}"
    
    try:
        response = sagemaker.create_notebook_instance(
            NotebookInstanceName=notebook_name,
            InstanceType='ml.t3.medium',
            RoleArn=role_arn,
            DirectInternetAccess='True',
            VolumeSizeInGB=5
        )
        
        print(f"✅ Created notebook instance: {notebook_name}")
        print("⏳ Waiting for notebook instance to be 'InService'...")
        
        # Wait for notebook to be ready
        waiter = sagemaker.get_waiter('notebook_instance_in_service')
        waiter.wait(NotebookInstanceName=notebook_name)
        
        print(f"✅ Notebook instance {notebook_name} is now InService!")
        return notebook_name
        
    except Exception as e:
        print(f"❌ Error creating notebook instance: {e}")
        return None

def safe_delete_notebook_instance(notebook_name):
    """Safely delete notebook instance if it exists"""
    if not notebook_name:
        return
    
    session = create_session()
    sagemaker = session.client('sagemaker')
    
    try:
        # Check if notebook exists and is not already being deleted
        response = sagemaker.describe_notebook_instance(NotebookInstanceName=notebook_name)
        if response['NotebookInstanceStatus'] not in ['Deleting', 'Failed']:
            sagemaker.delete_notebook_instance(NotebookInstanceName=notebook_name)
            print(f"🗑️  Deleted notebook instance: {notebook_name}")
        else:
            print(f"⚠️  Notebook instance {notebook_name} is in {response['NotebookInstanceStatus']} state, skipping deletion")
    except sagemaker.exceptions.ValidationException:
        print(f"⚠️  Notebook instance {notebook_name} does not exist, skipping deletion")
    except Exception as e:
        print(f"⚠️  Error deleting notebook instance {notebook_name}: {e}")

def cleanup_resources(notebook_name, bucket_name, role_arn, role_name, policy_name):
    """Clean up created resources with proper error handling"""
    print(f"\nCleaning up resources...")
    
    session = create_session()
    s3 = session.client('s3')
    iam = session.client('iam')
    
    # Delete notebook instance
    safe_delete_notebook_instance(notebook_name)
    
    # Delete S3 bucket contents and bucket
    if bucket_name:
        try:
            # Delete all objects in bucket
            objects = s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            
            # Delete bucket
            s3.delete_bucket(Bucket=bucket_name)
            print(f"🗑️  Deleted bucket: {bucket_name}")
        except Exception as e:
            print(f"⚠️  Could not delete bucket {bucket_name}: {e}")
    
    # Delete IAM role
    if role_name:
        try:
            # Delete inline policies
            policies = iam.list_role_policies(RoleName=role_name)
            for policy in policies['PolicyNames']:
                iam.delete_role_policy(RoleName=role_name, PolicyName=policy)
            
            # Delete the role
            iam.delete_role(RoleName=role_name)
            print(f"🗑️  Deleted IAM role: {role_name}")
        except Exception as e:
            print(f"⚠️  Could not delete IAM role {role_name}: {e}")

def main():
    print("🚀 Amazon SageMaker - Ultra Simple Demo")
    print("=" * 60)
    
    # Step 0: Clean up existing SageMaker resources
    cleanup_existing_sagemaker_resources()
    
    resources_created = []
    
    try:
        # Step 1: Test basic SageMaker operations
        test_sagemaker_basic_operations()
        
        # Step 2: List available algorithms
        list_sagemaker_algorithms()
        
        # Step 3: Create S3 bucket
        bucket_name = create_s3_bucket()
        if bucket_name:
            resources_created.append(('bucket', bucket_name))
        
        # Step 4: Create SageMaker execution role
        role_arn, role_name, policy_name = create_sagemaker_role()
        if role_arn:
            resources_created.append(('iam_role', role_arn))
        
        # Step 5: Create training data
        training_data_uri = create_training_data(bucket_name)
        
        # Step 6: Create notebook instance (simpler than training jobs)
        if role_arn:
            notebook_name = create_simple_notebook_instance(bucket_name, role_arn)
            if notebook_name:
                resources_created.append(('notebook', notebook_name))
        
        print(f"\n" + "=" * 60)
        print("🎉 SageMaker ultra-simple demo completed successfully!")
        print(f"Created resources:")
        for resource_type, resource_name in resources_created:
            print(f"  - {resource_type}: {resource_name}")
        
        print(f"\n📝 Summary:")
        print(f"  - Cleaned up existing SageMaker resources")
        print(f"  - Tested basic SageMaker operations")
        print(f"  - Listed available algorithms")
        print(f"  - Created S3 bucket for data storage")
        print(f"  - Created IAM role with proper permissions")
        print(f"  - Created training data")
        print(f"  - Created notebook instance for development")
    
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    
    finally:
        # Cleanup
        print(f"\n" + "=" * 60)
        cleanup_choice = input("Do you want to clean up all created resources? (y/n): ").lower()
        if cleanup_choice == 'y':
            cleanup_resources(notebook_name if 'notebook_name' in locals() else None, 
                            bucket_name, role_arn, role_name, policy_name)
        else:
            print("Resources kept for further testing.")

if __name__ == "__main__":
    main() 