import json
import os
import boto3
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrockConverse
from dotenv import load_dotenv
from pathlib import Path

from typing import Generator, Optional

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def create_llm_model(model_name: str, **kwargs):
    """Create a language model based on the selected provider."""
        # Initialize Bedrock client
    _bedrock = boto3.client(
        'bedrock-runtime',
        region_name="us-east-1",
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('SECRET_KEY'),
    )

    return ChatBedrockConverse(
        client=_bedrock,
        model_id=model_name,
        **kwargs
    )
    

def get_response(prompt: str, llm_provider: str):
    """Get a response from the LLM using the standard LangChain interface."""
    try:
        # Create the LLM instance dynamically
        llm = create_llm_model(llm_provider)

        # Wrap prompt in a HumanMessage
        message = HumanMessage(content=prompt)

        # Invoke model and return the output content
        response = llm.invoke([message])
        return response.content

    except Exception as e:
        return f"Error during LLM invocation: {str(e)}"

def get_response_stream(
    prompt: str,
    model_name: str,
    system: Optional[str] = '',
    temperature: float = 1.0,
    max_tokens: int = 4096,
    **kwargs,
    ):
    """
    Get a streaming response from the selected LLM provider.
    All provider-specific connection/auth should be handled via kwargs.
    """
    try:
        # Add streaming and generation params to kwargs
        kwargs.update({
            "temperature": temperature,
            "max_tokens": max_tokens
        })

        # Create the LLM with streaming enabled
        llm = create_llm_model(model_name, **kwargs)

        # Compose messages
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        # Stream the response
        

        for chunk in llm.stream(messages):
            if chunk and hasattr(chunk, 'content'):
                for i in chunk.content:
                    # print(f"Streaming chunk: {i["text"] if 'text' in i else ""}", flush=True)
                    yield i["text"] if 'text' in i else ""

        
    
    except Exception as e:
        print(f"Error during streaming: {str(e)}", flush=True)
        
def retrieve_and_generate_stream(user_query: str, model_name: str) -> Generator[str, None, None]:
    """
    Example streaming wrapper that yields text chunks from the streaming API.
    Note: boto3 streaming method names vary by version: check for retrieve_and_generate_stream.
    """
    bedrock_agent = boto3.client("bedrock-agent-runtime", 
                                region_name="us-east-1",         
                                aws_access_key_id=os.getenv('ACCESS_KEY'),
                                aws_secret_access_key=os.getenv('SECRET_KEY'),)
# bedrock-runtime client is still used for model-only calls; agent-runtime handles KB flows
# bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
    def get_bedrock_management_client(region="us-east-1"):
        return boto3.client(
            "bedrock",
            region_name=region,
            aws_access_key_id=os.getenv("ACCESS_KEY"),
            aws_secret_access_key=os.getenv("SECRET_KEY"),
        )

    # Example usage
    bedrock_mgmt = get_bedrock_management_client("us-east-1")
    resp = bedrock_mgmt.list_foundation_models()
    # print(resp,flush=True)
    KB_ID = "JGMPKF6VEI"  # replace with your KB ARN/ID
    GEN_MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/"+model_name  # optional: model to use for generation
    # If your boto3 has retrieve_and_generate_stream:
    stream_resp = bedrock_agent.retrieve_and_generate_stream(
        input={"text": user_query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {"knowledgeBaseId": KB_ID,'inferenceProfileArn': GEN_MODEL_ARN}
        },
    )

    # stream_resp may be an iterator of events (see boto3 docs). Normalize to text:
    for event in stream_resp:
        # event shape depends on SDK; often it contains 'generatedResponseEvent' or similar
        try:
            # try typical nested fields
            if isinstance(event, dict):
                # examples: event.get('generatedResponsePart', {}).get('textResponsePart', {}).get('text')
                gp = event.get("generatedResponsePart")
                if gp:
                    tr = gp.get("textResponsePart", {}).get("text")
                    if tr:
                        yield tr
                        continue
                # fallback: stringify small events
                yield json.dumps(event)
            else:
                yield str(event)
        except Exception:
            yield str(event)
