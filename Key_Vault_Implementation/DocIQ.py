from notebookutils import mssparkutils
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from pyspark.sql import SparkSession

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

vault_url = "vault_url"

os.environ["AZURE_CLIENT_ID"]     = mssparkutils.credentials.getSecret(vault_url, "ClientID")
os.environ["AZURE_TENANT_ID"]     = mssparkutils.credentials.getSecret(vault_url, "TenantID")
os.environ["AZURE_CLIENT_SECRET"] = mssparkutils.credentials.getSecret(vault_url, "ClientSecret")
    
spark = SparkSession.builder.getOrCreate()

endpoint = "your cognitive service endpoint"
credential = DefaultAzureCredential()

client = DocumentAnalysisClient(
    endpoint=endpoint,
    credential=credential
)

model_id = "prebuilt-read"

folder_path = Path("/lakehouse/******/input/raw/") # fabric file/folder path

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
            "content": extracted_text,
            "extracted_at":datetime.utcnow().isoformat()
        })


df = pd.DataFrame(records)

spark_df = spark.createDataFrame(df)

spark_df.write.mode("overwrite").saveAsTable("alexandria_ocr_output")