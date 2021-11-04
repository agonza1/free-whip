WHIP client
=======================

This example illustrates how to connect to the WebRTC server's video room using WHIP.

By default it simply sends green video frames, but you can instead specify a
video file to stream to the room.

First install the required packages:

.. code-block:: console

    $ pip install aiohttp aiortc

When you run the example, it will connect to the WHIP server and publish using the '1234' room:

.. code-block:: console

   $ python publish.py http://localhost:8088/whip/endpoint/1234

Additional options
------------------

If you want to join a different endpoint/room, run:

.. code-block:: console

   $ python publish.py http://localhost:8088/whip/endpoint/differentroom

If you want to play a media file instead of sending green video frames and specify your turn server, run:

.. code-block:: console

   $ python publish.py --play-from video.mp4 --turn turn:host:port@turnuser:turnpass http://localhost:8088/whip/endpoint/1234

Running with docker
------------------

.. code-block:: console

docker build -t whip-client .

.. code-block:: console

docker run whip-client