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

