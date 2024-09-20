FROM python:3.12.0
MAINTAINER Niketha Nethaji <nikenethaji@gmail.com>

ENV INSTALL_PATH /featherly
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--access-logfile", "-", "featherly.app:create_app()"]