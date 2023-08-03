# use an official Python runtime as a parent image
FROM python:3.11-slim

# set the maintainer label
LABEL maintainer="Nikan Doosti <nikan.doosti@outlook.com>"

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# create and set working directory
WORKDIR /app

# install Pipenv
RUN pip install --upgrade pip

# Copy only the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . /app/

# install the package itself (`cvfe` package)
RUN pip install .

# run FastAPI app with Uvicorn as the main application
CMD ["python", "-m", "cvfe.main.py", "--bind", "0.0.0.0", "--port", "8000"]
