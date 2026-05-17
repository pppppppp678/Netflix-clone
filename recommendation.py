import pandas as pd
import numpy as np

class NetflixRecommendationEngine:
    def __init__(self):
        # हाम्रो क्याटलगमा भएका मुभी र तिनीहरूको विधा (Genre)
        self.movie_genres = {
            "Squid_Game_S02": "Thriller/Drama",
            "Stranger_Things_S05": "Sci-Fi/Horror",
            "Money_Heist_Korea": "Action/Crime",
            "Wednesday_S02": "Fantasy/Comedy",
            "Narcos_Nepal": "Action/Crime"
        }

    def get_recommendations(self, target_movie):
        """
        कन्टेन्ट-बेस्ड कोराइसिन सिमिलारिटी (Cosine Similarity Concept) को आधारमा 
        रोजिएको मुभीसँग विधा मिल्ने अन्य मुभीहरू सिफारिस गर्ने प्रणाली।
        """
        if target_movie not in self.movie_genres:
            return []
            
        target_genre = self.movie_genres[target_movie]
        recommendations = []
        
        for movie, genre in self.movie_genres.items():
            if movie != target_movie:
                # यदि विधा पूर्ण रूपमा मिल्छ भने Score = 1.0, आंशिक मिले 0.5, नमिले 0.0
                score = 1.0 if genre == target_genre else (0.5 if any(x in genre for x in target_genre.split('/')) else 0.0)
                if score > 0:
                    recommendations.append({
                        "Movie": movie,
                        "Genre": genre,
                        "Match Score": f"{int(score * 100)}%"
                    })
                    
        # Score को आधारमा सट गर्ने
        return sorted(recommendations, key=lambda x: x["Match Score"], reverse=True)[:3]

    def simulate_ai_catalog(self):
        return pd.DataFrame([{"Movie": k, "Genre": v} for k, v in self.movie_genres.items()])
