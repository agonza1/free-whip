# free-whip
WebRTC broadcasting python cli using WHIP (WebRTC-HTTP ingestion protocol) based on [aiortc](https://github.com/aiortc/aiortc)

Note: 
This client has been tested with [janus-gateway](https://github.com/meetecho/janus-gateway) with [whip-simple-server](https://github.com/lminiero/simple-whip-server).
Since aiortc doesn't support trickle ice you might need to use ice-lite.

## Run locally
If you want to use a specific TURN you can pass it in a .env file like demonstrated in example.env.
Then just run:
```
docker-compose up --build
```