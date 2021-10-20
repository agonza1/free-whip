FROM ubuntu:18.04

# ignore dialogue
ENV DEBIAN_FRONTEND=noninteractive

# upgrade env
RUN apt update
RUN apt upgrade -y

# install python3 and pip
RUN apt install python3 -y
RUN apt install python3-pip -y
RUN apt install python3-dev -y
RUN pip3 install --upgrade pip

# for aiortc
RUN apt install libavdevice-dev -y
RUN apt install libavfilter-dev -y
RUN apt install libopus-dev -y
RUN apt install libvpx-dev -y
RUN apt install pkg-config -y
RUN apt install libopencv-dev -y
# python modules
RUN pip install aiortc
RUN pip install aiohttp
RUN pip install opencv-python

ADD janus.py /
#EXPOSE 3333
CMD [ "python3", "./janus.py", "http://localhost:8088/janus"]