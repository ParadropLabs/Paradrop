FROM python:2.7

ADD chute /opt/chute
WORKDIR /opt/chute

RUN pip install .

EXPOSE 80
CMD ["helloworld", "--port=80"]
