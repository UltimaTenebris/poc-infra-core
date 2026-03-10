import logging
import json
import os
import requests

import azure.functions as func

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobClient
from openai import AzureOpenAI

app = func.FunctionApp()
credential = DefaultAzureCredential()


def run_ocr(pdf_bytes, endpoint):

    doc_client = DocumentAnalysisClient(
        endpoint=endpoint,
        credential=credential
    )

    result = doc_client.begin_analyze_document(
        "prebuilt-layout",
        pdf_bytes
    ).result()

    lines = [line.content for page in result.pages for line in page.lines]
    text = "\n".join(lines)

    return lines, text

def run_ai_analysis(text, endpoint, deployment):

    token_provider = get_bearer_token_provider(
        credential,
        "https://cognitiveservices.azure.com/.default"
    )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview"
    )

    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "Extract item prices from receipt OCR text. Return JSON with high_price and low_price."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(completion.choices[0].message.content)

def send_discord_notification(blob_name, ai_json):

    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        logging.warning("DISCORD_WEBHOOK_URL not set")
        return

    message = {
        "content": f"""
            Receipt processed

            File: {blob_name}

            High price: {ai_json.get("high_price")}
            Low price: {ai_json.get("low_price")}
        """
    }

    resp = requests.post(webhook, json=message, timeout=10)

    logging.info(f"Discord status: {resp.status_code}")

@app.blob_trigger(
    arg_name="blob",
    path="input/{name}",
    connection="AzureWebJobsStorage"
)
def ocr(blob: func.InputStream):

    logging.info(f"Blob trigger fired: {blob.name}")

    storage_account = os.getenv("STORAGE_ACCOUNT_NAME")
    doc_intel_endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    blob_name = os.path.basename(blob.name)
    output_name = blob_name.replace(".pdf", ".json")

    blob_client = BlobClient(
        account_url=f"https://{storage_account}.blob.core.windows.net",
        container_name="output",
        blob_name=output_name,
        credential=credential
    )

    # idempotency
    try:
        blob_client.get_blob_properties()
        logging.info("Output exists, skipping")
        return
    except ResourceNotFoundError:
        pass

    pdf_bytes = blob.read()

    # OCR
    lines, text = run_ocr(pdf_bytes, doc_intel_endpoint)

    # AI
    ai_json = run_ai_analysis(text, openai_endpoint, deployment)

    result = {
        "ocr_lines": lines,
        "ai_analysis": ai_json
    }

    # write result
    blob_client.upload_blob(
        json.dumps(result, ensure_ascii=False),
        overwrite=False
    )

    logging.info(f"Output written: {output_name}")

    # notification
    send_discord_notification(blob_name, ai_json)