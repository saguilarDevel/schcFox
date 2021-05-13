import binascii
import unittest

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import SigfoxProfile
from Messages.ACK import ACK
from Messages.ACKHeader import ACKHeader
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from schc_utils import bitstring_to_bytes, is_monochar


class TestFragmentHeader(unittest.TestCase):
    def test_to_string(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = FragmentHeader(profile, rule_id, dtag, w, fcn)
        s = header.to_string()

        self.assertEqual(s, "00000000")

    def test_to_bytes(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "1" * profile.N
        header = FragmentHeader(profile, rule_id, dtag, w, fcn)
        b = header.to_bytes()
        self.assertEqual(b, b"\x07")


class TestACKHeader(unittest.TestCase):
    def test_to_string(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        c = "0"
        header = ACKHeader(profile, rule_id, dtag, w, c)
        s = header.to_string()

        self.assertEqual(s, "000000")


class TestFragment(unittest.TestCase):
    def test_is_all_0(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_0())

    def test_is_all_1(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "1" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])

        self.assertTrue(fragment.is_all_1())

    def test_to_string(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        rule_id = "0" * profile.RULE_ID_SIZE
        dtag = "0" * profile.T
        w = "0" * profile.M
        fcn = "0" * profile.N
        header = bitstring_to_bytes(rule_id + dtag + w + fcn)
        payload = bytearray.fromhex("3131313231333134313531")
        fragment = Fragment(profile, [header, payload])
        print(fragment.to_string())


class TestAck(unittest.TestCase):
    def test_from_hex(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        h = "0f08000000000000"
        ack = ACK.parse_from_hex(profile, h)
        self.assertEqual(ack.to_string(), "0000111100001000000000000000000000000000000000000000000000000000")
        self.assertEqual(ack.HEADER.RULE_ID, "00")
        self.assertEqual(ack.HEADER.DTAG, "0")
        self.assertEqual(ack.HEADER.W, "01")
        self.assertEqual(ack.HEADER.C, "1")
        self.assertEqual(ack.BITMAP, "1100001")
        self.assertTrue(is_monochar(ack.PADDING) and ack.PADDING[0] == '0')

    def test_from_bytes(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 2)
        b = b'\xf0/\xbf\xff\x00 \x00\x00'
        ack = ACK.parse_from_bytes(profile, b)
        self.assertEqual(ack.to_string(), "1111000000101111101111111111111100000000001000000000000000000000")
        self.assertEqual(ack.HEADER.RULE_ID, "1111000")
        self.assertEqual(ack.HEADER.DTAG, "0")
        self.assertEqual(ack.HEADER.W, "001")
        self.assertEqual(ack.HEADER.C, "0")
        self.assertEqual(ack.BITMAP, "1111101111111111111100000000001")
        self.assertTrue(is_monochar(ack.PADDING) and ack.PADDING[0] == '0')

    def test_last_bitmap(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        message = '12345678912123456789121234567891212345678912123456789121234567891212345678912'
        fragments = Fragmenter(profile, message).fragment()
        bitmap = '1001111'
        last_bitmap = bitmap[:(len(fragments) - 1) % profile.WINDOW_SIZE]
        self.assertEqual(last_bitmap, bitmap[:-1])

        message = '123456789121234567891212345678912123456789121234567891212345678912123456789123' \
                  '456789123456789121234567891212345678912123456789123456789123456789121234'
        fragments = Fragmenter(profile, message).fragment()
        bitmap = '1001111'
        last_bitmap = bitmap[:(len(fragments) - 1) % profile.WINDOW_SIZE]
        self.assertEqual(last_bitmap, bitmap[:-1])

        message = '123456789121234567891212345678912123456789121234567891212345678912123456789123456789123456'
        fragments = Fragmenter(profile, message).fragment()
        bitmap = '1000001'
        last_bitmap = bitmap[:(len(fragments) - 1) % profile.WINDOW_SIZE]
        self.assertEqual(last_bitmap, bitmap[:1])

        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        for list_length in range(1, profile.WINDOW_SIZE):
            bitmap = '1111111'
            last_bitmap = bitmap[:(list_length - 1) % profile.WINDOW_SIZE]
            self.assertEqual(len(last_bitmap), (list_length - 1) % profile.WINDOW_SIZE)

        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 2)
        for list_length in range(1, profile.WINDOW_SIZE):
            bitmap = '1' * profile.BITMAP_SIZE
            last_bitmap = bitmap[:(list_length - 1) % profile.WINDOW_SIZE]
            self.assertEqual(len(last_bitmap), (list_length - 1) % profile.WINDOW_SIZE)

class TestSenderAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = SenderAbort(profile, fragment.HEADER)

        self.assertEqual(type(abort.PROFILE), SigfoxProfile)
        self.assertEqual(abort.HEADER.RULE_ID, fragment.HEADER.RULE_ID)
        self.assertEqual(abort.HEADER.DTAG, fragment.HEADER.DTAG)
        self.assertEqual(abort.HEADER.W, fragment.HEADER.W)
        self.assertTrue(abort.HEADER.FCN[0] == '1' and all(abort.HEADER.FCN),
                        msg=f"{abort.HEADER.FCN[0] == '1'} and {all(abort.HEADER.FCN)}")
        self.assertTrue(abort.PAYLOAD.decode()[0] == '0' and all(abort.PAYLOAD.decode()),
                        msg=f"{abort.PAYLOAD[0] == '0'} and {all(abort.PAYLOAD)}")
        self.assertFalse(abort.is_all_1())
        self.assertTrue(abort.is_sender_abort())

        hex_data = "1f353235"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)

        self.assertFalse(fragment.is_sender_abort())

    def test_all_1(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        hex_data = '073132333435363738393132'
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        fragment = Fragment(profile, [header, payload])
        abort = SenderAbort(fragment.PROFILE, fragment.HEADER)

        self.assertEqual(len(abort.HEADER.to_string()), profile.HEADER_LENGTH)
        self.assertLessEqual(len(fragment.PAYLOAD), len(abort.PAYLOAD))
        self.assertEqual(len(abort.PAYLOAD), (profile.UPLINK_MTU - profile.HEADER_LENGTH) / 8)
        self.assertEqual(type(abort.PROFILE), SigfoxProfile)
        self.assertEqual(abort.HEADER.RULE_ID, fragment.HEADER.RULE_ID)
        self.assertEqual(abort.HEADER.DTAG, fragment.HEADER.DTAG)
        self.assertEqual(abort.HEADER.W, fragment.HEADER.W)
        self.assertTrue(abort.HEADER.FCN[0] == '1' and all(abort.HEADER.FCN),
                        msg=f"{abort.HEADER.FCN[0] == '1'} and {all(abort.HEADER.FCN)}")
        self.assertTrue(abort.PAYLOAD.decode()[0] == '0' and all(abort.PAYLOAD.decode()),
                        msg=f"{abort.PAYLOAD[0] == '0'} and {all(abort.PAYLOAD)}")
        self.assertFalse(abort.is_all_1())
        self.assertTrue(abort.is_sender_abort())


class TestReceiverAbort(unittest.TestCase):
    def test_init(self):
        hex_data = "053131313231333134313531"
        header = bytes.fromhex(hex_data[:2])
        payload = bytearray.fromhex(hex_data[2:])
        data = [header, payload]
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        fragment = Fragment(profile, data)
        abort = ReceiverAbort(profile, fragment.HEADER)

        self.assertEqual(len(abort.to_string()), profile.DOWNLINK_MTU)
        self.assertEqual(type(abort.PROFILE), SigfoxProfile)
        self.assertEqual(abort.HEADER.RULE_ID, fragment.HEADER.RULE_ID)
        self.assertEqual(abort.HEADER.DTAG, fragment.HEADER.DTAG)
        self.assertEqual(abort.HEADER.W, fragment.HEADER.W)
        self.assertEqual(len(abort.to_string()), 64)
        self.assertTrue(issubclass(type(abort), ACK))
        self.assertTrue(abort.is_receiver_abort())

    def test_receive(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
        ack = "0000111111111111100000000000000000000000000000000000000000000000"
        ack_index_dtag = profile.RULE_ID_SIZE
        ack_index_w = ack_index_dtag + profile.T
        ack_index_c = ack_index_w + profile.M
        ack_index_bitmap = ack_index_c + 1
        ack_index_padding = ack_index_bitmap + profile.BITMAP_SIZE

        received_ack = ACK(profile,
                           rule_id=ack[:ack_index_dtag],
                           dtag=ack[ack_index_dtag:ack_index_w],
                           w=ack[ack_index_w:ack_index_c],
                           c=ack[ack_index_c],
                           bitmap=ack[ack_index_bitmap:ack_index_padding],
                           padding=ack[ack_index_padding:])

        self.assertTrue(received_ack.is_receiver_abort())

    def test_receive_2byte(self):
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 2)
        frag_hex = 'f03439313231323334353637'
        header = bytes.fromhex(frag_hex[:4])
        payload = bytearray.fromhex(frag_hex[4:])
        fragment = Fragment(profile, [header, payload])
        abort = ReceiverAbort(profile, fragment.HEADER)
        self.assertTrue(abort.is_receiver_abort())
        ack_hex = 'f03fff0000000000'
        ack_object = ACK.parse_from_hex(profile, ack_hex)
        ack_object.HEADER.to_string()
        self.assertTrue(abort.is_receiver_abort())

    def test_from_hex(self):
        ack = ACK.parse_from_hex(SigfoxProfile("UPLINK", "ACK ON ERROR", 1), "07ff800000000000")
        self.assertEqual(ack.to_string(),
                         "0000011111111111100000000000000000000000000000000000000000000000")
        self.assertEqual(ack.HEADER.RULE_ID, "00")
        self.assertEqual(ack.HEADER.DTAG, "0")
        self.assertEqual(ack.HEADER.W, "00")
        self.assertEqual(ack.HEADER.C, "1")
        self.assertTrue(ack.is_receiver_abort())


class TestFragmenter(unittest.TestCase):
    def test_two_byte(self):
        message = "123456789121234567891212345678912123456789121234567891212345" \
                  "678912123456789123456789123456789121234567891212345678912123" \
                  "456789123456789123456789121234456789121234567891212345678912" \
                  "123456789121234567891212345678912345634567891234567341234567" \
                  "891212345678912123456789121234567891212345678912123456789121" \
                  "234567891234567891234567891212345678912123456789121234567891" \
                  "234567891234567891212344567891212345678912123456789121234567" \
                  "891212345678912123456789123456345678912345673491212345678912" \
                  "34567891234567891212345678912123 "

        header_bytes = 1 if len(message) <= 300 else 2
        profile = SigfoxProfile("UPLINK", "ACK ON ERROR", header_bytes)
        fragmenter = Fragmenter(profile, message)
        fragments = fragmenter.fragment()
        first_byte = fragments[0][0][0]
        equal = True
        for fragment in fragments:
            if fragment[0][0] != first_byte:
                equal = False
                break

        self.assertTrue(equal)

if __name__ == '__main__':
    unittest.main()
