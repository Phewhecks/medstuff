# modules/chatbot.py

import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import os


csv_path = r"C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\chatbot\data\training_data.csv"
json_path = r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\chatbot\data\knowledge_base.json'


df = pd.read_csv(csv_path)
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression())
])

X_train, X_test, y_train, y_test = train_test_split(df['text'], df['disease'], test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)

# Load knowledge base
with open(json_path) as f:
    knowledge_base = json.load(f)

def get_recommendations(disease):
    info = knowledge_base.get(disease.lower())
    if info:
        return {
            "diet": info['diet'],
            "exercise": info['exercise'],
            "tips": info['tips'],
            "note": "This advice is general and may not be accurate. Consult a healthcare provider for specifics."
        }
    return {}

def predict_disease(user_input):
    prediction = pipeline.predict([user_input])[0]
    return prediction, accuracy
