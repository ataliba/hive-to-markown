FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hive-to-markdown.py .

VOLUME ["/output"]

ENTRYPOINT ["python", "hive-to-markdown.py"]
CMD ["--help"]
