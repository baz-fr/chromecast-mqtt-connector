import logging
from json import loads
import mimetypes

# only used for publishing
TOPIC_FRIENDLY_NAME = "chromecast/%s/friendly_name"
TOPIC_CONNECTION_STATUS = "chromecast/%s/connection_status"
TOPIC_CAST_TYPE = "chromecast/%s/cast_type"
TOPIC_CURRENT_APP = "chromecast/%s/current_app"
TOPIC_PLAYER_DURATION = "chromecast/%s/player_duration"
TOPIC_PLAYER_POSITION = "chromecast/%s/player_position"
TOPIC_PLAYER_STATE = "chromecast/%s/player_state"
TOPIC_VOLUME_LEVEL = "chromecast/%s/volume_level"
TOPIC_VOLUME_MUTED = "chromecast/%s/volume_muted"
TOPIC_MEDIA_TITLE = "chromecast/%s/media/title"
TOPIC_MEDIA_ALBUM_NAME = "chromecast/%s/media/album_name"
TOPIC_MEDIA_ARTIST = "chromecast/%s/media/artist"
TOPIC_MEDIA_ALBUM_ARTIST = "chromecast/%s/media/album_artist"
TOPIC_MEDIA_TRACK = "chromecast/%s/media/track"
TOPIC_MEDIA_IMAGES = "chromecast/%s/media/images"
TOPIC_MEDIA_CONTENT_TYPE = "chromecast/%s/media/content_type"
TOPIC_MEDIA_CONTENT_URL = "chromecast/%s/media/content_url"

# subscribe
TOPIC_COMMAND_VOLUME_LEVEL = "chromecast/%s/command/volume_level"
TOPIC_COMMAND_VOLUME_MUTED = "chromecast/%s/command/volume_muted"
TOPIC_COMMAND_PLAYER_POSITION = "chromecast/%s/command/player_position"
TOPIC_COMMAND_PLAYER_STATE = "chromecast/%s/command/player_state"

STATE_REQUEST_RESUME = "RESUME"
STATE_REQUEST_PAUSE = "PAUSE"
STATE_REQUEST_STOP = "STOP"
STATE_REQUEST_SKIP = "SKIP"
STATE_REQUEST_REWIND = "REWIND"


# play stream has another syntax, not listed here therefore


class MqttChangesCallback:
    def on_volume_mute_requested(self, is_muted):
        pass

    def on_volume_level_relative_requested(self, relative_value):
        pass

    def on_volume_level_absolute_requested(self, absolute_value):
        pass

    def on_player_position_requested(self, position):
        pass

    def on_player_play_stream_requested(self, content_url, content_type):
        pass

    def on_player_pause_requested(self):
        pass

    def on_player_resume_requested(self):
        pass

    def on_player_stop_requested(self):
        pass

    def on_player_skip_requested(self):
        pass

    def on_player_rewind_requested(self):
        pass


class MqttPropertyHandler:
    def __init__(self, mqtt_connection, mqtt_topic_filter, changes_callback):
        self.logger = logging.getLogger("mqtt")
        self.mqtt = mqtt_connection
        self.topic_filter = mqtt_topic_filter
        self.changes_callback = changes_callback
        self.write_filter = {}

    def is_topic_filter_matching(self, topic):
        """
        Check if a topic (e.g.: chromecast/my_device_name/player_state) matches our filter (the name part).
        """
        try:
            return topic.split("/")[1] == self.topic_filter
        except IndexError:
            return False

    def _write(self, topic, value):
        # noinspection PyBroadException
        try:
            if isinstance(value, float):
                if 0 <= value <= 1:  # chromecast volume
                    value *= 100

                value = str(round(value))
            elif isinstance(value, bool):
                if value:
                    value = "1"
                else:
                    value = "0"
            elif value is None:
                value = ""
            else:
                value = str(value)

            formatted_topic = topic % self.topic_filter

            # filter to prevent writing the same value again until it has changed
            if formatted_topic in self.write_filter and self.write_filter[formatted_topic] == value:
                return

            self.write_filter[formatted_topic] = value
            self.mqtt.send_message(formatted_topic, value)
        except Exception:
            self.logger.exception("value conversion error")

    def write_cast_status(self, app_name, volume_level, is_volume_muted):
        self._write(TOPIC_CURRENT_APP, app_name)
        self._write(TOPIC_VOLUME_LEVEL, volume_level)
        self._write(TOPIC_VOLUME_MUTED, is_volume_muted)

    def write_player_status(self, state, current_time, duration):
        self._write(TOPIC_PLAYER_STATE, state)
        self._write(TOPIC_PLAYER_POSITION, current_time)
        self._write(TOPIC_PLAYER_DURATION, duration)

    def write_media_status(self, title, album_name, artist, album_artist, track, images, content_type, content_id):
        self._write(TOPIC_MEDIA_TITLE, title)
        self._write(TOPIC_MEDIA_ALBUM_NAME, album_name)
        self._write(TOPIC_MEDIA_ARTIST, artist)
        self._write(TOPIC_MEDIA_ALBUM_ARTIST, album_artist)
        self._write(TOPIC_MEDIA_TRACK, track)
        self._write(TOPIC_MEDIA_IMAGES, images)
        self._write(TOPIC_MEDIA_CONTENT_TYPE, content_type)
        self._write(TOPIC_MEDIA_CONTENT_URL, content_id)

    def write_connection_status(self, status):
        self._write(TOPIC_CONNECTION_STATUS, status)

    def write_cast_data(self, cast_type, friendly_name):
        self._write(TOPIC_CAST_TYPE, cast_type)
        self._write(TOPIC_FRIENDLY_NAME, friendly_name)

    def handle_message(self, topic, payload):
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')

        payload = str(payload).strip()

        if TOPIC_COMMAND_VOLUME_MUTED % self.topic_filter == topic:
            self.handle_volume_mute_change(payload)
        elif TOPIC_COMMAND_VOLUME_LEVEL % self.topic_filter == topic:
            self.handle_volume_level_change(payload)
        elif TOPIC_COMMAND_PLAYER_POSITION % self.topic_filter == topic:
            self.handle_player_position_change(payload)
        elif TOPIC_COMMAND_PLAYER_STATE % self.topic_filter == topic:
            self.handle_player_state_change(payload)

    def handle_volume_mute_change(self, payload):
        """
        Change volume mute where 1 = muted, 0 = unmuted.
        """

        if payload != "0" and payload != "1":
            return

        self.changes_callback.on_volume_mute_requested(payload == "1")

    def handle_volume_level_change(self, payload):
        """
        Change volume level to either absolute value between 0 .. 100 or by relative offset (prefix with "-" or "+",
        e.g +5 or -10).
        """

        if len(payload) == 0:
            return

        is_relative = payload[0] == "-" or payload[0] == "+"
        # noinspection PyBroadException
        try:
            # allow sending us floats but we only need the integer and not the decimal part
            value = int(float(payload))
        except Exception:
            self.logger.exception("failed decoding requested volume level")
            return

        if is_relative:
            self.changes_callback.on_volume_level_relative_requested(value)
        else:
            self.changes_callback.on_volume_level_absolute_requested(value)

    def handle_player_position_change(self, payload):
        """
        Change current player position
        """

        if len(payload) == 0:
            return

        # noinspection PyBroadException
        try:
            # allow sending us floats but we only need the integer and not the decimal part
            value = int(float(payload))
            self.changes_callback.on_player_position_requested(value)
        except Exception:
            self.logger.exception("failed decoding requested position")

    def handle_player_state_change(self, payload):
        if payload == STATE_REQUEST_PAUSE:
            self.changes_callback.on_player_pause_requested()
        elif payload == STATE_REQUEST_RESUME:
            self.changes_callback.on_player_resume_requested()
        elif payload == STATE_REQUEST_STOP:
            self.changes_callback.on_player_stop_requested()
        elif payload == STATE_REQUEST_SKIP:
            self.changes_callback.on_player_skip_requested()
        elif payload == STATE_REQUEST_REWIND:
            self.changes_callback.on_player_rewind_requested()
        else:
            if len(payload) == 0:
                return

            # noinspection PyBroadException
            try:
                # json object format
                if payload[0] == '{':
                    data = loads(payload)
                    self.changes_callback.on_player_play_stream_requested(**data)

                # json array format
                elif payload[0] == '[':
                    data = loads(payload)
                    if not isinstance(data, list) or len(data) != 2:
                        raise AssertionError("data must be array and must possess two elements (url, content type)")
                    self.changes_callback.on_player_play_stream_requested(*data)

                # string format
                else:
                    mime_data = mimetypes.guess_type(payload, strict=False)
                    found_mime_type = None
                    if mime_data is not None:
                        found_mime_type = mime_data[0]
                    else:
                        self.logger.warning("no mime type found")

                    self.changes_callback.on_player_play_stream_requested(payload, content_type=found_mime_type)
            except Exception:
                self.logger.exception("failed decoding requested play stream data: %s" % payload)
