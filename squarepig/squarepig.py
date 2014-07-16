#!/usr/bin/python3

"""Square Pig."""

import argparse
import imp
import sys
from os import path
from backpig import SquarePig, Playlist


GUI = True

try:
    # Check if PyQt is installed.
    imp.find_module('PyQt4')
except ImportError:
    GUI = False


def gui():
    """GUI."""
    from qtpig import main as gui_main
    gui_main()


def main():
    """Run Square Pig."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--playlist', metavar='PLAYLIST', type=str,
        help='playlist file - supported formats: [ m3u, xspf ]')
    parser.add_argument(
        '-d', '--destination', metavar='DESTINATION', type=str,
        help='target directory')
    parser.add_argument(
        '-m', '--musicdir', metavar='MUSIC_DIR', type=str,
        help='prefix paths in playlist with MUSIC_DIR')
    args = parser.parse_args()

    arg_count = 0
    if args.destination:
        arg_count += 1
        if path.isfile(path.expanduser(args.destination)):
            parser.error("DESTINATION {0} is a file.".format(args.destination))
    if args.playlist:
        arg_count += 1
        playlist = args.playlist
    musicdir = None
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
            sys.stderr.write(e + "\n")
            exit(1)


if __name__ == "__main__":
    main()
