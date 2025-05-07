from fastapi import APIRouter, Depends
import os
from vertexai.preview.generative_models import GenerativeModel
import vertexai
import dotenv
from pydantic import BaseModel
from app.db.models import PremUserInfo, JobInterviewQuestion
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
from typing import Generator, Dict, Any, Optional

router = APIRouter()

# Loading up our .env file 
dotenv.load_dotenv()

# Setting up our authentication 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('CREDENTIALS')
vertexai.init(project=os.getenv('PROJECT_ID'), location='us-central1')

# We no longer use Bert or Palm (text/chat bison) so no need to use predit() instead we use gemini-pro
model = GenerativeModel('gemini-2.0-flash-lite-001')

# Pydantic for Job Description 
class GenQ(BaseModel):
    job_id: int
    job_desc: str

class Questions(BaseModel):
    user_id: int 
    job_id: int
    questions: str

    model_config = {
        # Since orm=True is deprecaited...
        'from_attributes': True
    }

# Generating our database
def inject_db() -> Generator:
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()

@router.post('/gen-quest/{user_id}')
def generate_questions(user_id:int, extra_details:GenQ, db: Session=Depends(inject_db)) -> Dict[str, Any]:
    try:
        user_info = db.query(PremUserInfo).filter(PremUserInfo.user_id == user_id).first()
        # Make sure we're looking for the exact job_id from that user
        user_existing_job = db.query(JobInterviewQuestion).filter(JobInterviewQuestion.job_id == extra_details.job_id, JobInterviewQuestion.user_id == user_id)

        # Make sure the user exists and the requested job doesn't have questions already 
        if user_info and user_existing_job.count() == 0:
            job_description = extra_details.job_desc
            prompt = (
                f"You are a recruiter evaluating candidates for the following job description: {job_description}. "
                f"Generate 5 interview questions for a potential employee applying for the role of {user_info.job_title}, "
                f"with {user_info.yrs_exp} years of experience in {user_info.headline}. "
                "Return only the questions, with no explanations. "
                "Separate each question using the pipe symbol '|'. "
                "Do not number or bullet the questions."
            )


            res = model.generate_content(prompt)

            questions = [q.strip() for q in res.text.split('|')]

            # We'll also make sure to save the response 
            new_job_questions = JobInterviewQuestion(user_id=user_id, job_id=extra_details.job_id, questions=res.text)
            db.add(new_job_questions)
            db.commit()

            return {
                'questions': questions
            }
        return {
            'msg': 'No User Found or Interview Questions Already Generated!'
        }
    except Exception as e:
        return {
            'msg': str(e)
        }
    
# Optional user_id for an endpoint of: all-quest?user_id=123
@router.get('/all-quest')
def get_user_questions(user_id: Optional[int] = None, db:Session = Depends(inject_db)) -> Dict[str, Any]:
    """
        This API serves two purposes:
        1) If user_id is provided then that means we return questions for that user_id
        2) If no user_id is provided, we'll return all questions for all jobs in the db
    """
    try:
        if user_id is not None:
            # Retrieve (If no user found it should return an empty list)
            all_user_jobs_quest =  db.query(JobInterviewQuestion).filter(JobInterviewQuestion.user_id == user_id).all()
            return {
                'questions': [Questions.model_validate(quest) for quest in all_user_jobs_quest]
            }
        else:
            # Get All
            all_jobs_quest = db.query(JobInterviewQuestion).all()
            return {
                'questions': [Questions.model_validate(quest) for quest in all_jobs_quest]
            }
    except Exception as e:
        return {
            'msg': str(e)
        }
