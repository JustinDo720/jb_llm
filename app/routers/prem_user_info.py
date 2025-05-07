from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Generator 
from app.db.database import SessionLocal
from app.db.models import PremUserInfo
from app.utils.nltk_clean import clean_txt
from typing import Optional, Dict, Any
from docx import Document
from io import BytesIO

# Set up our router for better scaling 
router = APIRouter() 

class PremUserInfoPD(BaseModel):
    """
    user_id: Profile associate with these information 
    job_title: The overall field that our user is in 
    headline: More indepth extra details on the focus 
    yrs_exp: Number of years of experience in this focus
    """
    user_id: int
    job_title: str
    headline: str
    yrs_exp: int

    model_config = {
        'from_attributes': True
    }

class PremUserInfoUpdatePD(BaseModel):
    job_title: Optional[str] = None
    headline: Optional[str] = None 
    yrs_exp: Optional[int] = None

    model_config = {
        'from_attributes': True
    }

# Get the database to inject into our router 
def get_db() -> Generator: 
    db = SessionLocal()
    try:
        yield db
    finally:
        # Close out the connection to prevent memeory leakage 
        db.close()

@router.post('/submit')
def store_prem_user(user_info: PremUserInfoPD, db: Session = Depends(get_db)):
    # Create a Model instance off our user_info by unpacking 
    new_user_info = PremUserInfo(**user_info.model_dump())
    db.add(new_user_info)
    db.commit() 

    # Then we need to refresh our db to reflect changes 
    db.refresh(new_user_info)

    return {
        'message': 'Receieved',
        'data': new_user_info
    }

@router.post('/submit-resume/{user_id}')
async def store_prem_user_resume(user_id: int, resume: UploadFile = File(...), db: Session = Depends(get_db)):

    user = db.query(PremUserInfo).filter(PremUserInfo.user_id == user_id).first()
    if user: 
        # Read the content first before passing into Document 
        content = await resume.read()

        # Convert into bytes for python-docx to read 
        doc = Document(BytesIO(content))
        resume_txt = ''

        for p in doc.paragraphs:
            resume_txt += p.text + '\n'
        
        # Update our user's resume_txt field 
        user.resume_txt = clean_txt(resume_txt)
        db.commit() 
        db.refresh(user)
        return {
            'resume_txt': user.resume_txt
        }

@router.get('/user-info')
def get_prem_user(user_id: Optional[int]=None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        if user_id is not None:
            user = db.query(PremUserInfo).filter(PremUserInfo.user_id == user_id).first()
            return {
                'prem_user_info': PremUserInfoPD.model_validate(user)
            }
        else: 
            info = db.query(PremUserInfo).all()
            return {
                'prem_user_info': [PremUserInfoPD.model_validate(inf) for inf in info]
            }
    except Exception as e:
        return {
            'msg': str(e)
        }
    
@router.put('/user-info/{user_id}')
def update_prem_user(user_id:int, new_info:PremUserInfoUpdatePD, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        user = db.query(PremUserInfo).filter(PremUserInfo.user_id == user_id).first()
        
        # We wanna perform patch with set_attribute 
        for key, val in new_info.model_dump(exclude_unset=True).items():
            if val is not None:
                setattr(user, key, val)

        # Updating in our database 
        db.commit()
        db.refresh(user)

        return {
            'prem_user_info': PremUserInfoPD.model_validate(user)
        }

    except Exception as e:
        return {
            'msg': str(e)
        }