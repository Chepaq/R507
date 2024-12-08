FROM python:3.11-alpine
WORKDIR /app
COPY . /app
VOLUME /app/database
RUN pip install -r requirements.txt
EXPOSE 5008
CMD ["python", "front.py"]
