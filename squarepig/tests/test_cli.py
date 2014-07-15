"""Tests for the CLI of squarepig."""

import pytest

from squarepig.squarepig import main


class TestCLI:

    """Test CLI."""

    def test_cli(self, capsys, monkeypatch):
        """Test CLI."""
        monkeypatch.setattr('sys.argv', ['squarepig.py', '-h'])
        with pytest.raises(SystemExit):
            main()
        out, err = capsys.readouterr()
        assert "usage:" in out.lower()
