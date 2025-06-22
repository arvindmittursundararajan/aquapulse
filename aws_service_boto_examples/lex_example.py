import boto3
import json
import time
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

def list_bots():
    """List existing Lex bots"""
    print("Existing Lex Bots:")
    print("-" * 40)
    
    session = create_session()
    lex_models = session.client('lex-models')
    
    try:
        response = lex_models.get_bots()
        
        if response['bots']:
            for bot in response['bots']:
                print(f"  - {bot['name']} (Version: {bot['version']})")
            return response['bots']
        else:
            print("  No bots found.")
            return []
            
    except Exception as e:
        print(f"Error listing bots: {e}")
        return []

def test_existing_bot(bot_name):
    """Test an existing bot with sample inputs"""
    print(f"\nTesting bot: {bot_name}")
    print("-" * 40)
    
    session = create_session()
    lex = session.client('lex-runtime')
    
    test_inputs = [
        "Hello",
        "Hi there",
        "Good morning",
        "How are you?",
        "What's the weather like?"
    ]
    
    user_id = f"test-user-{int(time.time())}"
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"\nTest {i}: '{input_text}'")
        
        try:
            response = lex.post_text(
                botName=bot_name,
                botAlias="$LATEST",
                userId=user_id,
                inputText=input_text
            )
            
            print(f"  Intent: {response.get('intentName', 'None')}")
            print(f"  Response: {response.get('message', 'No response')}")
            print(f"  Dialog State: {response.get('dialogState', 'None')}")
            
            # Show slots if available
            if 'slots' in response and response['slots']:
                print("  Slots:")
                for slot_name, slot_value in response['slots'].items():
                    if slot_value:
                        print(f"    {slot_name}: {slot_value}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

def show_lex_info():
    """Show information about Lex and how to create bots"""
    print("\nAmazon Lex Information:")
    print("-" * 40)
    print("Lex V1 API is deprecated and new bot creation is disabled.")
    print("To create new bots, use Lex V2:")
    print("\n1. AWS Console: https://console.aws.amazon.com/lexv2/")
    print("2. AWS CLI: aws lexv2-models create-bot")
    print("3. Boto3: lexv2-models.create_bot()")
    print("\nCommon sample bots:")
    print("  - BookTrip (for travel booking)")
    print("  - OrderFlowers (for flower ordering)")
    print("  - ScheduleAppointment (for appointments)")
    print("\nLex V2 Features:")
    print("  - Improved NLU capabilities")
    print("  - Better slot filling")
    print("  - Enhanced conversation flow")
    print("  - Integration with other AWS services")

def main():
    print("🚀 Amazon Lex - Conversational AI")
    print("=" * 50)
    
    # List existing bots
    existing_bots = list_bots()
    
    # If bots exist, test them
    if existing_bots:
        print(f"\nFound {len(existing_bots)} existing bot(s).")
        bot_name = existing_bots[0]['name']
        print(f"Testing bot: {bot_name}")
        test_existing_bot(bot_name)
    else:
        print("\nNo existing bots found.")
        show_lex_info()
    
    print("\n🎉 Lex testing completed!")

if __name__ == "__main__":
    main() 