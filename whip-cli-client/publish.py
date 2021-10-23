import argparse
import asyncio
import logging
import math

import cv2
import numpy
from av import VideoFrame

import aiohttp

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceServer, RTCConfiguration
from aiortc.contrib.media import MediaPlayer

pcs = set()

class FlagVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        height, width = 480, 640

        # generate flag
        data_bgr = numpy.hstack(
            [
                self._create_rectangle(
                    width=213, height=480, color=(255, 0, 0)
                ),  # blue
                self._create_rectangle(
                    width=214, height=480, color=(255, 255, 255)
                ),  # white
                self._create_rectangle(width=213, height=480, color=(0, 0, 255)),  # red
            ]
        )

        # shrink and center it
        M = numpy.float32([[0.5, 0, width / 4], [0, 0.5, height / 4]])
        data_bgr = cv2.warpAffine(data_bgr, M, (width, height))

        # compute animation
        omega = 2 * math.pi / height
        id_x = numpy.tile(numpy.array(range(width), dtype=numpy.float32), (height, 1))
        id_y = numpy.tile(
            numpy.array(range(height), dtype=numpy.float32), (width, 1)
        ).transpose()

        self.frames = []
        for k in range(30):
            phase = 2 * k * math.pi / 30
            map_x = id_x + 10 * numpy.cos(omega * id_x + phase)
            map_y = id_y + 10 * numpy.sin(omega * id_x + phase)
            self.frames.append(
                VideoFrame.from_ndarray(
                    cv2.remap(data_bgr, map_x, map_y, cv2.INTER_LINEAR), format="bgr24"
                )
            )

    def _create_rectangle(self, width, height, color):
        data_bgr = numpy.zeros((height, width, 3), numpy.uint8)
        data_bgr[:, :] = color
        return data_bgr    

class JanusSession:
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
        async with self._http.post(self._root_url + '/whip/endpoint/1234', headers=headers, data=self._offersdp) as response:
            print(response)
            location = response.headers["Location"]
            assert isinstance(location, str)
            self._answersdp = await response.text()
            self._session_url = self._root_url + location
            print(self._session_url)
      
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
        pc.addTrack(FlagVideoStreamTrack())
        # pc.addTrack(VideoStreamTrack())

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
    await asyncio.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Janus")
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

    # create signaling and peer connection
    session = JanusSession(args.url, args.token, args.room)

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