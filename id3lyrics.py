#!/usr/bin/env python3
# Kaan Karaagacli
""" Library to listen to the state change events in a music player,
and call a given callback function with the lyrics of the new song played.

It is designed to work offline, therefore the lyrics are retrieved
using the library mutagen, so it only works with the embedded lyrics.

It is only tested with rhythmbox, but it should work with any MPRIS
capable player. """
# edit this line to find it out
PLAYER = 'rhythmbox'

from gi.repository import Gio, GLib
import urllib.parse
from mutagen.id3 import ID3, ID3NoHeaderError

class ID3LyricsMonitor(Gio.Application):
    """ Fetch the current lyrics and call the given function """
    def __init__(self, callback_func):
        """ Create a new monitor, setting the callback function to the
        given argument.

        Keyword arguments:
        callback_func -- the function to be called when the lyrics change,
                         it should have 3 string arguments (path, title,
                         lyrics)

        This function also initializes the bus.
        Note that the callback function is immediately called with the
        current lyrics. """

        self.callback_func = callback_func

        # initialize the bus
        bus = Gio.bus_get_sync(bus_type=Gio.BusType.SESSION, cancellable=None)
        self.proxy = Gio.DBusProxy.new_sync(connection=bus,
                flags=Gio.DBusProxyFlags.NONE,
                info=None,
                name="org.mpris.MediaPlayer2.rhythmbox",
                object_path="/org/mpris/MediaPlayer2",
                interface_name="org.mpris.MediaPlayer2.Player",
                cancellable=None)

        # return the current lyrics
        self.signal_metadata(self.proxy.get_cached_property("Metadata"))
        # when the properties changed (i.e. a new song starts)
        # call the listener function
        self.proxy.connect("g-properties-changed", self.listener)

    def listener(self, proxy, changed_properties, invalidated_properties):
        """ D-Bus listener, acts by calling signal_metadata when needed. """
        status = changed_properties.lookup_value("PlaybackStatus")
        # filter to only have the "start" or "resume" playing event
        if status != None and status.get_string() == "Playing":
            metadata = changed_properties.lookup_value("Metadata")
            # in case of "resume", metadata is not present
            # however, a "start" event is also fired, so this one can be ignored
            if metadata != None:
                self.signal_metadata(metadata)

    def signal_metadata(self, metadata):
        """ Extract the MPRIS metadata and fetch the lyrics using mutagen. """
        # default values to return
        path = None
        title = None
        lyrics = "No lyrics"

        if metadata != None:
            # url should be html encoded
            url = metadata.lookup_value("xesam:url").get_string()

            # decode path from url
            path = urllib.parse.urlparse(url).path
            path = urllib.parse.unquote(path)

            # extract the artist name and title
            # then create a window title from them
            artist_str = metadata.lookup_value("xesam:artist")[0]
            title_str = metadata.lookup_value("xesam:title").get_string()
            title = artist_str + " - " + title_str

            try:
                # extract the lyrics from the file using mutagen
                tags = ID3(path)
                lyrics_tag = tags.getall("USLT")

                if len(lyrics_tag) > 0:
                    lyrics = lyrics_tag[0].text
            except ID3NoHeaderError:
                # no lyrics in the file
                pass

        self.callback_func(path, title, lyrics)

    def run(self):
        """ Start the GLib loop.
        The callback function will be called immediately once, and again any
        time when the song changes in the future. """
        GLib.MainLoop().run()

if __name__ == '__main__':
    def print_func(path, title, lyrics):
        """ A simple callback function example that prints the lyrics to the
        standard output, along with the path as a title. """
        # clear the screen
        print(chr(27) + "[2J", chr(27) + "[;H")

        if path != None:
            print(path)
        print(lyrics)

    try:
        # simply create a monitor object, give it your callback function
        monitor = ID3LyricsMonitor(print_func)
        # and run it
        monitor.run()
    except KeyboardInterrupt:
        pass
