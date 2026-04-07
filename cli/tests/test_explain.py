from unittest.mock import Mock, patch

import pytest

from chaos.lib.explain import handleExplain


class MockExplain:
    _order = ["sub"]

    def explain_main(self, complexity="basic"):
        return {"concept": "Main Concept", "what": "This is the main topic."}

    def explain_sub(self, complexity="basic"):
        return {"concept": "Sub Concept", "what": "This is the sub topic."}


@pytest.fixture
def mock_args():
    args = Mock()
    args.details = "basic"
    args.no_pretty = False
    args.complexity = "basic"
    args.json = False
    return args


@pytest.fixture
def mock_dispatcher():
    return {"main": "chaos.lib.explain:MockExplain"}


@patch("chaos.lib.explain.import_module")
def test_handle_explain_main_topic(mock_import, capsys, mock_args, mock_dispatcher):
    mock_import.return_value.MockExplain = MockExplain
    mock_args.topics = ["main"]

    with patch.dict(mock_dispatcher, {"main": "test_module:MockExplain"}):
        handleExplain(mock_args, mock_dispatcher)

    captured = capsys.readouterr()
    assert "Main Concept" in captured.out
    assert "This is the main topic" in captured.out


@patch("chaos.lib.explain.import_module")
def test_handle_explain_sub_topic(mock_import, capsys, mock_args, mock_dispatcher):
    mock_import.return_value.MockExplain = MockExplain
    mock_args.topics = ["main.sub"]

    with patch.dict(mock_dispatcher, {"main": "test_module:MockExplain"}):
        handleExplain(mock_args, mock_dispatcher)

    captured = capsys.readouterr()
    assert "Sub Concept" in captured.out
    assert "This is the sub topic" in captured.out


@patch("chaos.lib.explain.sys.exit")
@patch("chaos.lib.explain.import_module")
def test_handle_explain_list_subtopics(mock_import, mock_exit, capsys, mock_args, mock_dispatcher):
    mock_import.return_value.MockExplain = MockExplain
    mock_args.topics = ["main.list"]

    with patch.dict(mock_dispatcher, {"main": "test_module:MockExplain"}):
        handleExplain(mock_args, mock_dispatcher)

    captured = capsys.readouterr()
    assert "Available subtopics for" in captured.out
    assert "main" in captured.out
    assert "sub" in captured.out
    mock_exit.assert_called_once_with(0)


@patch("chaos.lib.explain.import_module")
def test_handle_explain_invalid_topic(mock_import, capsys, mock_args, mock_dispatcher):
    mock_import.return_value.MockExplain = MockExplain
    mock_args.topics = ["invalid_topic"]

    with patch.dict(mock_dispatcher, {"main": "test_module:MockExplain"}):
        handleExplain(mock_args, mock_dispatcher)

    captured = capsys.readouterr()
    assert "ERROR:" in captured.out
    assert "No explanation found for topic 'invalid_topic'" in captured.out
