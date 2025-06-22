import boto3
import json
import time
import os

# AWS credentials (using same pattern as other files)
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION', 'us-east-1')

def create_session():
    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

# Initialize clients using the session
session = create_session()
bedrock_runtime = session.client('bedrock-runtime')

# --- CLEANUP LOGIC ---
def cleanup_all_resources():
    print("Starting cleanup of all AWS resources...")
    print("="*60)
    # S3 cleanup
    s3 = session.client('s3')
    bucket_name = 'bedrock-kb-bucket-demo-unique-12345'
    try:
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                print(f"Deleting S3 object: {obj['Key']}")
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        s3.delete_bucket(Bucket=bucket_name)
        print(f"  ✓ Deleted S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"  ✗ Failed to delete S3 bucket {bucket_name}: {e}")
    # IAM cleanup
    iam = session.client('iam')
    role_name = 'BedrockExecutionRole'
    try:
        try:
            iam.detach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess')
            iam.detach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess')
            print(f"  ✓ Detached policies from role: {role_name}")
        except Exception as e:
            print(f"  ✗ Failed to detach policies from role {role_name}: {e}")
        iam.delete_role(RoleName=role_name)
        print(f"  ✓ Deleted IAM role: {role_name}")
    except Exception as e:
        print(f"  ✗ Failed to delete IAM role {role_name}: {e}")
    # Bedrock agent cleanup
    bedrock_agent = session.client('bedrock-agent')
    try:
        agents = bedrock_agent.list_agents()['agentSummaries']
        for agent in agents:
            agent_name = agent['agentName']
            if agent_name == 'DemoAgent':
                agent_id = agent['agentId']
                print(f"Deleting agent: {agent_name} (ID: {agent_id})")
                try:
                    bedrock_agent.delete_agent(agentId=agent_id)
                    print(f"  ✓ Deleted agent: {agent_name}")
                except Exception as e:
                    print(f"  ✗ Failed to delete agent {agent_name}: {e}")
    except Exception as e:
        print(f"Error listing/deleting agents: {e}")
    print("="*60)
    print("Cleanup completed!")

def main():
    cleanup_all_resources()
    print("Invoking Bedrock Claude model as an agent...")
    prompt = "How can hospitals be protected in conflict zones?"
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = response['body'].read().decode()
    try:
        result_json = json.loads(result)
        print("\nAgent response:")
        print(result_json["content"][0]["text"])
    except Exception:
        print("Raw response:")
        print(result)

if __name__ == "__main__":
    main() 