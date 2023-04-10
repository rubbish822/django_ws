FROM python:3.7.1

ENV DJANGO_SETTINGS_MODULE=django_ws.pro

WORKDIR /code
ADD . /code/

RUN pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com

EXPOSE 8000
CMD bash run.sh
