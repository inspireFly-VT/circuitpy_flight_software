# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
MODIFIED VERSION of adafruit_rfm9x CircuitPython Library for PyCubed Use
See https://github.com/adafruit/Adafruit_CircuitPython_RFM9x

CircuitPython Version: 7.0.0 alpha
Library Repo: https://github.com/pycubed/library_pycubed.py
* Edits by: Max Holliday
Added temperature readout by Nicole Maggard
"""
import time
from random import random
import digitalio
from micropython import const
import adafruit_bus_device.spi_device as spidev

# pylint: disable=bad-whitespace
# Internal constants:
# Register names (FSK Mode even though we use LoRa instead, from table 85)
_RH_RF95_REG_00_FIFO = const(0x00)
_RH_RF95_REG_01_OP_MODE = const(0x01)
_RH_RF95_REG_06_FRF_MSB = const(0x06)
_RH_RF95_REG_07_FRF_MID = const(0x07)
_RH_RF95_REG_08_FRF_LSB = const(0x08)
_RH_RF95_REG_09_PA_CONFIG = const(0x09)
_RH_RF95_REG_0A_PA_RAMP = const(0x0A)
_RH_RF95_REG_0B_OCP = const(0x0B)
_RH_RF95_REG_0C_LNA = const(0x0C)
_RH_RF95_REG_0D_FIFO_ADDR_PTR = const(0x0D)
_RH_RF95_REG_0E_FIFO_TX_BASE_ADDR = const(0x0E)
_RH_RF95_REG_0F_FIFO_RX_BASE_ADDR = const(0x0F)
_RH_RF95_REG_10_FIFO_RX_CURRENT_ADDR = const(0x10)
_RH_RF95_REG_11_IRQ_FLAGS_MASK = const(0x11)
_RH_RF95_REG_12_IRQ_FLAGS = const(0x12)
_RH_RF95_REG_13_RX_NB_BYTES = const(0x13)
_RH_RF95_REG_14_RX_HEADER_CNT_VALUE_MSB = const(0x14)
_RH_RF95_REG_15_RX_HEADER_CNT_VALUE_LSB = const(0x15)
_RH_RF95_REG_16_RX_PACKET_CNT_VALUE_MSB = const(0x16)
_RH_RF95_REG_17_RX_PACKET_CNT_VALUE_LSB = const(0x17)
_RH_RF95_REG_18_MODEM_STAT = const(0x18)
_RH_RF95_REG_19_PKT_SNR_VALUE = const(0x19)
_RH_RF95_REG_1A_PKT_RSSI_VALUE = const(0x1A)
_RH_RF95_REG_1B_RSSI_VALUE = const(0x1B)
_RH_RF95_REG_1C_HOP_CHANNEL = const(0x1C)
_RH_RF95_REG_1D_MODEM_CONFIG1 = const(0x1D)
_RH_RF95_REG_1E_MODEM_CONFIG2 = const(0x1E)
_RH_RF95_REG_1F_SYMB_TIMEOUT_LSB = const(0x1F)
_RH_RF95_REG_20_PREAMBLE_MSB = const(0x20)
_RH_RF95_REG_21_PREAMBLE_LSB = const(0x21)
_RH_RF95_REG_22_PAYLOAD_LENGTH = const(0x22)
_RH_RF95_REG_23_MAX_PAYLOAD_LENGTH = const(0x23)
_RH_RF95_REG_24_HOP_PERIOD = const(0x24)
_RH_RF95_REG_25_FIFO_RX_BYTE_ADDR = const(0x25)
_RH_RF95_REG_26_MODEM_CONFIG3 = const(0x26)

_RH_RF95_REG_3C_REGTEMP = const(0x3C)

_RH_RF95_REG_40_DIO_MAPPING1 = const(0x40)
_RH_RF95_REG_41_DIO_MAPPING2 = const(0x41)
_RH_RF95_REG_42_VERSION = const(0x42)

_RH_RF95_REG_4B_TCXO = const(0x4B)
_RH_RF95_REG_4D_PA_DAC = const(0x4D)
_RH_RF95_REG_5B_FORMER_TEMP = const(0x5B)
_RH_RF95_REG_61_AGC_REF = const(0x61)
_RH_RF95_REG_62_AGC_THRESH1 = const(0x62)
_RH_RF95_REG_63_AGC_THRESH2 = const(0x63)
_RH_RF95_REG_64_AGC_THRESH3 = const(0x64)

_RH_RF95_DETECTION_OPTIMIZE = const(0x31)
_RH_RF95_DETECTION_THRESHOLD = const(0x37)

_RH_RF95_PA_DAC_DISABLE = const(0x04)
_RH_RF95_PA_DAC_ENABLE = const(0x07)

# The Frequency Synthesizer step = RH_RF95_FXOSC / 2^^19
_RH_RF95_FSTEP = 32000000 / 524288

# RadioHead specific compatibility constants.
_RH_BROADCAST_ADDRESS = const(0xFF)

# The acknowledgement bit in the FLAGS
# The top 4 bits of the flags are reserved for RadioHead. The lower 4 bits are reserved
# for application layer use.
_RH_FLAGS_ACK = const(0x80)
_RH_FLAGS_RETRY = const(0x40)

# User facing constants:
SLEEP_MODE  = const(0)#0b000
STANDBY_MODE= const(1)#0b001
FS_TX_MODE  = const(2)#0b010
TX_MODE     = const(3)#0b011
FS_RX_MODE  = const(4)#0b100
RX_MODE     = const(5)#0b101
# pylint: enable=bad-whitespace

# gap =bytes([0xFF])
# sgap=bytes([0xFF,0xFF,0xFF])
# dot =bytes([0])
# dash=bytes([0,0,0])
# # ...- .-. ...-- -..-
# VR3X = (gap+(dot+gap)*3)+dash+sgap+\
# (dot+gap)+dash+gap+dot+sgap+\
# ((dot+gap)*3)+dash+gap+dash+sgap+\
# dash+gap+((dot+gap)*2)+dash+gap
VR3X=b'\xff\x00\xff\x00\xff\x00\xff\x00\x00\x00\xff\xff\xff\x00\xff\x00\x00\x00\xff\x00\xff\xff\xff\x00\xff\x00\xff\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\xff\xff\x00\x00\x00\xff\x00\xff\x00\xff\x00\x00\x00\xff'


# Disable the too many instance members warning.  Pylint has no knowledge
# of the context and is merely guessing at the proper amount of members.  This
# is a complex chip which requires exposing many attributes and state.  Disable
# the warning to work around the error.
# pylint: disable=too-many-instance-attributes

_bigbuffer=bytearray(256)
bw_bins = (7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000)
class RFM9x:
    """Interface to a RFM95/6/7/8 LoRa radio module.  Allows sending and
    receivng bytes of data in long range LoRa mode at a support board frequency
    (433/915mhz).

    You must specify the following parameters:
    - spi: The SPI bus connected to the radio.
    - cs: The CS pin DigitalInOut connected to the radio.
    - reset: The reset/RST pin DigialInOut connected to the radio.
    - frequency: The frequency (in mhz) of the radio module (433/915mhz typically).

    You can optionally specify:
    - preamble_length: The length in bytes of the packet preamble (default 8).
    - high_power: Boolean to indicate a high power board (RFM95, etc.).  Default
    is True for high power.
    - baudrate: Baud rate of the SPI connection, default is 10mhz but you might
    choose to lower to 1mhz if using long wires or a breadboard.

    Remember this library makes a best effort at receiving packets with pure
    Python code.  Trying to receive packets too quickly will result in lost data
    so limit yourself to simple scenarios of sending and receiving single
    packets at a time.

    Also note this library tries to be compatible with raw RadioHead Arduino
    library communication. This means the library sets up the radio modulation
    to match RadioHead's defaults and assumes that each packet contains a
    4 byte header compatible with RadioHead's implementation.
    Advanced RadioHead features like address/node specific packets
    or "reliable datagram" delivery are supported however due to the
    limitations noted, "reliable datagram" is still subject to missed packets but with it,
    sender is notified if a packet has potentially been missed.
    """

    # Global buffer for SPI commands
    _BUFFER = bytearray(4)
    DEBUG_HEADER=False
    valid_ids  = (58,59,60,255)
    class _RegisterBits:        # Class to simplify access to the many configuration bits avaialable
        # on the chip's registers.  This is a subclass here instead of using
        # a higher level module to increase the efficiency of memory usage
        # (all of the instances of this bit class will share the same buffer
        # used by the parent RFM69 class instance vs. each having their own
        # buffer and taking too much memory).

        # Quirk of pylint that it requires public methods for a class.  This
        # is a decorator class in Python and by design it has no public methods.
        # Instead it uses dunder accessors like get and set below.  For some
        # reason pylint can't figure this out so disable the check.
        # pylint: disable=too-few-public-methods

        # Again pylint fails to see the true intent of this code and warns
        # against private access by calling the write and read functions below.
        # This is by design as this is an internally used class.  Disable the
        # check from pylint.
        # pylint: disable=protected-access

        def __init__(self, address, *, offset=0, bits=1):
            assert 0 <= offset <= 7
            assert 1 <= bits <= 8
            assert (offset + bits) <= 8
            self._address = address
            self._mask = 0
            for _ in range(bits):
                self._mask <<= 1
                self._mask |= 1
            self._mask <<= offset
            self._offset = offset

        def __get__(self, obj, objtype):
            reg_value = obj._read_u8(self._address)
            return (reg_value & self._mask) >> self._offset

        def __set__(self, obj, val):
            reg_value = obj._read_u8(self._address)
            reg_value &= ~self._mask
            reg_value |= (val & 0xFF) << self._offset
            obj._write_u8(self._address, reg_value)

    operation_mode = _RegisterBits(_RH_RF95_REG_01_OP_MODE, bits=3)

    low_frequency_mode = _RegisterBits(_RH_RF95_REG_01_OP_MODE, offset=3, bits=1)

    osc_calibration   = _RegisterBits(_RH_RF95_REG_24_HOP_PERIOD, offset=3, bits=1)

    modulation_type = _RegisterBits(_RH_RF95_REG_01_OP_MODE, offset=5, bits=2)

    # Long range/LoRa mode can only be set in sleep mode!
    long_range_mode = _RegisterBits(_RH_RF95_REG_01_OP_MODE, offset=7, bits=1)


    lna_boost = _RegisterBits(_RH_RF95_REG_0C_LNA, bits=2)

    output_power = _RegisterBits(_RH_RF95_REG_09_PA_CONFIG, bits=4)

    modulation_shaping = _RegisterBits(_RH_RF95_REG_0A_PA_RAMP, bits=2)

    pa_ramp = _RegisterBits(_RH_RF95_REG_0A_PA_RAMP, bits=4)

    max_power = _RegisterBits(_RH_RF95_REG_09_PA_CONFIG, offset=4, bits=3)

    pa_select = _RegisterBits(_RH_RF95_REG_09_PA_CONFIG, offset=7, bits=1)

    pa_dac = _RegisterBits(_RH_RF95_REG_4D_PA_DAC, bits=3)

    dio0_mapping = _RegisterBits(_RH_RF95_REG_40_DIO_MAPPING1, offset=6, bits=2)

    low_datarate_optimize = _RegisterBits(_RH_RF95_REG_26_MODEM_CONFIG3, offset=3, bits=1)
    auto_agc  = _RegisterBits(_RH_RF95_REG_26_MODEM_CONFIG3, offset=2, bits=1)

    debug=False
    buffview = memoryview(_bigbuffer)
    def __init__(
        self,
        spi,
        cs,
        reset,
        frequency,
        *,
        preamble_length=8,
        code_rate=5,
        high_power=True,
        baudrate=5000000,
        max_output=False
    ):
        self.high_power = high_power
        self.max_output=max_output
        self.dio0=False
        # Device support SPI mode 0 (polarity & phase = 0) up to a max of 10mhz.
        # Set Default Baudrate to 5MHz to avoid problems
        self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        # Setup reset as a digital input (default state for reset line according
        # to the datasheet).  This line is pulled low as an output quickly to
        # trigger a reset.  Note that reset MUST be done like this and set as
        # a high impedence input or else the chip cannot change modes (trust me!).
        self._reset = reset
        self._reset.switch_to_input(pull=digitalio.Pull.UP)
        self.reset()
        # No device type check!  Catch an error from the very first request and
        # throw a nicer message to indicate possible wiring problems.
        version = self._read_u8(_RH_RF95_REG_42_VERSION)
        if version != 18:
            raise RuntimeError(
                "Failed to find rfm9x with expected version -- check wiring"
            )

        # Set sleep mode, wait 10ms and confirm in sleep mode (basic device check).
        # Also set long range mode (LoRa mode) as it can only be done in sleep.
        self.idle()
        time.sleep(0.01)
        self.osc_calibration=True
        time.sleep(1)

        self.sleep()
        time.sleep(0.01)
        self.long_range_mode = True
        if self.operation_mode != SLEEP_MODE or not self.long_range_mode:
             raise RuntimeError("Failed to configure radio for LoRa mode, check wiring!")
        # clear default setting for access to LF registers if frequency > 525MHz
        if frequency > 525:
            self.low_frequency_mode = 0
        # Setup entire 256 byte FIFO
        self._write_u8(_RH_RF95_REG_0E_FIFO_TX_BASE_ADDR, 0x00)
        self._write_u8(_RH_RF95_REG_0F_FIFO_RX_BASE_ADDR, 0x00)
        # Disable Freq Hop
        self._write_u8(_RH_RF95_REG_24_HOP_PERIOD, 0x00)
        # Set mode idle
        self.idle()


        # Set frequency
        self.frequency_mhz = frequency
        # Set preamble length (default 8 bytes to match radiohead).
        self.preamble_length = preamble_length
        # Defaults set modem config to RadioHead compatible Bw125Cr45Sf128 mode.
        self.signal_bandwidth = 125000
        self.coding_rate = code_rate
        self.spreading_factor = 7
        # Default to disable CRC checking on incoming packets.
        self.enable_crc = False
        # Note no sync word is set for LoRa mode either!
        self._write_u8(_RH_RF95_REG_26_MODEM_CONFIG3, 0x00)
        # Set transmit power to 13 dBm, a safe value any module supports.
        self.tx_power = 13
        # initialize last RSSI reading
        self.last_rssi = 0.0
        """The RSSI of the last received packet. Stored when the packet was received.
           This instantaneous RSSI value may not be accurate once the
           operating mode has been changed.
        """
        # initialize timeouts and delays delays
        self.ack_wait = 0.5
        """The delay time before attempting a retry after not receiving an ACK"""
        self.receive_timeout = 0.5
        """The amount of time to poll for a received packet.
           If no packet is received, the returned packet will be None
        """
        self.xmit_timeout = 2.0
        """The amount of time to wait for the HW to transmit the packet.
           This is mainly used to prevent a hang due to a HW issue
        """
        self.ack_retries = 5
        """The number of ACK retries before reporting a failure."""
        self.ack_delay = None
        """The delay time before attemting to send an ACK.
           If ACKs are being missed try setting this to .1 or .2.
        """
        # initialize sequence number counter for reliabe datagram mode
        self.sequence_number = 0
        # create seen Ids list
        self.seen_ids = bytearray(256)
        # initialize packet header
        # node address - default is broadcast
        self.node = _RH_BROADCAST_ADDRESS
        """The default address of this Node. (0-255).
           If not 255 (0xff) then only packets address to this node will be accepted.
           First byte of the RadioHead header.
        """
        # destination address - default is broadcast
        self.destination = _RH_BROADCAST_ADDRESS
        """The default destination address for packet transmissions. (0-255).
           If 255 (0xff) then any receiving node should accept the packet.
           Second byte of the RadioHead header.
        """
        # ID - contains seq count for reliable datagram mode
        self.identifier = 0
        """Automatically set to the sequence number when send_with_ack() used.
           Third byte of the RadioHead header.
        """
        # flags - identifies ack/reetry packet for reliable datagram mode
        self.flags = 0
        """Upper 4 bits reserved for use by Reliable Datagram Mode.
           Lower 4 bits may be used to pass information.
           Fourth byte of the RadioHead header.
        """
        self.crc_error_count = 0

        self.auto_agc=True
        self.pa_ramp=0   # mode agnostic
        self.lna_boost=3 # mode agnostic

    def cw(self,msg=None):
        success=False
        if msg is None:
            msg = VR3X

        cache=[]
        if self.long_range_mode:
            # cache LoRa params
            cache = [self.spreading_factor,
                    self.signal_bandwidth,
                    self.coding_rate,
                    self.preamble_length,
                    self.enable_crc]

        self.operation_mode = SLEEP_MODE
        time.sleep(0.01)
        self.long_range_mode=False # FSK/OOK Mode
        self.modulation_type=0 # FSK
        self.modulation_shaping = 2
        self._write_u8(0x25,0x00) # no preamble
        self._write_u8(0x26,0x00) # no preamble
        self._write_u8(0x27,0x00) # no sync word
        self._write_u8(0x3f,10)   # clear FIFO
        self._write_u8(0x02,0xFF) # BitRate(15:8)
        self._write_u8(0x03,0xFF) # BitRate(15:8)
        self._write_u8(0x05,11)   # Freq deviation Lsb 600 Hz
        self.idle()
        # Set payload length VR3X Morse length = 51
        self._write_u8(0x35,len(msg)-1)
        self._write_from(_RH_RF95_REG_00_FIFO, bytearray(msg.encode('utf-8')))

        _t=time.monotonic() + 10
        self.operation_mode = TX_MODE
        while time.monotonic() < _t:
            a=self._read_u8(0x3f)
            # print(a,end=' ')
            if (a>>6)&1:
                time.sleep(0.01)
                success=True
                break
        if not (a>>6)&1:
            print('cw timeout')
        self.idle()
        if cache:
            self.operation_mode = SLEEP_MODE
            time.sleep(0.01)
            self.long_r