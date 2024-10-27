# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from dataclasses import dataclass
from PyStageLinQ import EngineServices, PyStageLinQ

PrimeGo = None
track_id = None

subscription_list = {
    "EngineDeck1ExternalMixerVolume" : "/Engine/Deck1/ExternalMixerVolume",
    "EngineDeck1Play" : "/Engine/Deck1/Play",
    "EngineDeck1TrackArtistName" : "/Engine/Deck1/Track/ArtistName",
    "EngineDeck1TrackSongName" : "/Engine/Deck1/Track/SongName",
    "EngineDeck2ExternalMixerVolume": "/Engine/Deck2/ExternalMixerVolume",
    "EngineDeck2Play": "/Engine/Deck2/Play",
    "EngineDeck2TrackArtistName": "/Engine/Deck2/Track/ArtistName",
    "EngineDeck2TrackSongName": "/Engine/Deck2/Track/SongName",
}


@dataclass
class FaderDataType:
    fader_channel: int
    fader_position: float


@dataclass
class TrackNameDataType:
    track_channel: int
    track_name: str

@dataclass
class TrackArtistDataType:
    track_channel: int
    track_artist: str


@dataclass
class TrackInfo:
    track_fader_position: float
    track_name: str
    track_artist: str
    track_playing: bool

class trackID:

    def __init__(self, n_decks):
        self.deck_playing = None
        self.N_DECKS = n_decks
        self.deck_status = [TrackInfo(0.0,"","",False) for i in range(self.N_DECKS)]
        self.f = open("trackID.txt", "wb")


    def deck_stopped(self, deck_channel: int):
        self._check_if_channel_valid(deck_channel)
        self.deck_status[deck_channel].track_playing = False
        self._set_deck_playing()

    def deck_started(self, deck_channel: int):
        self._check_if_channel_valid(deck_channel)

        self.deck_status[deck_channel].track_playing = True

        self._set_deck_playing()

    def channelfader_changed(self, fader_data: FaderDataType):
        self._check_if_channel_valid(fader_data.fader_channel)
        self.deck_status[fader_data.fader_channel].track_fader_position = fader_data.fader_position

        if fader_data.fader_position == 0:
            self._set_deck_playing()

    def _set_deck_playing(self):
        i = 0
        for deck in self.deck_status:
            if deck.track_playing is True:
                if deck.track_fader_position != 0:
                    self.deck_playing = i
            i += 1

        if self.deck_playing is not None:
            print(f"{self.deck_status[self.deck_playing].track_artist} - {self.deck_status[self.deck_playing].track_name}")
            self.f.seek(0)
            self.f.truncate()
            self.f.write(f"{self.deck_status[self.deck_playing].track_artist} - {self.deck_status[self.deck_playing].track_name}".encode(encoding='UTF-8'))
            self.f.flush()

    def update_track_artist(self, track_artist_data: TrackArtistDataType):
        deck = track_artist_data.track_channel
        self._check_if_channel_valid(deck)
        self.deck_status[deck].track_artist = track_artist_data.track_artist

    def update_track_name(self, track_name_data: TrackNameDataType):
        deck = track_name_data.track_channel
        self._check_if_channel_valid(deck)
        self.deck_status[deck].track_name = track_name_data.track_name

    def _check_if_channel_valid(self, deck: int):
        if deck > self.N_DECKS or deck < 0:
            raise Exception("deck outside limits")

    def __del__(self):
        self.f.close()


def new_device_found_callback(ip, discovery_frame, service_list):
    # Print device info and supplied services
    print(
        f"Found new Device on ip {ip}: Device name: {discovery_frame.device_name}, ConnectionType: {discovery_frame.connection_type}, SwName: {discovery_frame.sw_name}, "
        f"SwVersion: {discovery_frame.sw_version}, port: {discovery_frame.Port}")

    if len(service_list) > 0:
        print("Services found in device:")
    else:
        print("No services found")

    for service in service_list:
         print(f"\t{service.service} on port {service.port}")


    # Request StateMap service
    for service in service_list:
        if service.service == "StateMap":
            PrimeGo.subscribe_to_statemap(service, subscription_list, state_map_data_print)

def state_map_data_print(data):
    for message in data:
        key = message.ParameterName.split('/')
        if key[1] == "Engine":
            deck = int(key[2][-1:]) - 1

            match key[3] :
                case 'ExternalMixerVolume':
                    fader_data = FaderDataType(deck, float(message.ParameterValue['value']))
                    track_id.channelfader_changed(fader_data)
                case 'Play':
                    if message.ParameterValue['state']:
                        track_id.deck_started(deck)
                    else:
                        track_id.deck_stopped(deck)
                case 'Track':
                    match key[4]:
                        case 'ArtistName':
                            track_artist_data = TrackArtistDataType(deck, message.ParameterValue['string'])
                            track_id.update_track_artist(track_artist_data)
                        case 'SongName':
                            track_name_data = TrackNameDataType(deck, message.ParameterValue['string'])
                            track_id.update_track_name(track_name_data)
                case 'TrackTrackName':
                    print(message.ParameterValue['string'])

        elif key[1] == "mixer":
            print(message)
            deck = int(key[2][2:3])


if __name__ == '__main__':


    track_id = trackID(2)

    PrimeGo = PyStageLinQ.PyStageLinQ(new_device_found_callback, name="Jaxcie StagelinQ")
    PrimeGo.start_standalone()

