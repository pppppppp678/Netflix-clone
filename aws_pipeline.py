import pandas as pd
import json
import os
from datetime import datetime

class AWSS3BucketSimulation:
    def __init__(self):
        self.bronze_dir = "aws_s3/bronze_raw_events"
        self.silver_dir = "aws_s3/silver_cleaned"
        self.dlq_dir = "aws_s3/dead_letter_queue" # खराब डाटा राख्ने ठाउँ
        os.makedirs(self.bronze_dir, exist_ok=True)
        os.makedirs(self.silver_dir, exist_ok=True)
        os.makedirs(self.dlq_dir, exist_ok=True)

    def upload_mock_payload(self, file_name, json_data):
        file_path = os.path.join(self.bronze_dir, file_name)
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=4)
        return file_path

class AWSLambdaFunction:
    def __init__(self, s3_env):
        self.s3 = s3_env
        self.sns_logs = [] # SNS अलर्टहरू सेभ गर्न

    def trigger_sns_notification(self, subject, message):
        """AWS SNS (Simple Notification Service) को सिमुलेसन"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert = {
            "TopicArn": "arn:aws:sns:ap-south-1:123456789012:DataPipelineAlerts",
            "Subject": f"⚠️ [ALERT] {subject}",
            "Message": message,
            "Timestamp": timestamp
        }
        self.sns_logs.append(alert)
        print(f"\n🔔 [AWS SNS TRIGGERED]\nSubject: {alert['Subject']}\nMessage: {alert['Message']}\n")

    def aws_handler(self, event):
        s3_metadata = event.get("Records", [])[0].get("s3", {})
        file_name = s3_metadata.get("object", {}).get("key")
        raw_file_path = os.path.join(self.s3.bronze_dir, file_name)
        
        if not os.path.exists(raw_file_path):
            return {"statusCode": 404, "body": "Object Not Found"}

        with open(raw_file_path, 'r') as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                # यदि JSON फाइल नै करप्ट छ भने सिधै SNS र DLQ मा पठाउने
                self.trigger_sns_notification(
                    "Malformed JSON Target Ingestion", 
                    f"File {file_name} contains corrupted or invalid JSON structure. Routing to Dead Letter Queue (DLQ)."
                )
                os.rename(raw_file_path, os.path.join(self.s3.dlq_dir, file_name))
                return {"statusCode": 400, "body": "Malformed JSON Saved to DLQ"}

        df = pd.DataFrame(raw_data)
        
        # 🛡️ DATA VALIDATION GATEWAY
        required_columns = ["tx_id", "user", "amount"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        # नियम १: आवश्यक कोलमहरू छुटेका छन् कि छैनन्?
        if missing_cols:
            self.trigger_sns_notification(
                "Schema Mismatch (Missing Schema Columns)", 
                f"Critical failure on file {file_name}. Expected columns {required_columns} but missed {missing_cols}."
            )
            os.rename(raw_file_path, os.path.join(self.s3.dlq_dir, file_name))
            return {"statusCode": 422, "body": "Schema Validation Failed"}
            
        # नियम २: अमाउन्ट नेगेटिभ हुनुहुँदैन (Business Logic Check)
        if (df['amount'] < 0).any():
            self.trigger_sns_notification(
                "Data Quality Violation (Negative Amount Identified)", 
                f"File {file_name} rejected due to negative transaction volume detected in financial ledger records."
            )
            # ब्याड डेटा भएको फाइललाई DLQ मा सार्ने
            os.rename(raw_file_path, os.path.join(self.s3.dlq_dir, file_name))
            return {"statusCode": 422, "body": "Data Quality Constraint Violation"}

        # सबै ठीक छ भने ट्रान्सफर्म र लोड गर्ने (Silver Layer)
        df['amount'] = df['amount'].fillna(0.0)
        df['transaction_date'] = pd.to_datetime(df['timestamp']).dt.date
        df['ingestion_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        output_file_name = f"silver_{file_name.replace('.json', '.csv')}"
        silver_file_path = os.path.join(self.s3.silver_dir, output_file_name)
        df.to_csv(silver_file_path, index=False)
        
        return {"statusCode": 200, "body": "Data Partition Sync Successful"}
