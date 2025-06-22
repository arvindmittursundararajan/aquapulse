import boto3
import os
import time
import uuid
import glob
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

def cleanup_transcribe_resources():
    """Clean up any existing transcribe test resources"""
    print("🧹 Cleaning up existing transcribe test resources...")
    
    session = create_session()
    transcribe = session.client('transcribe')
    s3 = session.client('s3')
    
    try:
        # Clean up transcription jobs
        print("1. Cleaning up transcription jobs...")
        response = transcribe.list_transcription_jobs(MaxResults=100)
        jobs = response.get('TranscriptionJobSummaries', [])
        
        for job in jobs:
            job_name = job['TranscriptionJobName']
            if job_name.startswith('test-transcription-'):
                try:
                    if job['TranscriptionJobStatus'] in ['IN_PROGRESS', 'QUEUED']:
                        transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                        print(f"   🗑️  Deleted transcription job: {job_name}")
                except Exception as e:
                    print(f"   ⚠️  Error deleting transcription job {job_name}: {e}")
        
        # Clean up S3 buckets
        print("2. Cleaning up S3 buckets...")
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            if bucket_name.startswith('transcribe-audio-'):
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
        
        # Clean up local audio files
        print("3. Cleaning up local audio files...")
        audio_files = glob.glob("test_audio_*.mp3")
        for file in audio_files:
            try:
                os.remove(file)
                print(f"   🗑️  Deleted: {file}")
            except Exception as e:
                print(f"   ⚠️  Error deleting {file}: {e}")
        
        print("✅ Transcribe cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during transcribe cleanup: {e}")

def create_test_audio():
    """Create test audio files using Polly"""
    print("Creating test audio files...")
    
    session = create_session()
    polly = session.client('polly')
    
    test_texts = [
        "Hello, this is a test audio file for Amazon Transcribe. The weather is sunny today.",
        "Welcome to the world of speech recognition. This technology is amazing.",
        "Testing one, two, three. This is a sample audio for transcription testing."
    ]
    
    audio_files = []
    
    for i, text in enumerate(test_texts, 1):
        filename = f"test_audio_{i}.mp3"
        
        try:
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Joanna'
            )
            
            with open(filename, 'wb') as f:
                f.write(response['AudioStream'].read())
            
            file_size = os.path.getsize(filename)
            print(f"✅ Created {filename} ({file_size} bytes)")
            audio_files.append(filename)
            
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    return audio_files

def create_s3_bucket():
    """Create an S3 bucket for audio files"""
    print("\nCreating S3 bucket for audio files...")
    
    session = create_session()
    s3 = session.client('s3')
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    bucket_name = f"transcribe-audio-{timestamp}-{unique_id}"
    
    try:
        s3.create_bucket(Bucket=bucket_name)
        s3.get_waiter('bucket_exists').wait(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return None

def upload_audio_to_s3(bucket_name, audio_files):
    """Upload audio files to S3"""
    print(f"\nUploading audio files to S3 bucket: {bucket_name}")
    
    session = create_session()
    s3 = session.client('s3')
    
    uploaded_files = []
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            try:
                s3.upload_file(audio_file, bucket_name, audio_file)
                s3_uri = f"s3://{bucket_name}/{audio_file}"
                uploaded_files.append(s3_uri)
                print(f"✅ Uploaded {audio_file} -> {s3_uri}")
                
            except Exception as e:
                print(f"❌ Error uploading {audio_file}: {e}")
    
    return uploaded_files

def transcribe_audio(s3_uri, job_name, bucket_name):
    """Start transcription job for audio file"""
    print(f"\nStarting transcription for: {s3_uri}")
    
    session = create_session()
    transcribe = session.client('transcribe')
    
    try:
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=bucket_name  # Store results in same bucket
        )
        
        print(f"✅ Transcription job started: {job_name}")
        print(f"   Status: {response['TranscriptionJob']['TranscriptionJobStatus']}")
        
        return job_name
        
    except Exception as e:
        print(f"❌ Error starting transcription: {e}")
        return None

def wait_for_transcription(job_name, max_wait=60):
    """Wait for transcription job to complete"""
    print(f"\nWaiting for transcription job to complete...")
    
    session = create_session()
    transcribe = session.client('transcribe')
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            print(f"   Status: {status}")
            
            if status == 'COMPLETED':
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                print(f"✅ Transcription completed!")
                print(f"   Results: {transcript_uri}")
                return transcript_uri
                
            elif status == 'FAILED':
                print(f"❌ Transcription failed: {response['TranscriptionJob'].get('FailureReason', 'Unknown error')}")
                return None
            
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return None
    
    print(f"❌ Transcription timed out after {max_wait} seconds")
    return None

def get_transcription_results(transcript_uri):
    """Get transcription results from S3"""
    print(f"\nGetting transcription results...")
    
    session = create_session()
    s3 = session.client('s3')
    
    try:
        # Extract bucket and key from URI
        # transcript_uri format: https://s3.us-east-1.amazonaws.com/bucket-name/key
        # or: https://s3.amazonaws.com/bucket-name/key
        
        # Remove the protocol and domain
        if 's3.us-east-1.amazonaws.com' in transcript_uri:
            # Format: https://s3.us-east-1.amazonaws.com/bucket-name/key
            uri_without_domain = transcript_uri.replace('https://s3.us-east-1.amazonaws.com/', '')
        elif 's3.amazonaws.com' in transcript_uri:
            # Format: https://s3.amazonaws.com/bucket-name/key
            uri_without_domain = transcript_uri.replace('https://s3.amazonaws.com/', '')
        else:
            print(f"❌ Unsupported URI format: {transcript_uri}")
            return None
        
        # Split into bucket and key
        parts = uri_without_domain.split('/', 1)
        if len(parts) != 2:
            print(f"❌ Invalid URI format: {transcript_uri}")
            return None
            
        bucket = parts[0]
        key = parts[1]
        
        print(f"   Bucket: {bucket}")
        print(f"   Key: {key}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        transcript_data = response['Body'].read().decode('utf-8')
        
        # Parse JSON response
        import json
        transcript_json = json.loads(transcript_data)
        transcript_text = transcript_json['results']['transcripts'][0]['transcript']
        
        print(f"✅ Transcription text: '{transcript_text}'")
        return transcript_text
        
    except Exception as e:
        print(f"❌ Error getting results: {e}")
        return None

def list_transcription_jobs():
    """List recent transcription jobs"""
    print("\nRecent Transcription Jobs:")
    print("-" * 40)
    
    session = create_session()
    transcribe = session.client('transcribe')
    
    try:
        response = transcribe.list_transcription_jobs(MaxResults=10)
        
        if response['TranscriptionJobSummaries']:
            for job in response['TranscriptionJobSummaries']:
                print(f"  - {job['TranscriptionJobName']} ({job['TranscriptionJobStatus']})")
                if 'CompletionTime' in job:
                    print(f"    Completed: {job['CompletionTime']}")
        else:
            print("  No transcription jobs found.")
            
    except Exception as e:
        print(f"Error listing jobs: {e}")

def main():
    print("🚀 Amazon Transcribe - Speech to Text")
    print("=" * 50)
    
    # Create test audio files
    audio_files = create_test_audio()
    
    if not audio_files:
        print("❌ Failed to create test audio files.")
        return
    
    # Create S3 bucket
    bucket_name = create_s3_bucket()
    
    if not bucket_name:
        print("❌ Failed to create S3 bucket.")
        return
    
    # Upload audio files to S3
    s3_uris = upload_audio_to_s3(bucket_name, audio_files)
    
    if not s3_uris:
        print("❌ Failed to upload audio files to S3.")
        return
    
    # Transcribe each audio file
    print(f"\n" + "=" * 50)
    print("Starting transcription jobs...")
    
    for i, s3_uri in enumerate(s3_uris, 1):
        job_name = f"test-transcription-{int(time.time())}-{i}"
        
        # Start transcription
        job_name = transcribe_audio(s3_uri, job_name, bucket_name)
        
        if job_name:
            # Wait for completion
            transcript_uri = wait_for_transcription(job_name)
            
            if transcript_uri:
                # Get results
                transcript_text = get_transcription_results(transcript_uri)
                if transcript_text:
                    print(f"\n📝 Transcription {i} Results:")
                    print(f"   Text: {transcript_text}")
        
        print("-" * 30)
    
    print(f"\n" + "=" * 50)
    print("Transcribe testing completed!")

if __name__ == "__main__":
    cleanup_transcribe_resources()
    main() 