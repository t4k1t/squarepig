"""Tests for the CLI of squarepig."""

import pytest

from squarepig.main import main
from squarepig import __version__


class TestCLI:

    """Test CLI."""

    def test_cli(self, capsys, monkeypatch):
        """Test help text output."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-h'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "usage:" in out.lower()

    def test_version(self, capsys, monkeypatch):
        """Test version string output."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-V'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        # in python-3.3 argparse writes the version string to stderr but in
        # python-3.4 it writes to stdout so both is acceptable
        assert "Squarepig {version}".format(version=__version__) in (
            out or err)

    def test_invalid_playlist(self, capsys, monkeypatch):
        """Test invalid playlist argument."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-p',
                            'totally_invalid_playlist_path', '-d',
                            'invalid_destination_path'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "unable to find" in err

    def test_missing_playlist(self, capsys, monkeypatch):
        """Test missing playlist argument."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-d',
                            'totally_invalid_destination_path'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "mutually inclusive" in err
