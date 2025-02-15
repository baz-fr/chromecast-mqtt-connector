FROM arm64v8/python:3.12-alpine

COPY . /chromecast-mqtt/
COPY ./config.ini.dist /chromecast-mqtt/config.ini
WORKDIR /chromecast-mqtt
COPY requirements.txt .
RUN pip install --no-cache-dir --verbose -r requirements.txt
CMD [ "python", "/chromecast-mqtt/connector.py" ]
