import struct

class JPYGError(Exception):
    pass

segment_tags = {
    '\xff\xd8': 'SOI',
    '\xff\xc0': 'SOF0',
    '\xff\xc2': 'SOF2',
    '\xff\xc4': 'DHT',
    '\xff\xdb': 'DQT',
    '\xff\xdd': 'DRI',
    '\xff\xda': 'SOS',
    '\xff\xd0': 'RST0',
    '\xff\xd1': 'RST1',
    '\xff\xd2': 'RST2',
    '\xff\xd3': 'RST3',
    '\xff\xd4': 'RST4',
    '\xff\xd5': 'RST5',
    '\xff\xd6': 'RST6',
    '\xff\xd7': 'RST7',
    '\xff\xe0': 'APP0',
    '\xff\xe1': 'APP1',
    '\xff\xe2': 'APP2',
    '\xff\xe3': 'APP3',
    '\xff\xe4': 'APP4',
    '\xff\xe5': 'APP5',
    '\xff\xe6': 'APP6',
    '\xff\xe7': 'APP7',
    '\xff\xe8': 'APP8',
    '\xff\xe9': 'APP9',
    '\xff\xea': 'APPa',
    '\xff\xeb': 'APPb',
    '\xff\xec': 'APPc',
    '\xff\xed': 'APPd',
    '\xff\xee': 'APPe',
    '\xff\xef': 'APPf',
    '\xff\xfe': 'COM',
    '\xff\xd9': 'EOI',
}

segment_sized = {
    'SOI': False,
    'SOF0': True,
    'SOF2': True,
    'DHT': True,
    'DQT': True,
    'DRI': True,
    'SOS': True,
    'RST0': False,
    'RST1': False,
    'RST2': False,
    'RST3': False,
    'RST4': False,
    'RST5': False,
    'RST6': False,
    'RST7': False,
    'APP0': True,
    'APP1': True,
    'APP2': True,
    'APP3': True,
    'APP4': True,
    'APP5': True,
    'APP6': True,
    'APP7': True,
    'APP8': True,
    'APP9': True,
    'APPa': True,
    'APPb': True,
    'APPc': True,
    'APPd': True,
    'APPe': True,
    'APPf': True,
    'COM': True,
    'EOI': False,
}

class Segment(object):
    def __init__(self, content):
        self.segment_header = content[:2]

        if self.segment_header not in segment_tags:
            raise JPYGError('no such header')

        self.segment = segment_tags[self.segment_header]
        is_sized = segment_sized[self.segment]
        self.actual_size = 2

        if is_sized:
            self.size_bytes = content[2:4]
            self.actual_size += struct.unpack(">H", self.size_bytes)[0]
            self.payload = content[4:self.actual_size]
        else:
            self.size_bytes = ''
            self.payload = ''

        self.damaged = False
        self.stated_size = self.actual_size

        ff_indices = [ i for i,c in enumerate(self.payload) if c == "\xff" and (i+1 == len(self.payload) or self.payload[i+1] != '\x00') ]
        if ff_indices:
            actual_payload = self.payload[:ff_indices[0]]
            self.actual_size -= len(self.payload) - len(actual_payload)
            self.payload = actual_payload
            self.damaged = True

    @property
    def bytes(self):
        return self.segment_header + self.size_bytes + self.payload

    def __repr__(self):
        return "<Segment %s of length %d%s>" % (self.segment, self.stated_size, ' DAMAGED' if self.damaged else '')

class BrokenSegment(object):
    def __init__(self, content):
        self.segment_header = ''
        self.segment = None

        next_headers = [ content.index(k) for k in segment_tags.keys() if k in content ]
        self.size_bytes = ''
        self.actual_size = min(next_headers)
        self.payload = content[:self.actual_size]

    @property
    def bytes(self):
        return self.segment_header + self.size_bytes + self.payload

    def __repr__(self):
        return "<BrokenSegment of length %d>" % self.actual_size

class JPEG(object):
    def __init__(self, content):
        self.segments = [ ]

        while len(content) != 0:
            try:
                s = Segment(content)
            except JPYGError:
                s = BrokenSegment(content)
            self.segments.append(s)
            content = content[s.actual_size:]

    @property
    def bytes(self):
        return ''.join(s.bytes for s in self.segments)
