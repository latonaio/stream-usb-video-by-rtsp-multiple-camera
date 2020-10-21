# coding: utf-8

# Copyright (c) 2019-2020 Latona. All rights reserved.

from multiprocessing import Process
from time import sleep

import gi
from aion.logger import lprint
from aion.microservice import main_decorator, Options

gi.require_version('Gst', '1.0')  # noqa
gi.require_version('GstRtspServer', '1.0')  # noqa
from gi.repository import GLib, Gst, GstRtspServer  # isort:skip
import os

Gst.init(None)
# Gst.debug_set_active(True)
# Gst.debug_set_default_threshold(4)

DEFAULT_WIDTH = 864
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 10
DEFAULT_PORT = 8554
DEFAULT_URI = "/usb"

SERVICE_NAME = "stream-usb-video-by-rtsp-multiple-camera"
SUFFIX = os.environ.get('SUFFIX', '')
SERVICE_NAME = SERVICE_NAME + '-' + SUFFIX if SUFFIX else SERVICE_NAME


def get_pipeline(width, height, fps):
    return f"""
        ( v4l2src io-mode=2 name=source !
        image/jpeg, width={width}, height={height}, framerate={fps}/1 !
        queue ! rtpjpegpay name=pay0 pt=96 )
    """


class GstServer:
    def __init__(self, port, width, height, fps, device_path):
        port_str = str(port)
        pipe = get_pipeline(width, height, fps)
        self.pipe = None

        self.server = GstRtspServer.RTSPServer().new()
        self.server.set_service(port_str)
        self.server.connect("client-connected", self.client_connected)

        self.f = GstRtspServer.RTSPMediaFactory().new()
        self.f.set_eos_shutdown(True)
        self.f.set_launch(pipe)
        self.f.set_shared(True)
        self.f.connect("media-constructed", self.on_media_constructed)
        self.device_path = device_path

        m = self.server.get_mount_points()
        m.add_factory(DEFAULT_URI, self.f)
        self.server.attach(None)

    def start(self):
        loop = GLib.MainLoop()
        loop.run()
        self.stop()

    def client_connected(self, server, client):
        lprint(f'[RTSP] next service is connected')

    def on_media_constructed(self, factory, media):
        # get camera path
        if self.device_path is None:
            lprint("[RTSP] device is not connected")
            self.stop()
            return
        # get element state and check state
        self.pipe = media.get_element()
        appsrc = self.pipe.get_by_name('source')
        appsrc.set_property('device', self.device_path)

        self.pipe.set_state(Gst.State.PLAYING)
        ret, _, _ = self.pipe.get_state(Gst.CLOCK_TIME_NONE)
        if ret == Gst.StateChangeReturn.FAILURE:
            lprint("[RTSP] cant connect to device: " + self.device_path)
            self.stop()
        else:
            lprint(f"[RTSP] connect to device ({self.device_path})")

    def set_device_path(self, device_path):
        self.device_path = device_path

    def stop(self):
        if self.pipe is not None:
            self.pipe.send_event(Gst.Event.new_eos())


class DeviceData:
    process = None

    def __init__(self, serial, device_path, number, width, height, fps, is_docker, num):
        self.serial = serial
        port = DEFAULT_PORT + number
        self.addr = SERVICE_NAME + "-" + str(num).zfill(3) + "-srv:" + str(port) \
            if is_docker else "localhost:" + str(port)
        self.addr += DEFAULT_URI
        self.server = GstServer(port, width, height, fps, device_path)

        self.process = Process(target=self.server.start)
        self.process.start()
        lprint(f"[RTSP] ready at rtsp://{self.addr}")

    def get_serial(self):
        return self.serial

    def get_addr(self):
        return self.addr

    def set_device_path(self, device_path):
        self.server.set_device_path(device_path)

    def stop(self):
        self.server.stop()
        if self.process is not None:
            self.process.terminate()
            self.process.join()


class DeviceDataList:
    device_data_list = {}
    previous_device_list = []

    def start_rtsp_server(self, device_list: dict, scale: int, is_docker: bool, num: int):
        metadata_list = []
        # start device list
        for serial, path in device_list.items():
            lprint(f"Get device data (serial: {serial}, path: {path})")
            # set device path
            if self.device_data_list.get(serial):
                self.device_data_list[serial].set_device_path(path)

            # check over scale or already set in device list
            if len(self.previous_device_list) >= scale or serial in self.previous_device_list:
                continue

            # add new camera connection
            width = DEFAULT_WIDTH
            height = DEFAULT_HEIGHT
            fps = DEFAULT_FPS

            self.previous_device_list.append(serial)

            output_num = len(self.previous_device_list)
            device_data = DeviceData(serial, path, output_num, width, height, fps, is_docker, num)

            lprint(self.previous_device_list, output_num)

            metadata = {
                "width": width,
                "height": height,
                "framerate": fps,
                "addr": device_data.get_addr(),
            }
            metadata_list.append((metadata, output_num))
        return metadata_list

    def stop_all_device(self):
        for data in self.device_data_list:
            data.stop()


@main_decorator(SERVICE_NAME)
def main(opt: Options):
    conn = opt.get_conn()
    num = opt.get_number()

    scale = os.environ.get("SCALE")
    scale = 2 if not isinstance(scale, int) or scale <= 0 else scale
    debug = os.environ.get("DEBUG")
    device = DeviceDataList()

    # for debug
    if debug:
        conn.set_kanban(SERVICE_NAME, num)
        device.start_rtsp_server({"test": "/dev/video0"}, scale, opt.is_docker(), 1)
        while True:
            sleep(5)

    try:
        for kanban in conn.get_kanban_itr(SERVICE_NAME, num):
            device_list = kanban.get_metadata().get("device_list")
            if not device_list:
                continue
            metadata_list = device.start_rtsp_server(device_list, scale, opt.is_docker(), num)
            for metadata, num in metadata_list:
                lprint(metadata, num)
                conn.output_kanban(
                    metadata={
                        "type": "start",
                        "rtsp": metadata,
                    },
                    process_number=num,
                )
    finally:
        device.stop_all_device()
