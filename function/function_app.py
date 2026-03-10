import logging
import json
import os

from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

import azure.functions as func

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobClient

from openai import AzureOpenAI

app = func.FunctionApp()

credential = DefaultAzureCredential()


@app.blob_trigger(
    arg_name="blob",
    path="input/{name}",
    connection="AzureWebJobsStorage"
)
def ocr(blob: func.InputStream):

    logging.info(f"Blob trigger fired for {blob.name}")

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

    # IDEMPOTENCY CHECK

    try:
        blob_client.get_blob_properties()
        logging.info("Output already exists, skipping")
        return
    except ResourceNotFoundError:
        pass

    pdf_bytes = blob.read()

    # ---- OCR ----

    doc_client = DocumentAnalysisClient(
        endpoint=doc_intel_endpoint,
        credential=credential
    )

    result = doc_client.begin_analyze_document(
        "prebuilt-layout",
        pdf_bytes
    ).result()

    ocr_lines = [line.content for page in result.pages for line in page.lines]
    ocr_text = "\n".join(ocr_lines)

    # ---- OPENAI ----

    token_provider = get_bearer_token_provider(
        credential,
        "https://cognitiveservices.azure.com/.default"
    )

    openai_client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview"
    )

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

    final_result = {
        "ocr_lines": ocr_lines,
        "ai_analysis": ai_json
    }

    # ---- WRITE OUTPUT ----

    blob_client.upload_blob(
        json.dumps(final_result, ensure_ascii=False),
        overwrite=False
    )

    logging.info(f"Output written to output/{output_name}")