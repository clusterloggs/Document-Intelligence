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



records = []

for file in folder_path.iterdir():

    if file.suffix.lower() not in [".png", ".jpg", ".jpeg", ".pdf"]:
        continue

    document_id = file.stem   # GUID filename without extension

    with open(file, "rb") as f:
        poller = client.begin_analyze_document(
            model_id=model_id,
            document=f
        )

    result = poller.result()

    # --- LOOP THROUGH DOCUMENTS ---
    for document in result.documents:

        # --- LOOP THROUGH FIELDS ---
        for field_name, field in document.fields.items():

            # safely get value
            field_value = None
            if field.value is not None:
                field_value = str(field.value)
            elif field.content is not None:
                field_value = field.content

            records.append({
                "document_id": document_id,
                "field_name": field_name,
                "field_value": field_value,
                "field_type": str(field.value_type),
                "confidence_score": field.confidence,
                "extracted_at": datetime.utcnow().isoformat()
            })
