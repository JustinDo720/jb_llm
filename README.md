# FASTAPI Microservice for JobBuddy 

## Let's seperate this into a serverless api for Vertex AI LLM for 
1) Question Generation 
2) Similarity Scores 

## How will this work?

We'll obtain premium information 
- Job Title
- Headline 
- Years of experience 

These are going to help us with Vertex AI 
- Maybe we'll also change resume to text 

We plan to scale so we'll be using api router to have these 2 functionality seperate...

# Packages 

**FastAPI** & **Uvicorn**

`pipenv install fastapi; uvicorn`

**SQLAlchemy**

`pipenv install sqlalchemy`

## Getting Started 

Instead of putting everything in one file...
- We seperate it into **database** vs **routers** all controled by `main.py`

*main.py*
```py
from fastapi import FastAPI
app = FastAPI()
```

*routers/prem_user_info.py*
```py
from fastapi import APIRouter
from pydantic import BaseModel
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
```
1) Set up the router for this api view 
2) Padantic as a serializer (data validation layer)

*main.py*
```py
from app.routers.prem_user_info import router as user_info_router
# Extra Routers 
app.include_router(user_info_router, prefix='/prem-user-info', tags=['Premium User Information'])
```
1) Importing in the prem_user_info router then including it within our app


## Setting up SQLAlchemy 

Sqlalchemy are all set up under `db` directory

*db/database.py*
```py
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine('sqlite:///./user_info.db')
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
```
1) We set up the SessionLocal to later import for db usage
2) Set up Base to create our models 

*db/models.py*
```py
from .database import Base
from sqlalchemy import Column, Integer, String 


class PremUserInfo(Base):
    __tablename__ = 'user_info'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_title = Column(String)
    yrs_exp = Column(Integer)
    headline = Column(String)
```
1) Setting up our PremUserInfo model based off our `Base`

*main.py*
```py
from app.db import models 
from app.db.database import engine

# Creating the models into our db
models.Base.metadata.create_all(bind=engine)
```
1) After we make our model we make sure we create it inside our database 

## Using our SessionLocal 

After creating the session local, we could use this to add data into our database 

*routers/prem_user_info.py*
```py
from app.db.database import SessionLocal
from typing import Generator 
from fastapi import Depends
from sqlalchemy.orm import Session

# Get the database to inject into our router 
def get_db() -> Generator: 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter() 
@router.post('/submit')
def store_prem_user(user_info: PremUserInfoPD, db: Session = Depends(get_db)):
    new_user_info = PremUserInfo(**user_info.model_dump())
    db.add(new_user_info)
    db.commit() 

    db.refresh(new_user_info)

    return {
        'message': 'Receieved',
        'data': new_user_info
    }
```
1) We import in our SessionLocal then create a generator for it 
2) Using `Depends` and `Session` we could fit this into our API function
3) We use `model_dump()` because `**user_info` is still a pydantic object not a dictionary
4) We add, commit then refresh using our `db`