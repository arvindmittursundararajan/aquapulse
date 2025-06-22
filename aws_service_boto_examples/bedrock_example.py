import boto3
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

def list_bedrock_models():
    """List available Bedrock models"""
    print("Available Bedrock Models:")
    print("-" * 40)
    
    session = create_session()
    bedrock = session.client('bedrock')
    
    try:
        response = bedrock.list_foundation_models()
        
        if response['modelSummaries']:
            for model in response['modelSummaries']:
                print(f"  - {model['modelId']}")
                print(f"    Name: {model['modelName']}")
                print(f"    Provider: {model['providerName']}")
                print(f"    Input Modalities: {model['inputModalities']}")
                print(f"    Output Modalities: {model['outputModalities']}")
                print()
            return response['modelSummaries']
        else:
            print("  No models found.")
            return []
            
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def invoke_bedrock_model(prompt, model_id='anthropic.claude-3-sonnet-20240229-v1:0'):
    """Invoke a Bedrock model with a prompt"""
    print(f"\nInvoking Bedrock model: {model_id}")
    print(f"Prompt: '{prompt}'")
    
    session = create_session()
    bedrock = session.client('bedrock-runtime')
    
    try:
        # Prepare the request body based on model
        if 'claude' in model_id.lower():
            # Claude format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        elif 'llama' in model_id.lower():
            # Llama format
            body = {
                "prompt": prompt,
                "max_gen_len": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        elif 'titan' in model_id.lower():
            # Titan format
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        else:
            # Default format
            body = {
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7
            }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(body)
        )
        
        result = response['body'].read().decode()
        print(f"✅ Model response received")
        
        # Parse and display the response
        try:
            result_json = json.loads(result)
            print(f"Response: {json.dumps(result_json, indent=2)}")
        except:
            print(f"Raw response: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error invoking model: {e}")
        return None

def test_different_models():
    """Test different Bedrock models with various prompts"""
    print(f"\n" + "=" * 50)
    print("Testing different Bedrock models...")
    
    test_prompts = [
        "Hello, generate a summary for humanitarian logistics.",
        "Write a short poem about artificial intelligence.",
        "Explain quantum computing in simple terms.",
        "What are the benefits of cloud computing?"
    ]
    
    # Common model IDs (these may need to be updated based on availability)
    model_ids = [
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-haiku-20240307-v1:0',
        'meta.llama2-13b-chat-v1',
        'amazon.titan-text-express-v1'
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: {prompt}")
        
        # Try different models
        for model_id in model_ids:
            try:
                result = invoke_bedrock_model(prompt, model_id)
                if result:
                    print(f"✅ Success with {model_id}")
                    break
                else:
                    print(f"❌ Failed with {model_id}")
            except Exception as e:
                print(f"❌ Error with {model_id}: {e}")
                continue
        
        print("-" * 30)

def show_bedrock_info():
    """Show information about Bedrock"""
    print("\nAmazon Bedrock Information:")
    print("-" * 40)
    print("Amazon Bedrock provides access to multiple foundation models.")
    print("\nKey Features:")
    print("  - Access to leading AI models")
    print("  - Serverless inference")
    print("  - Built-in security and privacy")
    print("  - Easy integration with AWS services")
    print("\nAvailable Model Providers:")
    print("  - Anthropic (Claude)")
    print("  - Meta (Llama)")
    print("  - Amazon (Titan)")
    print("  - AI21 (Jurassic)")
    print("  - Cohere (Command)")
    print("\nUse Cases:")
    print("  - Text generation")
    print("  - Question answering")
    print("  - Content summarization")
    print("  - Code generation")
    print("  - Creative writing")

def main():
    print("🚀 Amazon Bedrock - Generative AI")
    print("=" * 50)
    
    # Show Bedrock information
    show_bedrock_info()
    
    # List available models
    models = list_bedrock_models()
    
    if not models:
        print("\n❌ No models found. Check your AWS credentials and Bedrock access.")
        return
    
    # Test with a simple prompt
    print(f"\n" + "=" * 50)
    print("Testing Bedrock with sample prompts...")
    
    simple_prompt = "Hello, generate a summary for humanitarian logistics."
    result = invoke_bedrock_model(simple_prompt)
    
    if result:
        print(f"\n✅ Bedrock test completed successfully!")
    else:
        print(f"\n❌ Bedrock test failed.")
    
    # Test different models
    test_different_models()
    
    print(f"\n" + "=" * 50)
    print("Bedrock testing completed!")

if __name__ == "__main__":
    main() 