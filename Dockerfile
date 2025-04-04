FROM python:3-alpine3.13

ADD src ./src
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

CMD ["python", "./src/main.py"]