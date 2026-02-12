%pip install azure-ai-formrecognizer --quiet

from pathlib import Path
from datetime import datetime
import json
import pandas as pd

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# AZURE CONFIG
DOC_INTEL_ENDPOINT = "https://<your-resource>.cognitiveservices.azure.com/"
DOC_INTEL_KEY = "<your-key>"
IRS_MODEL_ID = "<your-custom-irs-model-id>"

client = DocumentAnalysisClient(
    endpoint=DOC_INTEL_ENDPOINT,
    credential=AzureKeyCredential(DOC_INTEL_KEY)
)

folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")

records = []

# HELPER
def detect_document_type(file_path):

    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            document=f
        )
    result = poller.result()

    text = ""
    if result.pages:
        for line in result.pages[0].lines:
            text += line.content.upper() + " "

    
    if "DRIVER LICENSE" in text or "DLN" in text or "DOB" in text:
        return "driver_license"

    if "FORM 1040" in text or "U.S. INDIVIDUAL INCOME TAX RETURN" in text:
        return "irs_tax"

    if "FORM 1099" in text or "NONEMPLOYEE COMPENSATION" in text:
        return "irs_tax"

    return "unknown"



for file in folder_path.iterdir():

    if file.suffix.lower() not in [".png", ".jpg", ".jpeg", ".pdf"]:
        continue

    document_id = file.stem
    print(f"\nProcessing {file.name}")

    try:
        doc_type = detect_document_type(file)

        # DRIVER LICENSE
        if doc_type == "driver_license":

            with open(file, "rb") as f:
                poller = client.begin_analyze_document(
                    model_id="prebuilt-idDocument",
                    document=f
                )

            result = poller.result()
            doc = result.documents[0]

            for name, field in doc.fields.items():
                records.append({
                    "document_id": document_id,
                    "document_type": "driver_license",
                    "field_name": name,
                    "field_value": str(field.value),
                    "confidence_score": field.confidence,
                    "extracted_at": datetime.utcnow().isoformat()
                })

        # IRS FORMS (CUSTOM MODEL)
        elif doc_type == "irs_tax":

            with open(file, "rb") as f:
                poller = client.begin_analyze_document(
                    model_id=IRS_MODEL_ID,
                    document=f
                )

            result = poller.result()
            doc = result.documents[0]

            for name, field in doc.fields.items():
                records.append({
                    "document_id": document_id,
                    "document_type": "irs_tax_form",
                    "field_name": name,
                    "field_value": str(field.value),
                    "confidence_score": field.confidence,
                    "extracted_at": datetime.utcnow().isoformat()
                })

        else:
            print("Skipped (unknown document)")

    except Exception as e:
        print("Failed:", file.name, str(e))



df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)

spark_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable("document_extracted_fields")

print("Finished. Records written:", len(df))
