FROM python:3.9-buster

ARG TURN=${TURN}

RUN apt-get update
RUN apt-get install -y ffmpeg
RUN apt-get install -y libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config libsrtp2-dev

# Install python
RUN pip install aiohttp
RUN pip install aiortc
RUN pip install opencv-python
RUN pip install ffmpeg-python

# Copy files
RUN mkdir /app
COPY publish.py /app/

WORKDIR /app

CMD python publish.py --turn ${TURN} http://host.docker.internal:7080/whip/endpoint/1234