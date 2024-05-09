FROM python:3.11-alpine

WORKDIR /app

VOLUME /app

COPY ./requirements.txt ./requirements.txt

RUN touch /app/app.log
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "app.py"]