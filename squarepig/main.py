#!/usr/bin/env python

"""Squarepig."""

import argparse
import gettext
from imp import find_module
from os import path
from sys import stderr

from squarepig import __version__
from squarepig.backpig import SquarePig, Playlist


GUI = True

try:
    # check if PyQt is installed
    find_module('PyQt4')
except ImportError:
    GUI = False


gettext.install('squarepig', '/usr/share/locale')


def gui():
    """Start GUI."""
    from squarepig.qtpig import main as gui_main
    gui_main()


def main():
    """Run Squarepig."""
    parser = argparse.ArgumentParser(prog='squarepig')
    parser.add_argument(
        '-p', '--playlist', metavar='PLAYLIST', type=str,
        help='playlist file - supported formats: [ m3u, xspf ]')
    parser.add_argument(
        '-d', '--destination', metavar='DESTINATION', type=str,
        help='target directory')
    parser.add_argument(
        '-m', '--musicdir', metavar='MUSIC_DIR', type=str,
        help='prefix paths in playlist with MUSIC_DIR')
    parser.add_argument(
        '-V', '--version', action='version',
        version='Squarepig {version}'.format(version=__version__))
    args = parser.parse_args()

    # TODO: Check if this initialisation still makes sense
    musicdir = None
    playlist = None

    # count number of supplied arguments since argparse doesn't seem to
    # implement any convenience function for this
    arg_count = 0
    pl_and_dest = 0
    if args.destination:
        arg_count += 1
        if path.isfile(path.expanduser(args.destination)):
            parser.error("DESTINATION {0} is a file.".format(args.destination))
        pl_and_dest += 1
    if args.playlist:
        arg_count += 1
        playlist = args.playlist
        pl_and_dest += 1
    if pl_and_dest % 2 is not 0:
        parser.error(
            "destination and playlist arguments are mutually inclusive")
    if args.musicdir:
        arg_count += 1
        musicdir = path.expanduser(args.musicdir)

    if arg_count == 0:
        if GUI:
            gui()
        else:
            parser.print_help()
    else:
        sargasso = SquarePig()
        try:
            playlist = Playlist(playlist, musicdir)
        except Playlist.UnknownPlaylistFormat:
            parser.error("unknown playlist format")
        except Playlist.UnsupportedPlaylistFormat as e:
            parser.error("unsupported playlist format: {0}\n".format(e))
        except FileNotFoundError:
            parser.error("unable to find '{0}'\n".format(playlist))
        try:
            sargasso.copy_to(playlist.get_files(), args.destination)
        except SquarePig.CopyError as e:
            stderr.write(str(e) + "\n")
            exit(1)


if __name__ == "__main__":
    main()
