FROM python:3-slim

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    mkdir -p /wd

WORKDIR "/wd"
CMD ["./server.py"]
