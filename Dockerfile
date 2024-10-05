FROM python:3.9

RUN apt-get upgrade && apt-get update
RUN pip install -U pip

COPY . .

RUN pip install -r requirements.txt

# Uncomment this section if deploying to docker

# EXPOSE 8000

# ENTRYPOINT [ "gunicorn",  "--timeout=600", "--limit-request-line 8188", "--bind=0.0.0.0:8000", "app:app" ]


# This section is for deploying to cloud build and cloud run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --limit-request-line 8188 app:app


