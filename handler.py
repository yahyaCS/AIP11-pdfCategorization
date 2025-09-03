import os, json, uuid, boto3
from utils import extract_text_from_pdf, extract_field, is_soap

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")
DERIVED_BUCKET = os.environ.get("DERIVED_BUCKET")

def lambda_handler(event, context):
    for rec in event['Records']:
        bucket = rec['s3']['bucket']['name']
        key = rec['s3']['object']['key']
        doc_id = uuid.uuid4().hex
        tmp = f"/tmp/{doc_id}.pdf"

        s3.download_file(bucket, key, tmp)

        text = extract_text_from_pdf(tmp)

        if len(text.strip()) < 50:
            meta = {"doc_id": doc_id, "status": "NEEDS_OCR"}
            s3.put_object(Bucket=DERIVED_BUCKET,
                          Key=f"metadata/{doc_id}.json",
                          Body=json.dumps(meta).encode('utf-8'))
            continue

        category = "Clinical SOAP Note" if is_soap(text) else "Unknown"

        patient = extract_field(r"Patient Name[:\-]?\s*(.+)", text)
        dob = extract_field(r"DOB[:\-]?\s*([0-9/]{6,10})", text)
        bp = extract_field(r"BP[:\-]?\s*([0-9]{2,3}/[0-9]{2,3})", text)
        hba1c = extract_field(r"HbA1c[:\-]?\s*([0-9.]+%?)", text)

        comp = {
            "pii": comprehend.detect_pii_entities(Text=text, LanguageCode='en'),
            "entities": comprehend.detect_entities(Text=text, LanguageCode='en'),
            "key_phrases": comprehend.detect_key_phrases(Text=text, LanguageCode='en')
        }

        metadata = {
            "doc_id": doc_id,
            "s3_pdf": f"s3://{bucket}/{key}",
            "category": category,
            "patient_name": patient,
            "dob": dob,
            "vitals_bp": bp,
            "labs_hba1c": hba1c,
            "comprehend": comp,
            "full_text": text
        }

        s3.put_object(Bucket=DERIVED_BUCKET,
                      Key=f"metadata/{doc_id}.json",
                      Body=json.dumps(metadata).encode('utf-8'))

    return {"status": "done"}
