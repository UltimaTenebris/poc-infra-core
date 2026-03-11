import logging
import json
import os
import requests

import azure.functions as func

from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobClient
from openai import AzureOpenAI

app = func.FunctionApp()
credential = DefaultAzureCredential()

suffix = os.environ.get("SUFFIX", "")

logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


def log_info(msg):
    logging.info(f"[v5PROGPY] {msg}")


def log_error(msg):
    logging.error(f"[PROGPY] {msg}")


def run_ocr(pdf_bytes, endpoint):
    log_info(f"run_ocr started, endpoint={endpoint}")

    try:
        doc_client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=credential
        )

        poller = doc_client.begin_analyze_document(
            "prebuilt-layout",
            pdf_bytes
        )

        log_info("OCR request accepted, waiting for result")

        result = poller.result()

        lines = [line.content for page in result.pages for line in page.lines]
        text = "\n".join(lines)

        log_info(f"OCR success, lines={len(lines)}, text_len={len(text)}")
        return lines, text

    except HttpResponseError as e:
        status = getattr(e, "status_code", None)
        log_error(f"OCR HttpResponseError status={status}, message={str(e)}")
        logging.exception("[PROGPY] OCR FAILED WITH HTTP ERROR")
        raise
    except Exception as e:
        log_error(f"OCR unexpected error: {type(e).__name__}: {e}")
        logging.exception("[PROGPY] OCR FAILED")
        raise


def run_ai_analysis(text, endpoint, deployment):
    log_info(
        f"run_ai_analysis started, endpoint={endpoint}, deployment={deployment}, text_len={len(text)}"
    )

    try:
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

        content = completion.choices[0].message.content
        log_info(f"OpenAI success, raw_content={content}")

        return json.loads(content)

    except Exception as e:
        status_code = getattr(e, "status_code", None)
        response = getattr(e, "response", None)

        body_preview = None
        try:
            if response is not None:
                body_preview = response.text
        except Exception:
            body_preview = None

        log_error(
            f"OpenAI failed: type={type(e).__name__}, "
            f"status={status_code}, message={str(e)}, body={body_preview}"
        )
        logging.exception("[PROGPY] OPENAI FAILED")
        raise


def send_discord_notification(blob_name, ai_json):
    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        logging.warning("[PROGPY] DISCORD_WEBHOOK_URL not set")
        return

    message = {
        "content": f"""
Receipt processed

File: {blob_name}

High price: {ai_json.get("high_price")}
Low price: {ai_json.get("low_price")}
"""
    }

    try:
        resp = requests.post(webhook, json=message, timeout=10)
        log_info(f"Discord response status={resp.status_code}, body={resp.text[:500]}")
        resp.raise_for_status()
    except Exception as e:
        log_error(f"Discord failed: {type(e).__name__}: {e}")
        logging.exception("[PROGPY] DISCORD FAILED")
        raise


@app.blob_trigger(
    arg_name="blob",
    path="input%SUFFIX%/{name}",
    connection="AzureWebJobsStorage"
)
def ocr(blob: func.InputStream):
    try:
        log_info(f"Blob trigger fired: {blob.name}")

        storage_account = os.getenv("STORAGE_ACCOUNT_NAME")
        doc_intel_endpoint = os.getenv("DOC_INTEL_ENDPOINT")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        log_info(f"STORAGE_ACCOUNT_NAME={storage_account}")
        log_info(f"DOC_INTEL_ENDPOINT={doc_intel_endpoint}")
        log_info(f"AZURE_OPENAI_ENDPOINT={openai_endpoint}")
        log_info(f"AZURE_OPENAI_DEPLOYMENT={deployment}")

        blob_name = os.path.basename(blob.name)
        output_name = blob_name.replace(".pdf", ".json")

        blob_client = BlobClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            container_name=f"output{suffix}",
            blob_name=output_name,
            credential=credential
        )

        log_info(f"Checking if output exists: output{suffix}/{output_name}")

        try:
            blob_client.get_blob_properties()
            log_info("Output exists, skipping")
            return
        except ResourceNotFoundError:
            log_info("Output not found, continue")
        except Exception as e:
            log_error(f"get_blob_properties failed: {type(e).__name__}: {e}")
            logging.exception("[PROGPY] OUTPUT CHECK FAILED")
            raise

        pdf_bytes = blob.read()
        log_info(f"Blob read success, bytes={len(pdf_bytes)}")

        lines, text = run_ocr(pdf_bytes, doc_intel_endpoint)
        ai_json = run_ai_analysis(text, openai_endpoint, deployment)

        result = {
            "ocr_lines": lines,
            "ai_analysis": ai_json
        }

        payload = json.dumps(result, ensure_ascii=False)
        log_info(f"Uploading output json, bytes={len(payload.encode('utf-8'))}")

        blob_client.upload_blob(
            payload,
            overwrite=False
        )

        log_info(f"Output written: {output_name}")

        send_discord_notification(blob_name, ai_json)

        log_info("Pipeline completed successfully")

    except Exception as e:
        log_error(f"PIPELINE FAILED: {type(e).__name__}: {e}")
        logging.exception("[PROGPY] OCR FUNCTION FAILED")
        raise