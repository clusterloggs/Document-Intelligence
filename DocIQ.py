from pathlib import Path

# Correct path: Files, not Tables
folder_path = Path("/lakehouse/default/Files/alexandria-raw-data")

records = []

for file in folder_path.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]:

        # 1. Send file to Document Intelligence
        with open(file, "rb") as f:
            poller = client.begin_analyze_document(
                model_id=model_id,   # e.g. "prebuilt-read"
                document=f
            )

        # 2. Wait for OCR to complete
        result = poller.result()

        # 3. Extract text
        lines = []
        for page in result.pages:
            for line in page.lines:
                lines.append(line.content)

        extracted_text = "\n".join(lines)

        # 4. Store result (one row per file)
        records.append({
            "file_name": file.name,
            "file_type": file.suffix.lower(),
            "content": extracted_text
        })

# 5. Display results for validation
for r in records:
    print(f"\n===== {r['file_name']} =====")
    print(r["content"][:1000])


import pandas as pd

df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)

spark_df.write.mode("overwrite").saveAsTable("alexandria_ocr_output")
