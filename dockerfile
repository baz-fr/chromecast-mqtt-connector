FROM python:3.11

COPY . /chromecast-mqtt/
COPY ./config.ini.dist /chromecast-mqtt/config.ini
WORKDIR /chromecast-mqtt
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "/chromecast-mqtt/connector.py" ]
