FROM python:3

ADD . /opt/hawknest
WORKDIR /opt/hawknest
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
&& apt-get install -y python-dev libsasl2-dev libldap2-dev libssl-dev \
libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr \
flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN pip install -r requirements.txt
RUN python -m spacy download xx
RUN python -m spacy download pt
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]