#!/usr/bin/env python3
"""
Mi360RtspServer.py -- Mi 360 P2P to RTSP proxy (Python/GStreamer)

Reads CAMERA_IP and RTSP_PORT from environment variables.
"""

import os
import socket
import struct
from threading import Thread

import gi
from Crypto.Cipher import AES

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

class Mi360P2PClient:
    _DEFAULT_KEY = bytes.fromhex('31323334353637383930616263646566')

    def __init__(self, ip: str, port: int = 6666):
        self.ip = ip
        self.port = port
        self.key = self._DEFAULT_KEY
        self.sock = socket.create_connection((self.ip, self.port))

    def login(self) -> None:
        payload = b'\xA5\x5A' + b'\x00' * 29 + b'\x03'
        payload = payload.ljust(32, b'\x00')
        cipher = AES.new(self.key, AES.MODE_CBC, iv=b'\x00' * 16)
        self.sock.send(cipher.encrypt(payload))
        resp = self.sock.recv(32)
        dec = cipher.decrypt(resp)
        self.key = dec[4:20]

    def recv_frame(self) -> bytes:
        raw_len = self.sock.recv(4)
        if len(raw_len) < 4:
            raise ConnectionError("Incomplete frame length")
        frame_len = struct.unpack('>I', raw_len)[0]
        enc = b''
        while len(enc) < frame_len:
            chunk = self.sock.recv(frame_len - len(enc))
            if not chunk:
                raise ConnectionError("Socket closed prematurely")
            enc += chunk
        cipher = AES.new(self.key, AES.MODE_CBC, iv=b'\x00' * 16)
        dec = cipher.decrypt(enc)
        pad = dec[-1]
        if 1 <= pad <= 16:
            dec = dec[:-pad]
        return dec

class Mi360RtspFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, camera_ip: str):
        super().__init__()
        self.client = Mi360P2PClient(camera_ip)
        self.client.login()
        self.set_launch(
            'appsrc name=src is-live=true format=time '
            'caps=video/x-h264,stream-format=byte-stream '
            '! h264parse ! rtph264pay name=pay0 pt=96'
        )
        self.set_shared(True)

    def do_media_configure(self, rtsp_media):
        pipeline = rtsp_media.get_element()
        self.appsrc = pipeline.get_child_by_name("src")
        Thread(target=self._push_frames, daemon=True).start()

    def _push_frames(self):
        while True:
            try:
                nal = self.client.recv_frame()
            except Exception:
                break
            buf = Gst.Buffer.new_allocate(None, len(nal), None)
            buf.fill(0, nal)
            buf.pts = Gst.util_uint64_scale(Gst.ClockTime.now(), 1, 1)
            buf.duration = Gst.SECOND // 25
            self.appsrc.emit("push-buffer", buf)

def main():
    # Read from environment
    camera_ip = os.getenv('CAMERA_IP', '192.168.1.42')
    rtsp_port = int(os.getenv('RTSP_PORT', '8554'))

    Gst.init(None)
    server = GstRtspServer.RTSPServer()
    server.set_service(str(rtsp_port))
    mount_points = server.get_mount_points()

    factory = Mi360RtspFactory(camera_ip)
    mount_points.add_factory("/live", factory)

    server.attach(None)
    print(f"RTSP server running at rtsp://<host-ip>:{rtsp_port}/live")
    loop = GObject.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()
