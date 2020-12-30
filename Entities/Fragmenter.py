# -*- coding: utf-8 -*-

from math import ceil, floor
from Messages.Header import Header, HeaderNoACK

def zfill(string, width):
    if len(string) < width:
        return ("0" * (width - len(string))) + string
    else:
        return string

class Fragmenter:
	profile = None
	schc_packet = None

	def __init__(self, profile, schc_packet):
		self.profile = profile
		self.schc_packet = schc_packet

	def fragment(self):
		payload_max_length = int((self.profile.MTU - self.profile.HEADER_LENGTH) / 8)
		message = self.schc_packet
		fragment_list = []
		n = self.profile.N
		m = self.profile.M
		number_of_fragments = int(ceil(float(len(message)) / payload_max_length))
		if len(message) == 0: number_of_fragments = 1 #This is used to send 0-Payload SCHC Packets

		print("[FRGM] Fragmenting message into " + str(number_of_fragments) + " pieces...")
		
		#check if the packet size can be transmitted or not
		if len(fragment_list) > (2 ** self.profile.M) * self.profile.WINDOW_SIZE:
			print(len(fragment_list))
			print((2 ** self.profile.M) * self.profile.WINDOW_SIZE)
			print("The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be selected.")
			# What does this mean?
			# Sending packet does not fit (should be tested in fragmentation)


		for i in range(number_of_fragments):
			w = zfill(bin(int(floor((i/(2**n - 1) % (2 ** m)))))[2:], self.profile.M)
			fcn = zfill(bin((2 ** n - 2) - (i % (2 ** n - 1)))[2:], self.profile.N)

			fragment_payload = message[i * payload_max_length:(i + 1) * payload_max_length]

			if len(self.schc_packet) <= 300:
				if len(fragment_payload) < payload_max_length or i == (len(range(number_of_fragments)) - 1):
					header = Header(self.profile, rule_id="00", dtag="0", w=w, fcn="111", c=0)

				else:
					header = Header(self.profile, rule_id="00", dtag="0", w=w, fcn=fcn, c=0)
			else:
				if len(fragment_payload) < payload_max_length or i == (len(range(number_of_fragments)) - 1):
					header = Header(self.profile, rule_id="0000000", dtag="0", w=w, fcn="11111", c=0)

				else:
					header = Header(self.profile, rule_id="0000000", dtag="0", w=w, fcn=fcn, c=0)	

			

			fragment = [header.bytes, fragment_payload]
			# print("[" + header.string + "]" + str(fragment_payload))
			fragment_list.append(fragment)

		print("[FRGM] Fragmentation complete.")

		return fragment_list



class FragmenterNoAck(Fragmenter):

# From RFC 8724
# 8.4.1.  No-ACK Mode

#The No-ACK mode has been designed under the assumption that data unit
#out-of-sequence delivery does not occur between the entity performing
#fragmentation and the entity performing reassembly.  This mode
#supports L2 technologies that have a variable MTU.

#In No-ACK mode, there is no communication from the fragment receiver
#to the fragment sender.  The sender transmits all the SCHC Fragments
#without expecting any acknowledgement.  Therefore, No-ACK does not
#require bidirectional links: unidirectional links are just fine.

#In No-ACK mode, only the All-1 SCHC Fragment is padded as needed.
#The other SCHC Fragments are intrinsically aligned to L2 Words.

#The tile sizes are not required to be uniform.  Windows are not used.
#The Retransmission Timer is not used.  The Attempts counter is not
#used.

#    Each Profile MUST specify which RuleID value(s) corresponds to SCHC
#    F/R messages operating in this mode.

#    The W field MUST NOT be present in the SCHC F/R messages.  SCHC ACK
#    MUST NOT be sent.  SCHC ACK REQ MUST NOT be sent.  SCHC Sender-Abort
#    MAY be sent.  SCHC Receiver-Abort MUST NOT be sent.

#    The value of N (size of the FCN field) is RECOMMENDED to be 1.

#    Each Profile, for each RuleID value, MUST define:
#    *  the size of the DTag field,
#    *  the size and algorithm for the RCS field, and
#    *  the expiration time of the Inactivity Timer.
#    Each Profile, for each RuleID value, MAY define
#    *  a value of N different from the recommended one, and
#    *  the meaning of values sent in the FCN field, for values different
#       from the All-1 value.

#    For each active pair of RuleID and DTag values, the receiver MUST
#    maintain an Inactivity Timer.  If the receiver is under-resourced to
#    do this, it MUST silently drop the related messages.


# From draft-ietf-lpwan-schc-over-sigfox-03
# 4.5.1.1.  Uplink No-ACK Mode
# No-ACK is RECOMMENDED to be used for transmitting short, non-critical
# packets that require fragmentation and do not require full
# reliability.  This mode can be used by uplink-only devices that do
# not support downlink communications, or by bidirectional devices when
# they send non-critical data.

# Since there are no multiple windows in the No-ACK mode, the W bit is
# not present.  However it is RECOMMENDED to use FCN to indicate the
# size of the data packet.  In this sense, the data packet would need
# to be splitted into X fragments and, similarly to the other
# fragmentation modes, the first transmitted fragment would need to be
# marked with FCN = X-1.  Consecutive fragments MUST be marked with
# decreasing FCN values, having the last fragment marked with FCN =
# (All-1).  Hence, even though the No-ACK mode does not allow
# recovering missing fragments, it allows indicating implicitly to the
# Network the size of the expected packet and whether all fragments
# have been received or not.

# The RECOMMENDED Fragmentation Header size is 8 bits, and it is
# composed as follows:
# o  RuleID size: 4 bits
# o  DTag size (T): 0 bits
# o  Fragment Compressed Number (FCN) size (N): 4 bits
# o  As per [RFC8724], in the No-ACK mode the W (window) field is not
# 	present.
# o  RCS: Not used

# From RFC 8724	
# 8.4.1.1.  Sender Behavior

#    At the beginning of the fragmentation of a new SCHC Packet, the
#    fragment sender MUST select a RuleID and DTag value pair for this
#    SCHC Packet.

#    Each SCHC Fragment MUST contain exactly one tile in its Payload.  The
#    tile MUST be at least the size of an L2 Word.  The sender MUST
#    transmit the SCHC Fragments messages in the order that the tiles
#    appear in the SCHC Packet.  Except for the last tile of a SCHC
#    Packet, each tile MUST be of a size that complements the SCHC
#    Fragment Header so that the SCHC Fragment is a multiple of L2 Words
#    without the need for padding bits.  Except for the last one, the SCHC
#    Fragments MUST use the Regular SCHC Fragment format specified in
#    Section 8.3.1.1.  The SCHC Fragment that carries the last tile MUST
#    be an All-1 SCHC Fragment, described in Section 8.3.1.2.

#    The sender MAY transmit a SCHC Sender-Abort.

	def fragment(self):
		print("[FRGM] Begin fragmentation noACK uplink")
		

		payload_max_length = int((self.profile.MTU - self.profile.HEADER_LENGTH) / 8)
		message = self.schc_packet
		fragment_list = []
		n = self.profile.N
		m = self.profile.M
		number_of_fragments = int(ceil(float(len(message)) / payload_max_length))

		print("[FRGM] Fragmenting message into " + str(number_of_fragments) + " pieces...")
		
		if number_of_fragments > self.profile.WINDOW_SIZE:
			# print(number_of_fragments)
			# print(self.profile.WINDOW_SIZE)
			print("The SCHC packet of {} fragments cannot be carry in {} fragments. This fragmentation mode cannot be used.".format(number_of_fragments,self.profile.WINDOW_SIZE))
			# What does this mean?
			# This means that is not possible to send the SCHC Packet using the current mode
			# the Number of available FCN limits the max SCHC Packet size
			return None
		for i in range(number_of_fragments):
			# w = zfill(bin(int(floor((i/(2**n - 1) % (2 ** m)))))[2:], 2)
			fcn = zfill(bin((2 ** n - 2) - (i % (2 ** n - 1)))[2:], 4)
			print('i-> {}, range(number_of_fragments)- > {}'.format(i,len(range(number_of_fragments))))
			fragment_payload = message[i * payload_max_length:(i + 1) * payload_max_length]
			print('len(fragment_payload) -> {}, payload_max_length -> {}'.format(len(fragment_payload),payload_max_length))
			if len(fragment_payload) < payload_max_length or i == (len(range(number_of_fragments)) - 1):
				#added or condition so last fragment when len(fragment_payload) == payload_max_length it
				# still is marked as All-1 fragment
				header = HeaderNoACK(self.profile, rule_id="0001", fcn="1111", c=0)

			else:
				header = HeaderNoACK(self.profile, rule_id="0001", fcn=fcn, c=0)

			fragment = [header.bytes, fragment_payload]
			print("[" + header.string + "]" + str(fragment_payload))
			fragment_list.append(fragment)

		print("[FRGM] Fragmentation complete.")

		return fragment_list
