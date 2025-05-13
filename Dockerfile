FROM python:3.9-windowsservercore
WORKDIR /app
COPY . .
RUN pip install pyinstaller django psycopg2-binary
RUN pyinstaller --onefile main.py