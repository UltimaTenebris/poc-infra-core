import logging
import json
import os

import azure.functions as func

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.fileshare import ShareFileClient

from openai import AzureOpenAI

app = func.FunctionApp()


@app.route(route="ocr", auth_level=func.AuthLevel.FUNCTION)
def ocr(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("OCR function started")

    try:
        credential = DefaultAzureCredential()

        storage_account = os.getenv("STORAGE_ACCOUNT_NAME")
        file_share = os.getenv("FILE_SHARE_NAME")
        doc_intel_endpoint = os.getenv("DOC_INTEL_ENDPOINT")
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        missing = []
        if not storage_account:
            missing.append("STORAGE_ACCOUNT_NAME")
        if not file_share:
            missing.append("FILE_SHARE_NAME")
        if not doc_intel_endpoint:
            missing.append("DOC_INTEL_ENDPOINT")
        if not openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not deployment:
            missing.append("AZURE_OPENAI_DEPLOYMENT")

        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")

        logging.info("Getting storage token via Managed Identity")
        token = credential.get_token("https://storage.azure.com/.default")
        logging.info(f"STORAGE TOKEN OK: {token.token[:20]}")

        logging.info(f"STORAGE_ACCOUNT_NAME={storage_account}")
        logging.info(f"FILE_SHARE_NAME={file_share}")

        logging.info("Creating ShareFileClient")
        file_client = ShareFileClient(
            account_url=f"https://{storage_account}.file.core.windows.net",
            share_name=file_share,
            file_path="sample.pdf",
            credential=credential,
            token_intent="backup"
        )
        logging.info("ShareFileClient created")

        logging.info("Downloading PDF from Azure Files")
        try:
            pdf_bytes = file_client.download_file().readall()
            logging.info(f"PDF downloaded successfully, size={len(pdf_bytes)} bytes")
        except Exception as storage_error:
            logging.error(f"STORAGE ERROR: {str(storage_error)}")
            raise

        logging.info("Creating Document Intelligence client")
        doc_client = DocumentAnalysisClient(
            endpoint=doc_intel_endpoint,
            credential=credential
        )

        logging.info("Running OCR")
        result = doc_client.begin_analyze_document(
            "prebuilt-layout",
            pdf_bytes
        ).result()

        ocr_lines = [line.content for page in result.pages for line in page.lines]
        ocr_text = "\n".join(ocr_lines)
        logging.info(f"OCR extracted {len(ocr_lines)} lines")

        logging.info("Creating Azure OpenAI client")
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )

        openai_client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2024-12-01-preview"
        )

        logging.info("Calling OpenAI")
        completion = openai_client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": "Extract item prices from receipt OCR text. Return JSON with high_price and low_price."
                },
                {
                    "role": "user",
                    "content": ocr_text
                }
            ],
            response_format={"type": "json_object"},
        )

        ai_json = json.loads(completion.choices[0].message.content)
        logging.info("OpenAI analysis completed")

        final_result = {
            "ocr_lines": ocr_lines,
            "ai_analysis": ai_json
        }

        return func.HttpResponse(
            json.dumps(final_result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"FUNCTION ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )