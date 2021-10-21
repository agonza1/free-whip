FROM python:3.9-buster

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
COPY janus.py /app/
#COPY folder /app/folder

#EXPOSE 80
WORKDIR /app

CMD [ "python", "janus.py", "http://localhost:8088/janus"]