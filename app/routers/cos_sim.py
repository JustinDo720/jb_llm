from fastapi import APIRouter, Depends, UploadFile, File
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
from app.utils.jb_url import JB_BACKEND, PROD
from docx import Document
from io import BytesIO

router = APIRouter()

# Connect to our Vertex AI 
dotenv.load_dotenv()

if not PROD:
    # Local environemnt uses the credentials
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
    resume_txt: str

@router.post('/gen-cos-sim/{user_id}')
def generate_cosine_similarity(user_id: int, job_info: JobPD, db: Session=Depends(inject_db)):
    # Pull the resume text based on our user 
    try:
        # resp = requests.get(f'{JB_BACKEND}/users/profiles/{user_id}/')
        # resp.raise_for_status()

        # user = resp.json()
        resume_txt = job_info.resume_txt
        # Remember our frontend takes care of putting everything in oneliner: `.replace(/\n/g, '')`
        job_desc_cleaned = clean_txt(job_info.job_desc)

        # Gen AI Prompt
        prompt = (
            "You are an API service. Return only a numeric float between 0 and 1. "
            "Do not include code, explanations, markdown, or formatting. "
            "Do not include newlines or any text other than the number.\n\n"
            f"Resume: {resume_txt}\n"
            f"Job Description: {job_desc_cleaned}"
        )


        response = model.generate_content(prompt)
        sim_score = response.text

        if '\n' in sim_score:
            sim_score = sim_score.replace('\n', '')

        # Regardless of if condition we'll convert into float 
        try:
            sim_score = float(sim_score)
        except Exception as e:
            return {
                'msg': "Could not evaluate a similarity score with the materials provided."
            }

        return {
            'similarity_score': sim_score,
            'similarity_percentage': round(sim_score*100, 2)
        }
    except Exception as e:
        return {
            'err': str(e)
        }


@router.post('/resume/{user_id}')
async def convert_resume(resume: UploadFile = File(...)):
    try:
        # Waiting to read the contents 
        cont = await resume.read()
        # Convert into Bytes content
        doc = Document(BytesIO(cont))

        resume_txt = ' '.join([p.text for p in doc.paragraphs])
        cleaned_resume_txt = clean_txt(resume_txt)

        return {
            'resume_txt': cleaned_resume_txt
        }
    except Exception as e:
        return {
            'err': str(e)
        }

