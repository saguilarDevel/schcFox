from Entities.SigfoxProfile import SigfoxProfile
from Messages.ACK import ACK
from Messages.ACKHeader import ACKHeader
from Messages.Fragment import Fragment
from Messages.FragmentHeader import FragmentHeader
from Messages.ReceiverAbort import ReceiverAbort
from Messages.SenderAbort import SenderAbort
from schc_utils import bitstring_to_bytes, is_monochar

profile = SigfoxProfile("UPLINK", "ACK ON ERROR", 1)
byte_data = b'073132333435363738393132'
header = byte_data[:profile.HEADER_LENGTH]
payload = byte_data[profile.HEADER_LENGTH:]
fragment = Fragment(profile, [header, payload])
abort = SenderAbort(fragment.PROFILE, fragment.HEADER)
print(len(abort.HEADER.to_string()) == profile.HEADER_LENGTH)
print(len(abort.PAYLOAD) == profile.UPLINK_MTU - profile.HEADER_LENGTH)
print(abort.PROFILE)
print(type(abort.PROFILE) == SigfoxProfile)
print(abort.HEADER.RULE_ID == fragment.HEADER.RULE_ID)
print(abort.HEADER.DTAG == fragment.HEADER.DTAG)
print(abort.HEADER.W == fragment.HEADER.W)
print(abort.HEADER.FCN[0] == '1' and all(abort.HEADER.FCN))
print(abort.PAYLOAD.decode()[0] == '0' and all(abort.PAYLOAD.decode()))
print(not abort.is_all_1())
print(abort.is_sender_abort())
