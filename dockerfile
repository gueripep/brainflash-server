FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./gcp-service-account.json /code/gcp-service-account.json

# Create audio directory for TTS files
RUN mkdir -p /code/audio

EXPOSE 80

# Use development mode with auto-reload
CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "80"]