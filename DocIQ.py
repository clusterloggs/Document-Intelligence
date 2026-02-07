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


###########

# ---------------- INSTALL + IMPORTS ----------------
%pip install azure-ai-formrecognizer --quiet

import os
from pathlib import Path
from datetime import datetime
import pandas as pd

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# ---------------- AZURE DOCUMENT INTELLIGENCE ----------------
DOC_INTEL_ENDPOINT = "https://<your-resource-name>.cognitiveservices.azure.com/"
DOC_INTEL_KEY = "<your-key>"

client = DocumentAnalysisClient(
    endpoint=DOC_INTEL_ENDPOINT,
    credential=AzureKeyCredential(DOC_INTEL_KEY)
)

# ---------------- FILE LOCATION ----------------
# IMPORTANT: this must be the LOCAL Fabric path (NOT ABFS)
folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")

records = []

# ---------------- OCR PROCESSING LOOP ----------------
for file in folder_path.iterdir():

    if file.suffix.lower() not in [".png", ".jpg", ".jpeg", ".pdf"]:
        continue

    print(f"Processing: {file.name}")

    document_id = file.stem

    try:
        with open(file, "rb") as f:
            poller = client.begin_analyze_document(
                model_id="prebuilt-read",
                document=f
            )

        result = poller.result()

        extracted_text = ""
        total_conf = 0
        word_count = 0

        # Extract text + confidence
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + " "
                for word in line.words:
                    total_conf += word.confidence
                    word_count += 1

        avg_confidence = total_conf / word_count if word_count > 0 else None

        records.append({
            "document_id": document_id,
            "file_name": file.name,
            "file_type": file.suffix.lower(),
            "content": extracted_text.strip(),
            "confidence_score": avg_confidence,
            "page_count": len(result.pages),
            "extracted_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        print(f"Failed on {file.name}: {str(e)}")

# ---------------- CREATE DATAFRAME ----------------
df = pd.DataFrame(records)

print("Rows extracted:", len(df))
display(df.head())

# ---------------- CONVERT TO SPARK ----------------
spark_df = spark.createDataFrame(df)

# ---------------- SAVE TO LAKEHOUSE DELTA TABLE ----------------
table_name = "document_ocr"

spark_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(table_name)

print(f"Saved to Lakehouse table: {table_name}")
