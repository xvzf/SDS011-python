#!/usr/bin/env python3

#
#   Library for the SDS011 air quality sensor
# 
#       Filename:   sds011.py
#       Author:     Matthias Riegler <matthias@xvzf.tech>
#

from serial import Serial
from binascii import hexlify, unhexlify
from struct import unpack, pack
import time
# import asyncio # @TODO

class PacketParseException(Exception):
    pass

class Sds011(object):
    """
    Python library for the nova PM SDS011 dust sensor
    """
    
    baud = 9600 # 9600B8N1
    outgoing_cmd = 0xB4
    incoming_cmd = 0xC4


    def __init__(self, port):
        """
        Class constructor
        :param port: Serial port to which the sensor is connected
        """
        self.port = port
        self.init_connection()


    def init_connection(self):
        """
        Initializes the serial connection
        """
        self.conn = Serial(self.port, self.baud)
    

    def request(self, bytestring: bytes) -> bytes:
        """
        Send request to the sensor

        :param bytestring: Packet which should be send
        :return: Response
        """
        self.conn.reset_input_buffer() # Default mode is active reporting, just to make sure
 
        self.conn.write(bytestring)
 
        while self.conn.in_waiting < 10:
            time.sleep(0.05)
        
        return self.conn.read(10)
   

    def extract_data_from_incoming_packet(self, packet: bytes, unpack_scheme="<BHHHB") -> dict:
        """
        Decodes an incoming packet

        :param packet: bytestring of the received packet
        :param unpack_scheme: unpack scheme for struct.unpack(), default is "<BHHHB", other needed for other command types
        :return: Dictionary containing "cmd", "data", "checksum"
        """

        if not packet[0] != b"\xAA" and not packet[-1] != b"\xAB":
            raise PacketParseException("No matching tags")

        try:
            tmp = list(unpack(unpack_scheme, packet[1:-1]))
        except:
            raise PacketParseException("Bytestream mismatch")

        toreturn = {
            "cmd": tmp[0],
            "data": tmp[1:-1],
            "checksum": tmp[-1]
        }

        # Validate checksum
        if toreturn["checksum"] != Sds011.checksum_incoming(packet):
            raise PacketParseException("Checksum missmatch")

        return toreturn

        
    def build_packet(self, packetdict: dict) -> bytes:
        """
        Builds a packet
        
        :param packetdict: Should contain: "cmd", "data" (this time 15 bytes!!)
        :return: bytestring which can be transmitted
        """
        # Head, CommandID, Data, Checksum, Tail
        packet = b"\xAA"
        # Add data
        packet += pack("BBBBBBBBBBBBBBBB", *([packetdict["cmd"]]+ packetdict["data"]))
        # Add Checksum
        packet += pack("B", Sds011.checksum_outgoing(packet))
        # Add Tail
        packet += b"\xAB"

        return packet
    

    def build_packet_basic(self, data: list, ID=None) -> bytes:
        """
        Builds a packet using just the first n data bytes and the ID

        :param data: Data bytes (up to 13)
        :param ID: If only one sensor should be adressed, pass its ID here
        :return: packet bytestring
        """

        # Data bytes, 0 byte padding, ID
        data = [b for b in data] + [0] * (13 - len(data)) + Sds011.get_ID_bytes(ID)

        packetdict = {
            "cmd":  self.outgoing_cmd,
            "data": data
        }

        return self.build_packet(packetdict)
    
    
    @staticmethod
    def get_ID_bytes(ID=None) -> list:
        """
        Splits the ID into two bytes

        :param ID: 16-bit ID
        :return: two 8 bit values
        """
        ID0, ID1 = 0xFF, 0xFF

        if ID: # Specific ID required
            ID1, ID0 = (ID & 0xFF00) >> 8, ID & 0xFF
        
        return [ID0, ID1]


    
    @staticmethod
    def checksum_incoming(packet: bytes) -> int:
        """
        Calculates the checksum of incoming data packets

        :param packet: Received bytestring
        :return: Calculated checksum
        """
        return Sds011.checksum(packet[2:8])
    

    @staticmethod
    def checksum_outgoing(packet: bytes) -> int:
        """
        Calculates the checksum of outgoing data packets

        :param packet: Bytestring which should be send
        :return: Calculated checksum
        """
        return Sds011.checksum(packet[2:17])


    @staticmethod 
    def checksum(togenerate: bytes) -> int:
        """
        Calculates checksum

        :param togenerate: String for which the checksum should be created
        :return: Calculated checksum
        """
        checksum = 0
        for i in togenerate:
            checksum += i
            checksum &= 0xFF
        
        return checksum


    def set_report_mode(self, data, ID=None):
        """
        Sets the sensor reporting mode

        :param data: Data which should be set (two data bytes)
        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Action successfull
        """
        request = self.build_packet_basic( [2] + data, ID)
        response = self.request(request)
        # @TODO Check response
        return True
    

    def set_report_query_mode(self, ID=None) -> bool:
        """
        Changes the sensor reporting mode

        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Action successfull
        """

        return self.set_report_mode([1, 1], ID)
    

    def set_report_active_mode(self, ID=None) -> bool:
        """
        @NOTRECOMMENDED !!!
        Sets the sensor in reporting active mode, i.e. the sensor transmits measuring data without a query

        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Action successfull
        """

        return self.set_report_mode([1, 0], ID)
    

    def set_new_device_ID(self, newID: int, ID=None) -> bool:
        """
        Sets a new device ID (16-bit)

        :param newID: New device ID
        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Action successfull
        """

        # 5 for ID change, 0.. , old ID, new ID
        request = self.build_packet_basic( [5] + [0] * 10 + Sds011.get_ID_bytes(newID))
        response = self.request(request)
        # @TODO check response
        return True
    

    def set_sleep_work_mode(self, data: list, ID=None) -> bool:
        """
        Changes the sensors operating mode

        :param data: Data which should be set (two data bytes)
        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Action successfull
        """
        request = self.build_packet_basic([6] + data, ID)
        response = self.request(request)
        # @TODO Check response
        print(response)
        return True
    

    def set_sleep_mode(self, ID=None) -> bool:
        """
        Changes the sensors operating mode to sleep

        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Actuon successfull
        """
        self.set_sleep_work_mode([1, 0], ID)
    

    def set_work_mode(self, ID=None) -> bool:
        """
        Changes the sensors operating mode to sleep

        :param ID: If only one sensor should be adressed, pass its ID here
        :return: Actuon successfull
        """
        self.set_sleep_work_mode([1,1], ID)
    

    def query_data(self, ID=None) -> (float, float, int):
        """
        Queries the sensor and reports back PM2.5 and PM10

        :param ID: If only one sensor should be adressed, pass its ID here
        :return: PM2.5 and PM10 value additional the sensor ID
        """
        request = self.build_packet_basic([4], ID)
        response = self.request(request)

        data = [-1, -1, -1]

        try:
            data = self.extract_data_from_incoming_packet(response)["data"]
        except PacketParseException:
            print("Could not query, is the device in response query mode?")
            pass

        return (data[0] / 10.0, data[1] / 10.0, data[2])