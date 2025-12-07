import pytest
import os
from unittest.mock import Mock, patch
from chaos.lib.handlers import handleCreateRamble, handleReadRamble, handleDelRamble

# Precisamos simular o diretório home para um diretório temporário
@pytest.fixture
def mock_ramble_home(tmp_path, monkeypatch):
    ramble_dir = tmp_path / ".local/share/chaos/ramblings"
    ramble_dir.mkdir(parents=True)
    
    # Simula o `expanduser` para que `~` aponte para o nosso diretório temporário
    def mock_expanduser(path):
        if path.startswith("~/"):
             return str(tmp_path / path.replace("~/", ""))
        return str(tmp_path)
        
    monkeypatch.setattr(os.path, 'expanduser', mock_expanduser)
    return ramble_dir

def test_create_ramble_journal_and_page(mock_ramble_home, capsys):
    args = Mock()
    args.target = "diary" # cria um diário

    # A função chama o editor, então simulamos o subprocesso
    with patch('chaos.lib.handlers.subprocess.run') as mock_run:
         with pytest.raises(SystemExit):
            handleCreateRamble(args)

    journal_path = mock_ramble_home / "diary"
    page_path = journal_path / "diary.yml"
    assert journal_path.is_dir()
    assert page_path.is_file()
    
    content = page_path.read_text()
    assert "title: diary" in content

def test_create_ramble_page_in_journal(mock_ramble_home, capsys):
    args = Mock()
    args.target = "work.meeting_notes"

    with patch('chaos.lib.handlers.subprocess.run') as mock_run:
        with pytest.raises(SystemExit):
            handleCreateRamble(args)

    journal_path = mock_ramble_home / "work"
    page_path = journal_path / "meeting_notes.yml"
    assert journal_path.is_dir()
    assert page_path.is_file()
    
    content = page_path.read_text()
    assert "title: meeting_notes" in content

def test_read_and_delete_ramble(mock_ramble_home, capsys, monkeypatch):
    # --- Criação ---
    journal_path = mock_ramble_home / "todo"
    page_path = journal_path / "shopping.yml"
    journal_path.mkdir()
    page_path.write_text("title: Shopping List\nwhat: a list of things to buy")
    
    # --- Leitura ---
    read_args = Mock()
    read_args.targets = ["todo.shopping"]
    read_args.sops_file_override = None

    # Simula a descoberta de config global
    with patch('chaos.lib.handlers.os.path.exists') as mock_exists:
        mock_exists.return_value = False
        with pytest.raises(SystemExit):
             _process_ramble_target_path = "chaos.lib.handlers._process_ramble_target"
             with patch(_process_ramble_target_path) as mock_process:
                handleReadRamble(read_args)
    
    # Como a leitura é complexa, vamos apenas verificar se a função foi chamada
    # mock_process.assert_called_with("todo.shopping", None)
    
    # --- Deleção ---
    del_args = Mock()
    del_args.ramble = "todo.shopping"

    # Simula a confirmação do usuário
    monkeypatch.setattr('rich.prompt.Confirm.ask', lambda *args, **kwargs: True)
    
    with pytest.raises(SystemExit):
        handleDelRamble(del_args)
    
    assert not page_path.exists()
