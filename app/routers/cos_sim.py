from fastapi import APIRouter, Depends
import os
from vertexai.preview.generative_models import GenerativeModel
from app.db.database import SessionLocal
import vertexai
import dotenv
from typing import Generator, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.utils.nltk_clean import clean_txt
import requests
from app.utils.jb_url import JB_BACKEND

router = APIRouter()

# Connect to our Vertex AI 
dotenv.load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('CREDENTIALS')
vertexai.init(project=os.getenv('PROJECT_ID'), location='us-central1')

# Creating our Vertex Generative Model 
model = GenerativeModel('gemini-2.0-flash-lite-001')

# DB Helper function 
def inject_db() -> Generator:
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()

class JobPD(BaseModel):
    job_desc: str

@router.post('/gen-cos-sim/{user_id}')
def generate_cosine_similarity(user_id: int, job_info: JobPD, db: Session=Depends(inject_db)):
    # Pull the resume text based on our user 
    try:
        resp = requests.get(f'{JB_BACKEND}/users/profiles/{user_id}/')
        resp.raise_for_status()

        user = resp.json()

        resume_txt = user.resume_txt
        # Remember our frontend takes care of putting everything in oneliner: `.replace(/\n/g, '')`
        job_desc_cleaned = clean_txt(job_info.job_desc)

        # Gen AI Prompt
        prompt = (
            "Compute the cosine similarity between the semantic meanings of the following two texts by generating embeddings for each. "
            "Perform the calculation 3 separate times, then return only the average of the 3 similarity scores as a float between 0 and 1. "
            "Do not return intermediate results. Do not include any extra text or newline characters. Only return the final average on a single line.\n\n"
            f"Resume: {resume_txt}\n"
            f"Job Description: {job_desc_cleaned}"
        )

        response = model.generate_content(prompt)
        sim_score = response.text

        if '\n' in sim_score:
            sim_score = sim_score.replace('\n', '')

        # Regardless of if condition we'll convert into float 
        sim_score = float(sim_score)

        return {
            'similarity_score': sim_score,
            'similarity_percentage': round(sim_score*100, 2)
        }

    except Exception as e:
        return {
            'err': str(e)
        }
