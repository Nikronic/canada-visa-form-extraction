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

# Copy pyproject.toml, setup.cfg, and the entire package
COPY ./pyproject.toml /app/pyproject.toml
COPY ./setup.cfg /app/setup.cfg
COPY ./cvfe /app/cvfe

# install package dependencies (`cvfe` package)
RUN pip install .

# copy the content of the local src directory to the working directory
COPY . /app/

# run FastAPI app with Uvicorn as the main application
CMD ["python", "api.py", "--bind", "0.0.0.0", "--port", "8000"]
