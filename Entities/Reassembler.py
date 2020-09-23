from Messages.Fragment import Fragment


class Reassembler:
	profile = None
	schc_fragments = []
	rule_set = set()
	dtag_set = set()
	window_set = set()
	fcn_set = set()

	def __init__(self, profile, schc_fragments):
		self.profile = profile

		for fragment in schc_fragments:
			if fragment != b'':
				self.schc_fragments.append(Fragment(self.profile, fragment))

		for fragment in self.schc_fragments:
			self.rule_set.add(fragment.header.RULE_ID)
			self.dtag_set.add(fragment.header.DTAG)
			self.window_set.add(fragment.header.W)
			self.fcn_set.add(fragment.header.FCN)

	def reassemble(self):
		fragments = self.schc_fragments
		payload_list = []

		for fragment in fragments:
			payload_list.append(fragment.payload)

		return b"".join(payload_list)
