from Messages.Header import Header


class ReceiverAbort:
    profile = None
    header_length = 0
    rule_id_size = 0
    t = 0
    n = 0
    window_size = 0

    header = None
    padding = ''

    def __init__(self, profile, rule_id, dtag, w):
        self.profile = profile

        self.header = Header(profile=profile,
                             rule_id=rule_id,
                             dtag=dtag,
                             w=w,
                             fcn='',
                             c='1')

        # if the Header does not end at an L2 Word boundary, append bits set to 1 as needed to reach the next L2 Word boundary.
        while len(self.header.string + self.padding) % profile.L2_WORD_SIZE != 0:
            self.padding += '1'

        # append exactly one more L2 Word with bits all set to ones.
        self.padding += '1'*profile.L2_WORD_SIZE


    @staticmethod
    def checkReceiverAbort(ack_bitstring, rule_id_size, dtag_size, M, rule_id, dtag, W):
        """
        Method to check if the ACK received is a ReceiverAbort message
        params: the ACK bitstring, ruleid size, dtag size, fcn size (M), rule id, dtag and W
        return: True if ReceiverAbort, False otherwise
        """
        bitstring = ack_bitstring
        # bitstring = '0000010000000000000000000000000000000000000000000000000000000000'
        # bitstring = '0001111111111111111111111111111111111111111111111111111111111111'
        ackRuleID = bitstring[0:rule_id_size]
        ackDTAG = bitstring[rule_id_size:rule_id_size + dtag_size]
        ackW = bitstring[rule_id_size + dtag_size:rule_id_size + dtag_size + M]
        ackC = bitstring[rule_id_size + dtag_size + M:rule_id_size + dtag_size + M + 1]
        # print(ackRuleID)
        # print(ackDTAG)
        # print(ackW)
        # print(ackC)
        if rule_id != ackRuleID:
            # Another Rule ID
            False
        if dtag != ackDTAG:
            # Different DTAG
            False
        if W == ackW:
            # Same window, not an Abort
            False
        
        if ackC == '1':
            # if C equals 1, may be an Abort, 
            # ackW must be W-1 to be an Abort
            # also if padding is 1
            ackPadding = bitstring[rule_id_size + dtag_size + M + 1:]
            #print(ackPadding)
            for paddingbit in ackPadding:
                #print(paddingbit)
                if paddingbit == '0':
                    #print('paddingbit = 1 False')
                    return False
            # print(int(ackW,2))
            # print(int(W,2))
            # print(2^(M)-1)
            # padding is 1 check window number
            # the Window is 0, so the ackW must be 2^M-1, example M = 2 (max window 0b'11)
            if int(ackW,2) == (2^(M)-1):
                # print('ackW=2^(M)-1 True')
                return True
            # print(' False')
            
            return False
        return False

        pass