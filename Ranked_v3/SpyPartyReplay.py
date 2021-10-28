from base64 import urlsafe_b64encode
from dataclasses import dataclass
from datetime import datetime
from struct import unpack
from typing import Optional


@dataclass
class Player:
    username: str
    display_name: str

    def __init__(self, username, display_name):
        self.username = username
        self.display_name = display_name.removesuffix('/steam')

    def is_steam_user(self):
        return self.username.endswith('/steam')

    def __str__(self):
        return self.display_name

    def __hash__(self):
        return hash(self.username)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.username == other
        return self.username == other.username


class SpyPartyReplay:
    class ParsingException(Exception):
        pass

    @dataclass
    class ReplayVersionOffsets:
        magic_number: int = 0x00
        file_version: int = 0x04
        protocol_version: int = 0x08
        game_version: int = 0x0C
        game_duration: int = 0x14
        uuid: int = 0x18
        timestamp: int = 0x28
        play_id: int = 0x2C
        players: int = 0x50
        len_user_spy: int = 0x2E
        len_user_sniper: int = 0x2F
        len_disp_spy: Optional[int] = None
        len_disp_sniper: Optional[int] = None
        guests: Optional[int] = None
        clock: Optional[int] = None
        result: int = 0x30
        setup: int = 0x34
        venue: int = 0x38
        variant: Optional[int] = None
        missions_s: int = 0x3C
        missions_p: int = 0x40
        missions_c: int = 0x44

        @staticmethod
        def read_bytes(sector, start, length):
            return sector[start:(start + length)]

        def extract_names(self, sector):
            total_offset = self.players

            spy_user_len = sector[self.len_user_spy]
            spy_username = self.read_bytes(sector, total_offset, spy_user_len).decode()
            total_offset += spy_user_len

            sni_user_len = sector[self.len_user_sniper]
            sniper_username = self.read_bytes(sector, total_offset, sni_user_len).decode()

            spy_display_name, sniper_display_name = spy_username, sniper_username
            if self.len_disp_spy or self.len_disp_sniper:
                total_offset += sni_user_len
                spy_disp_len = sector[self.len_disp_spy]
                spy_display_name = self.read_bytes(sector, total_offset, spy_disp_len).decode()

                total_offset += spy_disp_len
                sni_disp_len = sector[self.len_disp_sniper]
                sniper_display_name = self.read_bytes(sector, total_offset, sni_disp_len).decode()

                if not spy_display_name:
                    spy_display_name = spy_username
                if not sniper_display_name:
                    sniper_display_name = sniper_username
            return Player(spy_username, spy_display_name), Player(sniper_username, sniper_display_name)

    __HEADER_DATA_MINIMUM_BYTES = 416
    __HEADER_DATA_USERNAME_LIMIT = 33
    __HEADER_DATA_DISPLAYNAME_LIMIT = 135
    __HEADER_DATA_MAXIMUM_BYTES = __HEADER_DATA_MINIMUM_BYTES + 2 * (
            __HEADER_DATA_USERNAME_LIMIT + __HEADER_DATA_DISPLAYNAME_LIMIT)
    __OFFSETS_DICT = {
        3: ReplayVersionOffsets(),
        4: ReplayVersionOffsets(
            players=0x54, result=0x34, setup=0x38, venue=0x3C,
            missions_s=0x40, missions_p=0x44, missions_c=0x48
        ),
        5: ReplayVersionOffsets(
            players=0x60, len_user_spy=0x2E, len_user_sniper=0x2F, len_disp_spy=0x30, len_disp_sniper=0x31,
            guests=0x50, clock=0x54, result=0x38, setup=0x3C, venue=0x40,
            missions_s=0x44, missions_p=0x48, missions_c=0x4C
        ),
        6: ReplayVersionOffsets(
            players=0x64, len_user_spy=0x2E, len_user_sniper=0x2F, len_disp_spy=0x30, len_disp_sniper=0x31,
            guests=0x54, clock=0x58, result=0x38, setup=0x3C, venue=0x40, variant=0x44,
            missions_s=0x48, missions_p=0x4C, missions_c=0x50
        )
    }

    __VENUE_MAP = {
        0x8802482A: "Old High-rise",
        0x3A30C326: "High-rise",
        0x5996FAAA: "Ballroom",
        0x5B121925: "Ballroom",
        0x1A56C5A1: "High-rise",
        0x28B3AA5E: "Old Gallery",
        0x290A0C75: "Old Courtyard 2",
        0x3695F583: "Panopticon",
        0xA8BEA091: "Old Veranda",
        0xB8891FBC: "Old Balcony",
        0x0D027340: "Pub",
        0x3B85FFF3: "Pub",
        0x09C2E7B0: "Old Ballroom",
        0xB4CF686B: "Old Courtyard",
        0x7076E38F: "Double Modern",
        0xE6146120: "Modern",
        0x6F81A558: "Veranda",
        0x9DC5BB5E: "Courtyard",
        0x168F4F62: "Library",
        0x1DBD8E41: "Balcony",
        0x7173B8BF: "Gallery",
        0x9032CE22: "Terrace",
        0x2E37F15B: "Moderne",
        0x79DFA0CF: "Teien",
        0x98E45D99: "Aquarium",
        0x35AC5135: "Redwoods",
        0xF3E61461: "Modern",
    }
    __VARIANT_MAP = {
        "Aquarium": ["Bottom", "Top"],
        "Teien": [
            "BooksBooksBooks", "BooksStatuesBooks", "StatuesBooksBooks", "StatuesStatuesBooks",
            "BooksBooksStatues", "BooksStatuesStatues", "StatuesBooksStatues", "StatuesStatuesStatues"
        ],
    }
    __RESULT_MAP = {
        0: "Missions Win",
        1: "Time Out",
        2: "Spy Shot",
        3: "Civilian Shot",
        4: "In Progress"
    }
    __MODE_MAP = {
        0: "k",
        1: "p",
        2: "a"
    }
    __MISSION_OFFSETS = {
        "Bug": 0,
        "Contact": 1,
        "Transfer": 2,
        "Swap": 3,
        "Inspect": 4,
        "Seduce": 5,
        "Purloin": 6,
        "Fingerprint": 7,
    }

    def __unpack_missions(self, sector, offset, container_type):
        data = self.__unpack_int(sector, offset)
        return container_type(
            mission for mission in self.__MISSION_OFFSETS if data & (1 << self.__MISSION_OFFSETS[mission]))

    @staticmethod
    def __read_bytes(sector, start, length):
        return sector[start:(start + length)]

    @staticmethod
    def __unpack_byte(sector, offset):
        return unpack('B', sector[offset])[0]

    def __unpack_float(self, sector, offset):
        return unpack('f', self.__read_bytes(sector, offset, 4))[0]

    def __unpack_int(self, sector, start):
        return unpack('I', self.__read_bytes(sector, start, 4))[0]

    def __unpack_short(self, sector, start):
        return unpack('H', self.__read_bytes(sector, start, 2))[0]

    def __init__(self, filepath, mission_container=set):
        with open(filepath, "rb") as replay_file:
            bytes_read = bytearray(replay_file.read(self.__HEADER_DATA_MAXIMUM_BYTES))

            if len(bytes_read) < self.__HEADER_DATA_MINIMUM_BYTES:
                raise SpyPartyReplay.ParsingException(
                    f"A minimum of {self.__HEADER_DATA_MINIMUM_BYTES} bytes are required to parse: {filepath}")
            if bytes_read[:4] != b"RPLY":
                raise SpyPartyReplay.ParsingException(f"Unknown File ({filepath})")

            replay_version = self.__unpack_int(bytes_read, 0x04)
            try:
                offsets = self.__OFFSETS_DICT[replay_version]
            except KeyError as e:
                raise SpyPartyReplay.ParsingException(f"Unknown file version: {e} ({filepath})")

            # passed all possible exceptions, start assigning values
            self.filepath = filepath
            self.date = datetime.fromtimestamp(self.__unpack_int(bytes_read, offsets.timestamp))

            self.venue = self.__VENUE_MAP[self.__unpack_int(bytes_read, offsets.venue)]
            if self.venue == 'Terrace' and self.__unpack_int(bytes_read, offsets.game_version) < 6016:  # thx chris
                self.venue = 'Old Terrace'
            self.variant = (
                venue_variants[self.__unpack_int(bytes_read, offsets.variant)]
                if offsets.variant and (venue_variants := self.__VARIANT_MAP.get(self.venue))
                else None)

            uuid_offset = offsets.uuid
            self.uuid = urlsafe_b64encode(bytes_read[uuid_offset:uuid_offset + 16]).decode().removesuffix('==')
            self.playid = self.__unpack_short(bytes_read, offsets.play_id)
            self.spy, self.sniper = offsets.extract_names(bytes_read)
            self.result = self.__unpack_int(bytes_read, offsets.result)

            if self.result == 0 or self.result == 3:
                self.winner, self.loser = self.spy, self.sniper
            elif self.result == 1 or self.result == 2:
                self.winner, self.loser = self.sniper, self.spy
            else:
                self.winner, self.loser = None, None

            setup_info = self.__unpack_int(bytes_read, offsets.setup)
            self.game_type = setup_info >> 28
            self.missions_available = (setup_info & 0x0FFFC000) >> 14
            self.missions_required = setup_info & 0x00003FFF

            self.guests = self.__unpack_int(bytes_read, offsets.guests) if offsets.guests else None
            self.start_clock = self.__unpack_int(bytes_read, offsets.clock) if offsets.clock else None
            self.duration = int(self.__unpack_float(bytes_read, offsets.game_duration))
            self.selected_missions = self.__unpack_missions(bytes_read, offsets.missions_s, mission_container)
            self.picked_missions = self.__unpack_missions(
                bytes_read, offsets.missions_p, mission_container) if self.game_type == 1 else None
            self.completed_missions = self.__unpack_missions(bytes_read, offsets.missions_c, mission_container)

    def get_game_result(self):
        return SpyPartyReplay.__RESULT_MAP[self.result]

    def get_game_type(self):
        return SpyPartyReplay.__MODE_MAP[self.game_type]

    def get_setup(self):
        return '%s%d/%d' % (self.get_game_type(), self.missions_required, self.missions_available)

    def to_dictionary(
            self, uuid='uuid', playid='playid', date='date',
            spy_displayname='spy_displayname', sniper_displayname='sniper_displayname',
            spy_username='spy_username', sniper_username='sniper_username',
            venue='venue', variant='variant', setup='setup',
            guests='guests', clock='clock', duration='duration',
            selected_missions='selected_missions', picked_missions='picked_missions',
            completed_missions='completed_missions', result='result'
    ):
        return {
            key: value for key, value in (
                (uuid, self.uuid), (playid, self.playid), (date, str(self.date)),
                (spy_displayname, self.spy.display_name), (sniper_displayname, self.sniper.display_name),
                (spy_username, self.spy.username), (sniper_username, self.sniper.username),
                (venue, self.venue), (variant, self.variant), (setup, self.get_setup()),
                (guests, self.guests), (clock, self.start_clock), (duration, self.duration),
                (selected_missions, list(self.selected_missions)),
                (picked_missions, list(self.picked_missions) if self.picked_missions else None),
                (completed_missions, list(self.completed_missions)), (result, self.get_game_result()),
            ) if key
        }
