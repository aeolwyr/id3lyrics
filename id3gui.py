#!/usr/bin/env python3
# Kaan Karaagacli
""" A GTK graphical front-end for id3lyrics, shows the current lyrics
and the title and path when available. """

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
import id3lyrics

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        # initial size
        self.set_default_size(350, 600)
        # window title (to be shown in the DE)
        self.set_wmclass('Lyrics', 'Lyrics')
        # window icon
        self.set_icon_name('audio-x-generic-symbolic')

        # window header
        self.header = Gtk.HeaderBar(title='ID3 Lyrics GUI')
        self.header.props.show_close_button = True
        self.set_titlebar(self.header)

        # we only need one scrolled window (for lyrics)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
                hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                vscrollbar_policy=Gtk.PolicyType.ALWAYS)
        self.scrolled_window.set_border_width(10)

        # a label is used inside the scrolled window
        self.label = Gtk.Label('Waiting for a player...')
        self.label.set_line_wrap(True)

        self.scrolled_window.add_with_viewport(self.label)
        self.add(self.scrolled_window)

        def callback_func(path, title, lyrics):
            # set the label text inside the scrolled window as the lyrics
            self.label.set_text(lyrics)

            # move the scrolled window to the top
            vadjustment = self.scrolled_window.get_vadjustment()
            vadjustment.set_value(vadjustment.get_lower())
            self.scrolled_window.set_vadjustment(vadjustment)

            # include path in the header
            if path != None:
                self.header.set_subtitle(path)
            else:
                self.header.set_subtitle('')

            # include title in the header
            if title != None:
                self.header.set_title(title)
            else:
                self.header.set_title('ID3 Lyrics GUI')

        # finally we can create a monitor object
        id3lyrics.ID3LyricsMonitor(callback_func)

window = MainWindow()
window.connect('delete-event', Gtk.main_quit)
window.show_all()

# this line also runs the monitor, as it uses GLib internally
Gtk.main()
