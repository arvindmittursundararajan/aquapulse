import boto3
import os
import time
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

def cleanup_rekognition_resources(bucket_name, image_name):
    print("🧹 Cleaning up Rekognition test resources...")
    session = create_session()
    s3 = session.client('s3')
    try:
        # Delete image from bucket
        s3.delete_object(Bucket=bucket_name, Key=image_name)
        print(f"   🗑️  Deleted {image_name} from {bucket_name}")
    except Exception as e:
        print(f"   ⚠️  Error deleting {image_name} from {bucket_name}: {e}")
    try:
        s3.delete_bucket(Bucket=bucket_name)
        print(f"   🗑️  Deleted bucket: {bucket_name}")
    except Exception as e:
        print(f"   ⚠️  Error deleting bucket {bucket_name}: {e}")
    print("✅ Rekognition cleanup completed")

def upload_image_to_s3(bucket_name, image_name, local_path):
    session = create_session()
    s3 = session.client('s3')
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
    except Exception as e:
        if 'BucketAlreadyOwnedByYou' in str(e):
            print(f"ℹ️  Bucket {bucket_name} already exists.")
        else:
            print(f"❌ Error creating bucket: {e}")
            return False
    try:
        s3.upload_file(local_path, bucket_name, image_name)
        print(f"✅ Uploaded {local_path} to s3://{bucket_name}/{image_name}")
        return True
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return False

def detect_faces(bucket, photo):
    session = create_session()
    rekognition = session.client('rekognition')
    try:
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
            Attributes=['ALL']
        )
        print(f"Detected {len(response['FaceDetails'])} faces in {photo}")
        for i, face in enumerate(response['FaceDetails']):
            print(f"Face {i+1}:")
            print(f"  Confidence: {face['Confidence']:.2f}%")
            print(f"  Emotions: {[e['Type'] for e in face.get('Emotions', []) if e['Confidence'] > 50]}")
            print(f"  Gender: {face['Gender']['Value']} ({face['Gender']['Confidence']:.2f}%)")
            print(f"  Age Range: {face['AgeRange']['Low']} - {face['AgeRange']['High']}")
    except Exception as e:
        print(f"❌ Error detecting faces: {e}")

def main():
    print("🚀 Amazon Rekognition - Face Detection Demo")
    print("=" * 50)
    
    # Test bucket and image
    timestamp = int(time.time())
    bucket_name = f"rekognition-demo-bucket-{timestamp}"
    image_name = "anorak.png"
    local_image_path = "anorak.png"
    
    # Cleanup before test
    cleanup_rekognition_resources(bucket_name, image_name)
    
    # Upload image to S3
    if not os.path.exists(local_image_path):
        print(f"❌ Local image {local_image_path} not found. Please add it to the project directory.")
        return
    if not upload_image_to_s3(bucket_name, image_name, local_image_path):
        print("❌ Failed to upload image. Aborting test.")
        return
    
    # Detect faces
    print("\nDetecting faces in image...")
    detect_faces(bucket_name, image_name)
    
    # Cleanup after test
    cleanup_rekognition_resources(bucket_name, image_name)
    print("\n🎉 Rekognition face detection test completed!")

if __name__ == "__main__":
    main() 