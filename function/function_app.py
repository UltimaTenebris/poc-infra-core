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