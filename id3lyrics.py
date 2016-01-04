#!/usr/bin/env python3
# Kaan Karaagacli
""" Library to listen to the state change events in a music player,
and call a given callback function with the lyrics of the new song played.

It is designed to work offline, therefore the lyrics are retrieved
using the library mutagen, so it only works with the embedded lyrics.

It is only tested with 'rhythmbox' and 'GnomeMusic', but it should work
with any MPRIS capable player.

The player is automatically detected when the class initializes,
and it is not refreshed if you change to another player, you need to
create a new class if you need reinitialization.

In case of multiple players running at the same time, one of them
is chosen randomly, therefore make sure only the one you want to be
connected is running when creating this class. """

from gi.repository import Gio, GLib
import urllib.parse
import mutagen.id3

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
        Note that the callback function is immediately called when the
        connection to the player is established. """

        self.callback_func = callback_func

        # url of the last played file
        self.last_url = None

        # initialize the bus
        bus = Gio.bus_get_sync(bus_type=Gio.BusType.SESSION, cancellable=None)

        self.detect_and_connect_to_player(bus)

    def detect_and_connect_to_player(self, bus):
        """ Find the first available MPRIS capable player and connect to it. """
        proxy = Gio.DBusProxy.new_sync(connection=bus,
                flags=Gio.DBusProxyFlags.NONE,
                info=None,
                name='org.freedesktop.DBus',
                object_path='/org/freedesktop/DBus',
                interface_name='org.freedesktop.DBus',
                cancellable=None)

        def find_player():
            """ Go through all the DBus names and connect if a music player
            is found. This function will be repeatedly called until
            this happens.
            Returns True if a player is not found, and False
            if a player is found and connected. """
            # the return value may seem backwards, but this is a requirement
            # of the GLib timeout function:
            # True means 'loop again'
            # False means 'end loop'
            names = proxy.call_sync(method_name='ListNames',
                    parameters=None,
                    flags=Gio.DBusCallFlags.NONE,
                    timeout_msec=-1,
                    cancellable=None)
            for name in names[0]:
                if name.startswith('org.mpris.MediaPlayer2.'):
                    self.start_connection(bus, name)
                    return False
            else:
                return True

        # do the initial check instantly
        if find_player():
            # continue checking until a player is found
            GLib.timeout_add_seconds(2, find_player)

    def start_connection(self, bus, player_name):
        """ Connect to a player.
        Calls the callback function once, and then sets up so that it
        is called whenever the song changes. """
        self.proxy = Gio.DBusProxy.new_sync(connection=bus,
                flags=Gio.DBusProxyFlags.NONE,
                info=None,
                name=player_name,
                object_path='/org/mpris/MediaPlayer2',
                interface_name='org.mpris.MediaPlayer2.Player',
                cancellable=None)

        # call the callback function, even if there is no file played
        self.process_metadata(self.proxy.get_cached_property('Metadata'), True)
        # when the properties change (e.g. a new song
        # starts), call the listener function
        self.proxy.connect('g-properties-changed', self.listener)

    def listener(self, proxy, changed_properties, invalidated_properties):
        """ D-Bus listener, acts by calling process_metadata when needed. """
        metadata = changed_properties.lookup_value('Metadata')
        # do not signal if the metadata is empty
        self.process_metadata(metadata, False)

    def process_metadata(self, metadata, allow_empty):
        """ Extract the MPRIS metadata and pass it for signalling if needed.

        Keyword arguments:
        metadata    -- a GVariant object that holds information about the song,
                       may be None or empty
        allow_empty -- indicates if the signalling should be done even if
                       the metadata object is None or empty """

        # make sure the metadata is not null nor empty
        url = self.get_url_from_metadata(metadata)
        if url != None:
            # don't signal if we have already signalled this file
            if url != self.last_url:
                artist = metadata.lookup_value('xesam:artist')[0]
                title = metadata.lookup_value('xesam:title').get_string()

                self.last_url = url
                self.signal_metadata(url, artist, title)

        # in case when the script has just started, we need to signal
        # even if there is no file
        elif allow_empty:
            self.signal_metadata(None)

    def signal_metadata(self, url, artist=None, title=None):
        """ Get the lyrics using mutagen and give them to the callback.

        Keyword arguments:
        url    -- location of the music file
        artist -- name of the song's artist, not used if the url is None
        title  -- title of the song, not used if the url is None """

        # default values to return
        path = None
        full_title = None
        lyrics = 'No lyrics'

        # if url is null, send an empty message with the default values
        # (happens when the player has just started and is not playing)
        # if not, extract lyrics
        if url != None:
            # decode path from url
            path = urllib.parse.urlparse(url).path
            path = urllib.parse.unquote(path)

            # extract the artist name and title
            # then create a window title from them
            full_title = artist + ' - ' + title

            try:
                # extract the lyrics from the file using mutagen
                tags = mutagen.id3.ID3(path)
                lyrics_tag = tags.getall('USLT')

                if len(lyrics_tag) > 0:
                    lyrics = lyrics_tag[0].text
            except mutagen.id3.ID3NoHeaderError:
                # no lyrics in the file
                pass

            # do not return /home/username if we can replace it with '~'
            home = GLib.get_home_dir()
            if path.startswith(home):
                path = path.replace(home, '~', 1)

        self.callback_func(path, full_title, lyrics)

    def get_url_from_metadata(self, metadata):
        """ Extract the URL from a metadata object. Returns None if the URL is
        invalid or the metadata does not contain an URL. """
        if metadata != None:
            url_object = metadata.lookup_value('xesam:url')
            if url_object != None:
                url = url_object.get_string()
                if url != '':
                    return url
        return None

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
        print(chr(27) + '[2J', chr(27) + '[;H')

        if path != None:
            print(path)
        print(lyrics)

    try:
        print('Connecting to the first available player...')
        # simply create a monitor object, give it your callback function
        monitor = ID3LyricsMonitor(print_func)
        # and run it
        monitor.run()
    except KeyboardInterrupt:
        pass
