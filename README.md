# free-whip
WebRTC broadcasting python cli using WHIP (WebRTC-HTTP ingestion protocol) based on [aiortc](https://github.com/aiortc/aiortc)

Note: 
This client has been tested with [janus-gateway](https://github.com/meetecho/janus-gateway) with [whip-simple-server](https://github.com/lminiero/simple-whip-server).
Since aiortc doesn't support trickle ice you will need to use ice-lite.

## Run locally
```
docker-compose up --build
```