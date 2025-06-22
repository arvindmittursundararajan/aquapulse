import boto3
import os
import glob

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

def cleanup_audio_files():
    """Clean up any existing audio files from previous runs"""
    print("🧹 Cleaning up existing audio files...")
    
    # Find all MP3 files that match our pattern
    audio_files = glob.glob("speech_*.mp3")
    
    if audio_files:
        for file in audio_files:
            try:
                os.remove(file)
                print(f"   🗑️  Deleted: {file}")
            except Exception as e:
                print(f"   ⚠️  Error deleting {file}: {e}")
        print(f"✅ Cleaned up {len(audio_files)} audio files")
    else:
        print("✅ No existing audio files found")

def list_voices():
    """List available Polly voices"""
    print("Available Polly Voices:")
    print("-" * 40)
    
    session = create_session()
    polly = session.client('polly')
    
    try:
        response = polly.describe_voices(LanguageCode='en-US')
        
        voices = response['Voices']
        for i, voice in enumerate(voices[:15], 1):  # Show first 15 voices
            print(f"{i:2d}. {voice['Name']} ({voice['Gender']}) - {voice['LanguageName']}")
        
        if len(voices) > 15:
            print(f"... and {len(voices) - 15} more voices")
            
        return voices
        
    except Exception as e:
        print(f"Error listing voices: {e}")
        return []

def text_to_speech(text, voice_id='Joanna', output_file='speech.mp3'):
    """Convert text to speech using Amazon Polly"""
    print(f"\nConverting text to speech...")
    print(f"Text: '{text}'")
    print(f"Voice: {voice_id}")
    print(f"Output: {output_file}")
    
    session = create_session()
    polly = session.client('polly')
    
    try:
        # Synthesize speech
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id
        )
        
        # Save the audio file
        with open(output_file, 'wb') as f:
            f.write(response['AudioStream'].read())
        
        # Get file size
        file_size = os.path.getsize(output_file)
        
        print(f"✅ Successfully created {output_file}")
        print(f"   File size: {file_size} bytes")
        print(f"   Voice: {voice_id}")
        print(f"   Format: MP3")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Amazon Polly - Text to Speech")
    print("=" * 50)
    
    # List available voices
    voices = list_voices()
    
    if not voices:
        print("❌ Failed to get voices. Check your AWS credentials.")
        return
    
    # Test with different voices
    test_texts = [
        "Hello from AWS Polly! This is a test of text to speech conversion.",
        "Welcome to the world of artificial intelligence and cloud computing.",
        "Amazon Polly makes it easy to add natural-sounding speech to your applications."
    ]
    
    voice_options = ['Joanna', 'Kevin', 'Salli', 'Matthew', 'Ivy']
    
    print(f"\n" + "=" * 50)
    print("Testing Text-to-Speech with different voices:")
    
    for i, (text, voice) in enumerate(zip(test_texts, voice_options), 1):
        output_file = f"speech_{i}_{voice.lower()}.mp3"
        success = text_to_speech(text, voice, output_file)
        
        if success:
            print(f"✅ Test {i} completed: {output_file}")
        else:
            print(f"❌ Test {i} failed")
        
        print("-" * 30)
    
    print("\n🎉 Polly testing completed!")
    print("Generated files:")
    for i, voice in enumerate(voice_options, 1):
        filename = f"speech_{i}_{voice.lower()}.mp3"
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  - {filename} ({size} bytes)")

if __name__ == "__main__":
    cleanup_audio_files()
    main() 