import os
import json
import logging
import azure.functions as func

from azure.identity import ManagedIdentityCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Received request.")
    try:
        uami_client_id = os.environ.get("UAMI_CLIENT_ID")
        endpoint = os.environ.get("DOCINTEL_ENDPOINT")  

        if not uami_client_id or not endpoint:
            return func.HttpResponse(
                "Missing UAMI_CLIENT_ID or DOCINTEL_ENDPOINT app setting.",
                status_code=500
            )

        credential = ManagedIdentityCredential(client_id=uami_client_id)

        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        logging.info(f"Token acquired length={len(token.token)}")

        client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)

        doc_bytes = req.get_body()
        if not doc_bytes:
            return func.HttpResponse("No document provided in request body.", status_code=400)

        model_id = req.params.get("modelId", "prebuilt-document")

        poller = client.begin_analyze_document(model_id=model_id, document=doc_bytes)
        result = poller.result()

        payload = {
            "modelId": model_id,
            "pages": len(result.pages) if result.pages else 0,
        }
        return func.HttpResponse(json.dumps(payload), mimetype="application/json", status_code=200)

    except Exception as ex:
        logging.exception("Error in function")
        return func.HttpResponse(str(ex), status_code=500)
