#!/usr/bin/env python3
# Kaan Karaagacli
""" Search for a given string in the lyrics of the music
files inside a given folder. 

It is designed to work offline, therefore only the embedded
lyrics are checked. The files must end with a ".mp3" extension.

FOLDER_NAME is used when the script is run standalone.
The argument to the script is searched as the keyword,
or it is asked from the user if there is no argument.
"""

# edit your music folder name here
# it is expected to be inside your home directory
FOLDER_NAME="Music"

import os, sys
from mutagen.id3 import ID3, ID3NoHeaderError

def id3_search(text, folder):
    """ Search for a substring in the all music files in the given folder,
    including subdirectories, and print the paths of the matching ones. """

    # perform a linear search
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            # libmagic would be a much better choice
            if f.endswith(".mp3"):
                fullpath = os.path.join(dirpath, f)
                if check_for_lyrics(text, fullpath):
                    print(fullpath)

def check_for_lyrics(text, path):
    """ Check if a given text is a substring of the lyrics of the music file
    located in the given path. """
    try:
        # extract the lyrics using mutagen
        tags = ID3(path)
        lyrics = tags.getall("USLT")

        return len(lyrics) > 0 and text in lyrics[0].text
    except ID3NoHeaderError:
        return False

if __name__ == "__main__":
    # xdg spec would be a better choice here
    home = os.path.expanduser("~")
    path = os.path.join(home, FOLDER_NAME)

    if (len(sys.argv) > 1):
        # get the string from the arguments if possible
        text = ' '.join(sys.argv[1:])
    else:
        # else ask it from the user
        text = input("Enter text: ")

    try:
        id3_search(text, path)
    except KeyboardInterrupt:
        pass
