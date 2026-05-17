import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class NetflixDataEngine:
    def __init__(self):
        self.bronze_path = "data/bronze_user_clicks.json"
        self.silver_path = "data/silver_user_history.csv"
        self.gold_path = "data/gold_user_engagement.csv"
        os.makedirs("data", exist_ok=True)

    def simulate_user_clicks(self):
        """
        १. BRONZE LAYER: प्रयोगकर्ताले भिडियो हेर्दा निस्कने Raw क्लिकस्ट्रिम डाटा।
        (यसले काफका वा एपीआईबाट आउने रियल-टाइम डाटालाई सिमुलेट गर्छ)
        """
        users = [f"USR_{i:04d}" for i in range(101, 110)]
        movies = ["Squid_Game_S02", "Stranger_Things_S05", "Money_Heist_Korea", "Wednesday_S02", "Narcos_Nepal"]
        devices = ["SmartTV", "Mobile", "Web", "Tablet"]
        
        raw_events = []
        for _ in range(200):
            event = {
                "user_id": np.random.choice(users),
                "profile_name": np.random.choice(["Adult_Profile", "Kids_Profile"]),
                "movie_title": np.random.choice(movies),
                "playback_seconds": int(np.random.randint(10, 7200)), # २ घण्टासम्मको भिडियो
                "device_type": np.random.choice(devices),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            raw_events.append(event)
            
        with open(self.bronze_path, "w") as f:
            json.dump(raw_events, f, indent=4)
        return f"Bronze Layer Sync: {len(raw_events)} raw click events stored."

    def process_silver_layer(self):
        """
        २. SILVER LAYER: Raw डाटालाई क्लिन गर्ने र असंगत विवरहरू हटाउने।
        (Data Cleaning & Structural Transformation)
        """
        if not os.path.exists(self.bronze_path):
            return "Error: Bronze data missing."
            
        with open(self.bronze_path, "r") as f:
            data = json.load(f)
            
        df = pd.DataFrame(data)
        
        # ५ मिनेट भन्दा कम हेरिएका (Accidental Clicks) डाटालाई 'Binge' नमान्ने, तर इतिहासमा राख्ने
        df["is_completed"] = df["playback_seconds"] > 5400 # ९० मिनेट भन्दा बढी हेरेको भए Completed
        df["playback_minutes"] = round(df["playback_seconds"] / 60, 2)
        
        df.to_csv(self.silver_path, index=False)
        return "Silver Layer Sync: Data structured and normalized into CSV."

    def generate_gold_insights(self):
        """
        ३. GOLD LAYER: सिधै बिजनेस इन्टेलिजेंस वा रिकमेन्डेसन इन्जिनमा पठाउन मिल्ने एग्रीगेटेड डाटा।
        (Aggregated Metrics for Business Analytics)
        """
        if not os.path.exists(self.silver_path):
            return "Error: Silver data missing."
            
        df = pd.read_csv(self.silver_path)
        
        # कुन मुभी कुन डिभाइसमा बढी हेरियो र औसत कति मिनेट हेरियो भन्ने एग्रीगेसन
        gold_df = df.groupby(["movie_title", "device_type"]).agg(
            total_views=("user_id", "count"),
            avg_minutes_watched=("playback_minutes", "mean"),
            completed_streams=("is_completed", "sum")
        ).reset_index()
        
        gold_df.to_csv(self.gold_path, index=False)
        return "Gold Layer Sync: Business-ready aggregation matrix compiled."

if __name__ == "__main__":
    engine = NetflixDataEngine()
    print(engine.simulate_user_clicks())
    print(engine.process_silver_layer())
    print(engine.generate_gold_insights())
