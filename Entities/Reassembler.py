from Messages.Fragment import Fragment


class Reassembler:
	PROFILE = None
	SCHC_FRAGMENTS = []
	rule_set = set()
	dtag_set = set()
	window_set = set()
	fcn_set = set()

	def __init__(self, profile, schc_fragments):
		self.PROFILE = profile

		for fragment in schc_fragments:
			if fragment != b'':
				self.SCHC_FRAGMENTS.append(Fragment(self.PROFILE, fragment))

		for fragment in self.SCHC_FRAGMENTS:
			self.rule_set.add(fragment.HEADER.RULE_ID)
			self.dtag_set.add(fragment.HEADER.DTAG)
			self.window_set.add(fragment.HEADER.W)
			self.fcn_set.add(fragment.HEADER.FCN)

	def reassemble(self):
		fragments = self.SCHC_FRAGMENTS
		payload_list = []

		for fragment in fragments:
			payload_list.append(fragment.PAYLOAD)

		return b"".join(payload_list)
