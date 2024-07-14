FROM python:latest
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
WORKDIR /app
CMD ["python", "-u","syncuserplaylist/run.py"]