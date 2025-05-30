from fastapi import FastAPI
from app.routers.gen_quest import router as generate_question_router
from app.routers.cos_sim import router as cosine_similarity_router
from app.db.database import engine, Base
from app.db import models
import nltk
from fastapi.middleware.cors import CORSMiddleware

# Initialize App
app = FastAPI()

# Download the stopwords for our utility clean text function 
nltk.download('stopwords') 


# Corsheaders
# Allow requests from your frontend origin
origins = [
    "http://localhost:3000",  # React dev server
    "https://jobbuddy.web.app", # React prod server 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all (not recommended in prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root Page 
@app.get('/')
def root():
    # Returning a basic message to get started.
    return {'message': 'FastAPI Ready for LLM!'}

# Create our DB based on models if needed
models.Base.metadata.create_all(bind=engine)

# Extra Routers 
# app.include_router(user_info_router, prefix='/prem-user-info', tags=['Premium User Information'])
app.include_router(generate_question_router, prefix='/gen-int-quest', tags=['Generate Interview Questions'])
app.include_router(cosine_similarity_router, prefix='/gen-cos-sim', tags=['Generate Cosine Similarity'])

