import os
from pathlib import Path
from typing import Generator

import boto3
from dotenv import load_dotenv

# Usually .env file is located at the root of the project so we load it from there
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def create_agent():

    return boto3.client(
        "bedrock-agent-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
    )


def retrieve_and_generate_stream(
    user_query: str, model_name: str
) -> Generator[str, None, None]:
    bedrock_agent = create_agent()

    KB_ID = "JGMPKF6VEI"
    GEN_MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/" + model_name

    stream_resp = bedrock_agent.retrieve_and_generate_stream(
        input={"text": user_query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": GEN_MODEL_ARN,
            },
        },
    )

    for event in stream_resp["stream"]:
        if "output" in event:
            part = event["output"]["text"]
            # print(f"Streaming part: {part}", flush=True)
            yield part
