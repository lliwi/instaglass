FROM python

LABEL maintainer="lliwi"

WORKDIR /code
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./app /code/app

RUN export FLASK_APP=app

CMD ["gunicorn","-w4","-t0","-b0.0.0.0:8000" ,"app:create_app()"]