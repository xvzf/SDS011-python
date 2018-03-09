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
import unittest

class PacketParseException(Exception):
    pass

class Sds011(object):
    """
    @TODO
    """
    
    baud = 9600 # 9600B8N1


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
        print(self.port)
        print("@TODO")
    

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
            print(packet[1:-2])
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


    def set_report_mode(self, data, id=None):
        """
        Sets the sensor reporting mode

        :param data: Data which should be set (first two data bytes)
        :id: Sensor ID, None for all sensors
        :return: Action successfull
        """
        id0, id1 = 0xFF, 0xFF # Set all sensors

        if id: # Specif ID required
            id0, id1 = id & 0xFF00, id & 0x00FF

        packetdict = {
            "cmd":  0xB4,
            # 2 is fixed, 1 for reporting mode, 1 for query mode, 0...., ID
            "data": [2, data[0], data[1], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, id0, id1]
        }

        request = self.build_packet(packetdict)
        print(request)
        # @TODO
        return True
    

    def set_report_query_mode(self, id=None) -> bool:
        """
        Sets the sensor in reporting active mode, i.e. the sensor transmits measuring data when it is queried

        :id: If only one Sensor ID should be set; leave default to set all sensors
        :return: Action successfull
        """

        return self.set_report_mode([1, 1], id)
    

    def set_report_active_mode(self, id=None) -> bool:
        """
        Sets the sensor in reporting active mode, i.e. the sensor transmits measuring data without a query

        :id: If only one Sensor ID should be set; leave default to set all sensors
        :return: Action successfull
        """

        return self.set_report_mode([1, 0], id)
        

if __name__ == "__main__":
    s = Sds011("")
    print(s.extract_data_from_incoming_packet(b"\xAA\xC0\xD4\x04\x3A\x0A\xA1\x60\x1D\xAB"))
    print("===================")
    s.set_report_active_mode()
    print("===================")
    s.set_report_query_mode()
