# FROM l4t-ds-opencv-7.2:latest
# FROM latonaio/l4t-ds-opencv-7.2-jetpack-4.4:latest
FROM python:3.9.9-bullseye

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=stream-usb-video-by-rtsp-multiple-camera \
    AION_HOME=/var/lib/aion

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libcairo2-dev \
    build-essential \
    libgirepository1.0-dev \
    libmariadb-dev \
    libgstrtspserver-1.0-dev \
    gstreamer1.0-rtsp \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
 
RUN mkdir -p ${AION_HONE}/$POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

ADD . .

RUN pip3 install -r requirements.txt

RUN python3 setup.py install

CMD ["python3","-m", "streamusb"]

