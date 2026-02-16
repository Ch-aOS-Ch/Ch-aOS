import os
from unittest.mock import Mock, patch

import pytest

from chaos.lib.ramble import (
    handleCreateRamble,
    handleDelRamble,
    handleReadRamble,
)


@pytest.fixture
def mock_ramble_home(tmp_path, monkeypatch):
    ramble_dir = tmp_path / ".local/share/chaos/ramblings"
    ramble_dir.mkdir(parents=True)

    def mock_expanduser(path):
        if path.startswith("~"):
            # Substitui apenas o til no início do caminho
            return str(tmp_path) + path[1:]
        return str(tmp_path)

    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    monkeypatch.setattr("chaos.lib.ramble._get_ramble_dir", lambda team: ramble_dir)
    return ramble_dir


def test_create_ramble_journal_and_page(mock_ramble_home):
    args = Mock()
    args.target = "diary"  # cria um diário
    args.encrypt = False
    args.keys = []
    args.sops_file_override = None
    args.team = None

    with patch("chaos.lib.ramble.subprocess.run"):
        handleCreateRamble(args)

    journal_path = mock_ramble_home / "diary"
    page_path = journal_path / "diary.yml"
    assert journal_path.is_dir()
    assert page_path.is_file()

    content = page_path.read_text()
    assert "title: diary" in content


def test_create_ramble_page_in_journal(mock_ramble_home):
    args = Mock()
    args.target = "work.meeting_notes"
    args.encrypt = False
    args.keys = []
    args.sops_file_override = None
    args.team = None

    with patch("chaos.lib.ramble.subprocess.run"):
        handleCreateRamble(args)

    journal_path = mock_ramble_home / "work"
    page_path = journal_path / "meeting_notes.yml"
    assert journal_path.is_dir()
    assert page_path.is_file()

    content = page_path.read_text()
    assert "title: meeting_notes" in content


def test_read_and_delete_ramble(mock_ramble_home, monkeypatch):
    journal_path = mock_ramble_home / "todo"
    page_path = journal_path / "shopping.yml"
    journal_path.mkdir()
    page_path.write_text("title: Shopping List\nwhat: a list of things to buy")

    read_args = Mock()
    read_args.targets = ["todo.shopping"]
    read_args.sops_file_override = None
    read_args.team = None
    read_args.from_bw = None
    read_args.from_bws = None
    read_args.from_op = None
    read_args.provider = None

    # Simula a descoberta de config global
    with patch("chaos.lib.ramble.os.path.exists") as mock_exists:
        mock_exists.return_value = False
        _process_ramble_target_path = "chaos.lib.ramble._print_ramble"
        with patch(_process_ramble_target_path) as mock_print_ramble:
            handleReadRamble(read_args)

    # Verifica se a função de impressão foi chamada corretamente
    mock_print_ramble.assert_called_once()

    del_args = Mock()
    del_args.ramble = "todo.shopping"
    del_args.team = None

    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)

    handleDelRamble(del_args)

    assert not page_path.exists()
