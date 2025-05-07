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

## Set up Vertex AI

IN GCP we create a new **service account** then we copy the name of it something like:

`name-acc@jobbuddy-458908.iam.gserviceaccount.com`

Then we create an **IAM** policy with this name
1) Add: Vertex AI 
2) Add: Vertex User 

**Generate JSON Key** 
- Service Acc 
- Keys 
- Generate JSON file

Vertex SDK
`pipenv install google-cloud-aiplatform`

**IMPORTANT NOTE:**
- Bert Palm (Text Chat Bison) is deprecated 
- We switched over to a **Gemini** model: `gemini-2.0-flash-lite-001`
- If confused look at the [video](https://www.youtube.com/watch?v=I8W-4oq1onY) again

*routers/gen_quest.py*
```py
from vertexai.preview.generative_models import GenerativeModel
import vertexai
# pipenv install python-dotenv
import dotenv

# Loading up our .env file 
dotenv.load_dotenv()

# Setting up our authentication 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('CREDENTIALS')
vertexai.init(project=os.getenv('PROJECT_ID'), location='us-central1')

# We no longer use Bert or Palm (text/chat bison) so no need to use predit() instead we use gemini-pro
model = GenerativeModel('gemini-2.0-flash-lite-001')
```
1) We set the `CREDENTIALS` environmental varaible to a path to our json key file for the secured user 
2) then we use the GenerativeModel with the lastest flash-lite


Now all we need to do is **generate** a response:

```py
prompt = 'Say hi'
res = model.generate_content(prompt)
```
1) Fit this logic into our Generate Interview Questions API

## Structure 

When these questions are generated we purposefully asked for our questions to be **delimited** by `|` so we could split and return a list of questions 

These questions are stored
1) `JobInterviewQuestion` model 
2) With `job_id` and `user_id`

We've set up a Pandantic to then **serialize** the questions from our database:

```py
class Questions(BaseModel):
    user_id: int 
    job_id: int
    questions: str

    model_config = {
        # Since orm=True is deprecaited...
        'from_attributes': True
    }

# Logic using Pandantic
all_user_jobs_quest =  db.query(JobInterviewQuestion).filter(JobInterviewQuestion.user_id == user_id).all()
return {
    'questions': [Questions.model_validate(quest) for quest in all_user_jobs_quest]
}
```

But when we set up our path `user_id` is optional using the `Optional` from **typing**

```py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

@router.get('/all-quest')
def get_user_questions(user_id: Optional[int] = None, db:Session = Depends(inject_db)) -> Dict[str, Any]:
    pass 
```

## Updating 

Remember we were using `setattr()` to perform something similar to PATCH 

```py
for key, val in new_info.model_dump(exclude_unset=True).items():
    if val is not None:
        setattr(user, key, val)
```
1) But now with *exclude_unset=True* we don't necessarily need to check if Val is null.

Because we're following the PATCH format, this conflicts with our **Pydantic** model which requires all the fields. So we made a seperate one...

```py
from pydantic import BaseModel
from typing import Optional 

class PremUserInfoUpdatePD(BaseModel):
    job_title: Optional[str] = None
    headline: Optional[str] = None 
    yrs_exp: Optional[int] = None

    model_config = {
        'from_attributes': True
    }
```
1) Now all of these are optionl to submit an update for...

## Freezing our requirements with Pipenv 

`pipenv requirements > requirements.txt`

## 5.7 Plans 

- [x] Restrict our AI from running if there's already generated Questions 
- [x] Build out our similarity API 
  - `pipenv install python-docx`
  - We need to have our users upload their resume because we'll return the cosine simialrity based on their entire portfoilio 
  - `pipenv install python-multipart`
  - Convert the `UploadFile` into bytes using `BytesIO` then let `python-docx` read the binary content
  - We may need to use nltk to remove **stopwords** and **punciation** before we send these texts for our prmopt
    - `pipenv install nltk`
- [x] Ready for React Testing 


### End-to-End Similarity API 

**Overview:**

We want achieve a json response the tells us the **text** simialrity between the user's resume with the job description they're providing

Final json Response:
```json
{
  "similarity_score": 0.71485,
  "similarity_percentage": 71.48
}
```

**Creating a Util Function** to clean up the text that we'll eventually grab from the resume `.docx` file.
- we use **NLTK** [(Natural Language Tool Kit)](https://www.nltk.org/index.html) for this purpose
- `pipenv install nltk`

*utils/nltk_clean.py*
```py
from nltk.corpus import stopwords
import string
```

**Removing Punctuations**
```py
# Looping through characters
no_punc = [txt for txt in text if txt not in string.punctuation]
no_punc = ''.join(no_punc)
```
1) Make sure we join back to get a **string of words**

**Corpus stopwords** 
```py
stop_words_set = set(stopwords.words('english'))
no_stop_words = [wrd for wrd in no_punc.split() if wrd.lower() not in stop_words_set] 
```
1) grab the list of stop words 
2) filter out `no_punc.split()` for words that aren't inside the **stop words** list 


**Handling File Uploads** 

In **FastAPI** we accept handle uploads from our views with `UploadFile` and `File`

*routers/prem_user_info.py*
```py
from fastapi import APIRouter, Depends, UploadFile, File

router = APIRouter() 

@router.post('/submit-resume/{user_id}')
async def store_prem_user_resume(user_id: int, resume: UploadFile = File(...), db: Session = Depends(get_db)):
    pass
```
1) Set up your router and endpoint 
2) `resume: UploadFile = File(...)` creates that file upload field in `docs` 

Now we need to read `docx` files (resume file format)
- `pipenv install python-multipart; python-docx`
- We also need multipart to handle the file uploads 

*routers/prem_user_info.py*
```py
from io import BytesIO
from docx import Document

@router.post('/submit-resume/{user_id}')
async def store_prem_user_resume(user_id: int, resume: UploadFile = File(...), db: Session = Depends(get_db)):
    # Await reading 
    context = await resume.read() 

    # Passing into the Document class in byte format 
    resume = Document(BytesIO(context))
    resume_txt = ''

    # Looping through the paragraphs 
    for para in resume.paragraphs:
        resume_txt += para.text + '\n'
```

**Clean Util** + **Database Update** 

*routers/prem_user_info.py*
```py
from app.utils.nltk_clean import clean_txt

user.resume_txt = clean_txt(resume_txt)
db.commit() 
db.refresh(user)
```

**Importing NLTK** 

In order for our app to use clean_txt we need to download `stopwords` in the **main.py** 

*app/main.py*
```py
import nltk

# Download the stopwords for our utility clean text function 
nltk.download('stopwords') 
```
1) This way we could download once and use throughout the routers...

**VertexAI** to generate **Cosine Similarity**

*routers/cos_sim*
```py
from vertexai.preview.generative_models import GenerativeModel
import vertexai
import dotenv

dotenv.load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('CREDENTIALS')
vertexai.init(project=os.getenv('PROJECT_ID'), location='us-central1')

model = GenerativeModel('gemini-2.0-flash-lite-001')
```
1) Setting up the Gen model and credietials to use **GCP**


**Pydantic** model to handle job description and title
```py
from pydantic import BaseModel

class JobPD(BaseModel):
    job_title: str
    job_desc: str
```

**Set up your routers** then we use `clean_txt` utils

```py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.nltk_clean import clean_txt

router = APIRouter() 

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        # Close out the connection to prevent memeory leakage 
        db.close()

@router.post('/gen-cos-sim/{user_id}')
def generate_cosine_similarity(user_id: int, job_info: JobPD, db: Session=Depends(inject_db)):
    user = db.query(PremUserInfo).filter(PremUserInfo.user_id == user_id).first()
    # Cleaning our one-liner job description provided by React Frontend: `.replace(/\n/g, '')`
    job_desc_cleaned = clean_txt(job_info.job_desc)

    prompt = (
        "Compute the cosine similarity between the semantic meanings of the following two texts by generating embeddings for each. "
        "Perform the calculation 3 separate times, then return only the average of the 3 similarity scores as a float between 0 and 1. "
        "Do not return intermediate results. Do not include any extra text or newline characters. Only return the final average on a single line.\n\n"
        f"Resume: {resume_txt}\n"
        f"Job Description: {job_desc_cleaned}"
    )
    response = model.generate_content(prompt)
```

Now we **manipulate** the response text and return the information 

```py
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
```
1) We want to change it into a float and there's a chance where we have `\n` in the final result from Vertex AI 
2) Remember the higher the score the better (from 0-1)

