id3lyrics
=========
A set of python scripts to display or search ID3 lyrics.

It is designed to work only using the embedded lyrics, therefore it does
**not** connect to internet at all.

id3lyrics.py
------------
A monitor class that provides the lyrics of the music currently playing.
Also includes a command-line interface to this class.
It should work with any MPRIS capable player. Tested with:
* audacious
* clementine
* gnome-music
* gogglesmm
* pragha
* qmmp
* quodlibet
* rhythmbox

id3gui.py
---------
A GTK frontend for id3lyrics.py.  
![gui screenshot](https://cloud.githubusercontent.com/assets/8158408/11224415/89906e1c-8d7d-11e5-9545-ff47cfc27561.png)

id3search.py
------------
A simple search engine for lyrics. Given a folder, it finds the music files
that include the given string in their lyrics.

Requirements
------------
* GLib
* mutagen
* GTK (for GUI)

Implementation Details
----------------------
The library (id3lyrics.py) communicates with the music player using the
MPRIS interface over D-Bus. Using this, it acquires the location of the
music currently playing.

Then, mutagen library is used to extract the lyrics (USLT, unsynced lyrics).
This information is then provided to interested parties using a callback
function.
