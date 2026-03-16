import os
import json
import logging
import azure.functions as func

from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="dociq_trigger", methods=["POST"])
def dociq_trigger(req: func.HttpRequest) -> func.HttpResponse:
    try:
        endpoint = os.environ.get("DOCINTEL_ENDPOINT")
        uami_client_id = os.environ.get("UAMI_CLIENT_ID")

        running_in_azure = bool(os.environ.get("WEBSITE_HOSTNAME"))

        logging.info(f"DEBUG endpoint exists: {bool(endpoint)}")
        logging.info(f"DEBUG uami_client_id exists: {bool(uami_client_id)}")
        logging.info(f"DEBUG WEBSITE_HOSTNAME: {os.getenv('WEBSITE_HOSTNAME')}")
        logging.info(f"running_in_azure={running_in_azure}, has_uami_client_id={bool(uami_client_id)}")

        if not endpoint:
            return func.HttpResponse("Missing DOCINTEL_ENDPOINT", status_code=500)

        if running_in_azure:
            if not uami_client_id:
                return func.HttpResponse("Missing UAMI_CLIENT_ID in Azure app settings", status_code=500)
            credential = ManagedIdentityCredential(client_id=uami_client_id)
        else:
            credential = DefaultAzureCredential(exclude_managed_identity_credential=True)

        client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)

        doc_bytes = req.get_body()
        if not doc_bytes:
            return func.HttpResponse("POST a document in the request body.", status_code=400)

        model_id = req.params.get("modelId", "prebuilt-document")

        poller = client.begin_analyze_document(model_id=model_id, document=doc_bytes)
        result = poller.result()

        payload = {
            "modelId": model_id,
            "pages": len(result.pages) if result.pages else 0,
            "contentLength": len(result.content) if result.content else 0
        }

        return func.HttpResponse(json.dumps(payload), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.exception("Function failed")
        return func.HttpResponse(str(e), status_code=500)
