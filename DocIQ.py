from pathlib import Path

# Correct path: Files, not Tables
folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")

records = []

for file in folder_path.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]:


        with open(file, "rb") as f:
            poller = client.begin_analyze_document(
                model_id=model_id,  
                document=f
            )


        result = poller.result()


        lines = []
        for page in result.pages:
            for line in page.lines:
                lines.append(line.content)

        extracted_text = "\n".join(lines)

     
        records.append({
            "file_name": file.name,
            "file_type": file.suffix.lower(),
            "content": extracted_text
        })


for r in records:
    print(f"\n===== {r['file_name']} =====")
    print(r["content"][:1000])


import pandas as pd

df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)

spark_df.write.mode("overwrite").saveAsTable("alexandria_ocr_output")



#######################

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime
from pathlib import Path
import pandas as pd

# Initialize Doc IQ client
endpoint = "https://<your-doc-iq-resource>.cognitiveservices.azure.com/"
key = "<your-doc-iq-key>"
model_id = "prebuilt-document"  # or your custom model ID
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")
records = []

for file in folder_path.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]:
        with open(file, "rb") as f:
            poller = client.begin_analyze_document(model_id=model_id, document=f)
        result = poller.result()

        document_id = str(file.stem)  # Use filename stem as document_id

        for doc in result.documents:
            for field_name, field in doc.fields.items():
                records.append({
                    "document_id": document_id,
                    "field_name": field_name,
                    "field_value": field.value,
                    "field_type": field.type,
                    "confidence_score": field.confidence,
                    "extracted_at": datetime.utcnow().isoformat()
                })

# Convert to Spark DataFrame and write to Fabric Lakehouse
df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)
spark_df.write.mode("overwrite").saveAsTable("extracted_fields")

#############

import requests
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Azure Document Intelligence endpoint and key
endpoint = "https://<your-doc-iq-resource>.cognitiveservices.azure.com/"
key = "<your-doc-iq-key>"
model_id = "prebuilt-document"  # or your custom model ID

folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")
records = []

for file in folder_path.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]:
        with open(file, "rb") as f:
            url = f"{endpoint}documentintelligence/documentModels/{model_id}:analyze?api-version=2024-07-31"
            headers = {
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/octet-stream"
            }
            response = requests.post(url, headers=headers, data=f.read())
            response.raise_for_status()

            # Poll for result
            result_url = response.headers["operation-location"]
            while True:
                result_resp = requests.get(result_url, headers={"Ocp-Apim-Subscription-Key": key})
                result_json = result_resp.json()
                if result_json.get("status") in ["succeeded", "failed"]:
                    break

            if result_json["status"] == "succeeded":
                document_id = file.stem
                for doc in result_json["analyzeResult"]["documents"]:
                    for field_name, field in doc.get("fields", {}).items():
                        records.append({
                            "document_id": document_id,
                            "field_name": field_name,
                            "field_value": field.get("valueString") or field.get("content"),
                            "field_type": field.get("type"),
                            "confidence_score": field.get("confidence"),
                            "extracted_at": datetime.utcnow().isoformat()
                        })

# Convert to Spark DataFrame and save
df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)
spark_df.write.mode("overwrite").saveAsTable("extracted_fields")


