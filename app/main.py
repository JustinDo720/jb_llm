from fastapi import FastAPI
from app.routers.prem_user_info import router as user_info_router
from app.routers.gen_quest import router as generate_question_router
from app.db.database import engine, Base
from app.db import models
# Initialize App
app = FastAPI()

# Root Page 
@app.get('/')
def root():
    # Returning a basic message to get started.
    return {'message': 'FastAPI Ready for LLM!'}

# Create our DB based on models if needed
models.Base.metadata.create_all(bind=engine)

# Extra Routers 
app.include_router(user_info_router, prefix='/prem-user-info', tags=['Premium User Information'])
app.include_router(generate_question_router, prefix='/gen-int-quest', tags=['Generate Interview Questions'])

