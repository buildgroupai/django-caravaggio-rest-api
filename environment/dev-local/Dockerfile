FROM bgds/base-caravaggio:0.1

# DB connection information
ENV DB_USER caravaggio
ENV DB_PASSWORD caravaggio
ENV DB_NAME caravaggio

# CASSANDRA connection information
ENV CASSANDRA_DB_NAME caravaggio

RUN mkdir /caravaggio

ADD . /caravaggio/

RUN pip install Cython django-haystack

RUN cd /caravaggio \
    && python setup.py develop \
    && pip install django_caravaggio_rest_api[spatial] \
    && pip install -r requirements.txt || echo "ignore error" \
    && pip install -r requirements_tests.txt || echo "ignore error"

RUN mkdir -p /data/caravaggio_rest_api/log

WORKDIR /caravaggio

VOLUME /caravaggio

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0:8000"]