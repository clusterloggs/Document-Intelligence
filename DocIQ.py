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
