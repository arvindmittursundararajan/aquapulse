import boto3
import uuid
from datetime import datetime
import os

# AWS credentials
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION', 'us-east-1')

def cleanup_s3_resources():
    """Clean up any existing S3 test resources"""
    print("🧹 Cleaning up existing S3 test resources...")
    
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    s3 = session.client('s3')
    
    try:
        # List all buckets
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            if bucket_name.startswith('minimal-bucket-'):
                try:
                    # Delete all objects in bucket
                    objects = s3.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in objects:
                        for obj in objects['Contents']:
                            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    
                    # Delete bucket
                    s3.delete_bucket(Bucket=bucket_name)
                    print(f"   🗑️  Deleted bucket: {bucket_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting bucket {bucket_name}: {e}")
        
        # Clean up local test file
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")
            print("   🗑️  Deleted local test_file.txt")
            
        print("✅ S3 cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during S3 cleanup: {e}")

def main():
    cleanup_s3_resources()
    
    # Create session
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    s3 = session.client('s3')
    
    # Create unique bucket name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    bucket_name = f"minimal-bucket-{timestamp}-{unique_id}"
    
    print(f"Creating bucket: {bucket_name}")
    
    # Create bucket
    s3.create_bucket(Bucket=bucket_name)
    s3.get_waiter('bucket_exists').wait(Bucket=bucket_name)
    print("Bucket created successfully!")
    
    # Create text file
    filename = "test_file.txt"
    content = f"Hello from AWS S3!\nCreated on: {datetime.now()}\nThis is a test file."
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created file: {filename}")
    
    # Upload file
    print(f"Uploading {filename} to s3://{bucket_name}/")
    s3.upload_file(filename, bucket_name, filename)
    print("Upload successful!")
    
    # Confirm upload
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"Found in bucket: {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("No objects found in bucket")
    
    # Clean up local file
    os.remove(filename)
    print(f"Cleaned up local file: {filename}")
    
    print(f"\nBucket URL: s3://{bucket_name}")
    print(f"File URL: s3://{bucket_name}/{filename}")

if __name__ == "__main__":
    main() 