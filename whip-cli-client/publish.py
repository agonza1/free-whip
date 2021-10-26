import argparse
import asyncio
import logging

import aiohttp

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceServer, RTCConfiguration
from aiortc.contrib.media import MediaPlayer

pcs = set()

class WhipSession:
    def __init__(self, url, token, room):
        self._http = None
        self._root_url = url
        self._session_url = None
        self._token = token
        self._session_room = room
        self._offersdp = None
        self._answersdp = None

    async def createEndpoint(self, offer):
        self._http = aiohttp.ClientSession()
        self._offersdp = offer.sdp
        headers = {'content-type': 'application/sdp', 'Authorization' : 'Bearer ' + self._token}
        async with self._http.post(self._root_url + '/whip/endpoint/' + str(self._session_room), headers=headers, data=self._offersdp) as response:
            print(response)
            location = response.headers["Location"]
            assert isinstance(location, str)
            self._answersdp = await response.text()
            self._session_url = self._root_url + location
      
    async def trickle(self, data):
        self._http = aiohttp.ClientSession()
        headers = {'content-type': 'application/trickle-ice-sdpfrag', 'Authorization' : 'Bearer +' + self._token}
        async with self._http.patch(self._session_url, headers=headers, data=data) as response:
            print(response)
            data = await response.text()

    async def destroy(self):
        if self._session_url:
            headers = {'Authorization' : 'Bearer ' + self._token}
            async with self._http.delete(self._session_url, headers=headers) as response:
                print(response)
                assert response.ok == True
            self._session_url = None

        if self._http:
            await self._http.close()
            self._http = None


async def publish(session, player):
    """
    Live stream video to the room.
    """
    pc = RTCPeerConnection(configuration=RTCConfiguration(
        iceServers=[RTCIceServer(
            urls=["stun:stun.l.google.com:19302", 
            "turn:host.docker.internal:3478"], 
            username="turnuser", 
            credential="turnpassword")]))

    pcs.add(pc)
    pc.addTransceiver("audio", direction="sendonly")
    pc.addTransceiver("video", direction="sendonly")

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # configure media
    media = {"audio": False, "video": True}
    if player and player.audio:
        pc.addTrack(player.audio)
        media["audio"] = True

    if player and player.video:
        pc.addTrack(player.video)
    else:
        pc.addTrack(VideoStreamTrack())

    # send offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    #Create WHIP endpoint with the SDP offer
    await session.createEndpoint(offer)
    print(session) 
    # apply answer
    await pc.setRemoteDescription(
        RTCSessionDescription(
            sdp=session._answersdp, type="answer"
        )
    )
    # aiortc doesn't support trickle ice yet
    # await session.trickle("")

async def run(player, session):
    # send video
    await publish(session=session, player=player)
    # exchange media for 1 minute
    print("Exchanging media...")
    await asyncio.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WHIP cli client for Janus live streaming")
    parser.add_argument("url", help=" WHIP root URL, e.g. http://localhost:7080/whip"),
    parser.add_argument(
        "--token",
        default="verysecret",
        help="The bearer token for the endpoint that will provide the resource.",
    ),
    parser.add_argument(
        "--room",
        type=int,
        default=1234,
        help="The video room ID to join (default: 1234).",
    ),
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # HTTP signaling and peer connection
    session = WhipSession(args.url, args.token, args.room)

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        player = None

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(player=player, session=session)
        )
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(session.destroy())
        # close peer connections
        coros = [pc.close() for pc in pcs]
        loop.run_until_complete(asyncio.gather(*coros))