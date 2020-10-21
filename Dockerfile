# FROM l4t-ds-opencv-7.2:latest
FROM latonaio/l4t-ds-opencv-7.2-jetpack-4.4:latest


# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=stream-usb-video-by-rtsp-multiple-camera \
    AION_HOME=/var/lib/aion

# Install dependencies
RUN apt-get update && apt-get install -y \ 
    pkg-config \
    libcairo2-dev \ 
    gcc \ 
    python3-dev \ 
    libgirepository1.0-dev \ 
    libmysqlclient-dev \
    libgstrtspserver-1.0-dev \
    gstreamer1.0-rtsp \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
 
RUN mkdir -p ${AION_HONE}/$POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

ADD . .
RUN python3 setup.py install

CMD ["python3","-m", "streamusb"]

