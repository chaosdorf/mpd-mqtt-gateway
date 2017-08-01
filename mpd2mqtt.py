#!/usr/bin/env python3

# DEBUG
import os
DEBUG = "DEBUG" in os.environ
print("Debugging: {} (You might want to set DEBUG.)".format(DEBUG))

# connect to Sentry (pip3 install raven)
if "SENTRY_DSN" in os.enivron:
    import raven
    raven = raven.Client(os.environ["SENTRY_DSN"])
    print("Connected to Sentry.")
else:
    raven = None
    print("Didn't connect to Sentry. You might want to set SENTRY_DSN.")

def handle_status(playing):
    title = playing.get("title")
    artist = playing.get("artist")
    album = playing.get("album")
    if DEBUG:
        print("------------------------")
        print("Currently playing: {}".format(playing))
        print("Title: {}".format(title))
        print("Artist: {}".format(artist))
        print("Album: {}".format(album))
    mqtt.publish("music/title", title)
    mqtt.publish("music/artist", artist)
    mqtt.publish("music/album", album)
    mqtt.publish("music/source", "mpd")

def quit():
    print("Exiting...")
    mqtt.loop_stop(force=False)
    mpd.close()
    mpd.disconnect()

try:
    # connect to mpd (apt install python3-mpd)

    from mpd import MPDClient
    mpd = MPDClient()
    mpd.idletimeout = None
    mpd.connect("mpd", 6600)
    print("Connected to mpd: version {}".format(mpd.mpd_version))

    # connect to mqtt (pip3 install paho-mqtt)

    import paho.mqtt.client

    mqtt = paho.mqtt.client.Client()
    mqtt.connect("mqttserver")
    mqtt.loop_start()
    print("Connected to mqtt.")

    # SIGTERM
    import signal
    signal.signal(signal.SIGTERM, quit)

    try:
        while True:
            playing = mpd.currentsong()
            handle_status(playing)
            mpd.idle()
    except KeyboardInterrupt:
        quit()

except Exception as exc:
    if raven:
        raven.captureException()
        print("Exception: {}".format(exc))
    else:
        raise
