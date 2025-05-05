from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Generator 
from app.db.database import SessionLocal
from app.db.models import PremUserInfo

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
