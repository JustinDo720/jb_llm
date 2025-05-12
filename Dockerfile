# Using the slim python image
FROM python:3.12-slim

# Creating a working directory
WORKDIR /app

# Copying the requirements.txt so we could pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application over 
COPY . .

# Setting up buffers 
ENV PYTHONUNBUFFERED=1

# Running app: Make sure we have host as 0.0.0.0 to handle the docker container url and cloud run compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]