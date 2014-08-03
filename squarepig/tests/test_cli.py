"""Tests for the CLI of squarepig."""

import pytest

from squarepig.main import main
from squarepig import __version__


class TestCLI:

    """Test CLI."""

    def test_cli(self, capsys, monkeypatch):
        """Test CLI."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-h'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "usage:" in out.lower()

    def test_version(self, capsys, monkeypatch):
        """Test CLI."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-V'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "Squarepig {version}".format(version=__version__) in out
