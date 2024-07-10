import json
from unittest.mock import mock_open, patch

import pytest

from sync.card_parser import Card, parse_cards
from sync.main import (
    get_anki_cards,
    get_changed_cards,
    get_deck_notes,
    get_note_info,
    load_all_cards_in_dir,
    sync_anki_to_markdown,
    update_card,
)


@pytest.fixture
def mock_requests_post():
    with patch("requests.post") as mock_post:
        yield mock_post


def test_get_deck_notes(mock_requests_post):
    mock_response = mock_requests_post.return_value
    mock_response.text = json.dumps({"result": [1, 2, 3]})

    result = get_deck_notes("Test Deck")

    assert result == [1, 2, 3]
    mock_requests_post.assert_called_once_with(
        "http://localhost:8765",
        json={
            "action": "findNotes",
            "version": 6,
            "params": {"query": "deck:Test Deck"},
        },
    )


def test_get_note_info(mock_requests_post):
    mock_response = mock_requests_post.return_value
    mock_response.text = json.dumps(
        {
            "result": [
                {
                    "noteId": 1,
                    "fields": {
                        "Front": {"value": "Question"},
                        "Back": {"value": "Answer"},
                    },
                }
            ]
        }
    )

    result = get_note_info(1)

    assert result == {
        "noteId": 1,
        "fields": {"Front": {"value": "Question"}, "Back": {"value": "Answer"}},
    }
    mock_requests_post.assert_called_once_with(
        "http://localhost:8765",
        json={"action": "notesInfo", "version": 6, "params": {"notes": [1]}},
    )


def test_update_card():
    mock_file_content = """
Q: Old Question
- Old Answer
<!--ID: 123-->
Some other content
Q: Another Question
- Another Answer
    """
    expected_content = """
Q: Old Question
- New Answer
<!--ID: 123-->
Some other content
Q: Another Question
- Another Answer
    """

    old_card = parse_cards(mock_file_content, "test.md")[0]
    new_card = parse_cards(expected_content, "test.md")[0]

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        update_card(
            Card(
                new_card.question,
                new_card.answer,
                new_card.id,
                new_card.source,
                old_card.start_idx,
                old_card.end_idx,
            ),
            False,
        )
        mock_file().write.assert_called_once_with(expected_content)


def test_update_card_multiple_cards():
    mock_file_content = """Q: Old Question
- Old Answer
<!--ID: 123-->
Some other content
Q: Another Question
- Another Answer
<!--ID: 456-->
Some other content
    """

    expected_content = """Q: Old Question
- New Answer
<!--ID: 123-->
Some other content
Q: Another Question
- Another Answer
<!--ID: 456-->
Some other content
    """

    cards = parse_cards(mock_file_content, "test.md")
    new_cards = parse_cards(expected_content, "test.md")

    card_to_update = Card(
        new_cards[0].question,
        new_cards[0].answer,
        new_cards[0].id,
        new_cards[0].source,
        cards[0].start_idx,
        cards[0].end_idx,
    )

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        update_card(card_to_update, False)
        mock_file().write.assert_called_once_with(expected_content)


@patch("sync.main.get_anki_cards")
@patch("sync.main.load_all_cards_in_dir")
@patch("sync.main.get_changed_cards")
@patch("sync.main.update_card")
def test_sync_anki_to_markdown(mock_update, mock_get_changed, mock_load, mock_get_anki):
    mock_get_anki.return_value = {
        "1": Card("Q1", "A1", "1", "", 0, 0),
        "2": Card("Q2", "A2", "2", "", 0, 0),
    }
    mock_load.return_value = {
        "1": Card("Q1", "Old A1", "1", "file1.md", 0, 20),
        "2": Card("Q2", "A2", "2", "file1.md", 21, 40),
    }
    mock_get_changed.return_value = [Card("Q1", "A1", "1", "file1.md", 0, 20)]

    sync_anki_to_markdown("Test Deck", "/path", False, False)

    mock_get_anki.assert_called_once_with("Test Deck")
    mock_load.assert_called_once_with("/path")
    mock_get_changed.assert_called_once()
    mock_update.assert_called_once()


@patch("sync.main.get_anki_cards")
@patch("sync.main.load_all_cards_in_dir")
@patch("sync.main.get_changed_cards")
@patch("sync.main.update_card")
def test_sync_anki_to_markdown_empty_deck(
    mock_update, mock_get_changed, mock_load, mock_get_anki
):
    mock_get_anki.return_value = {}
    mock_load.return_value = {"1": Card("Q1", "A1", "1", "file1.md", 0, 20)}

    sync_anki_to_markdown("Empty Deck", "/path", False, False)

    mock_get_anki.assert_called_once_with("Empty Deck")
    mock_load.assert_called_once_with("/path")
    mock_get_changed.assert_called_once()
    mock_update.assert_not_called()


@patch("os.walk")
@patch("builtins.open", new_callable=mock_open)
def test_load_all_cards_in_dir(mock_file, mock_walk):
    mock_walk.return_value = [
        ("/path", [], ["file1.md", "file2.txt"]),
        ("/path/subdir", [], ["file3.md"]),
    ]
    mock_file.return_value.read.side_effect = [
        "Q: Q1\nA1\n<!--ID: 1-->",
        "Q: Q2\nA2\n<!--ID: 2-->",
    ]

    result = load_all_cards_in_dir("/path")

    assert len(result) == 2
    assert "1" in result
    assert "2" in result
    assert result["1"].question == "Q1"
    assert result["2"].question == "Q2"


@patch("sync.main.get_deck_notes")
@patch("sync.main.get_note_info")
def test_get_anki_cards(mock_get_info, mock_get_notes):
    mock_get_notes.return_value = [1, 2]
    mock_get_info.side_effect = [
        {"fields": {"Front": {"value": "Q1"}, "Back": {"value": "A1"}}},
        {"fields": {"Front": {"value": "Q2"}, "Back": {"value": "A2"}}},
    ]

    result = get_anki_cards("Test Deck")

    assert len(result) == 2
    assert "1" in result
    assert "2" in result
    assert result["1"].question == "Q1"
    assert result["2"].question == "Q2"


def test_get_changed_cards():
    obsidian_cards = {
        "1": Card("Q1", "Old A1", "1", "file1.md", 0, 20),
        "2": Card("Q2", "A2", "2", "file1.md", 21, 40),
    }
    anki_cards = {
        "1": Card("Q1", "New A1", "1", "", 0, 0),
        "2": Card("Q2", "A2", "2", "", 0, 0),
    }

    result = get_changed_cards(obsidian_cards, anki_cards)

    assert len(result) == 1
    assert result[0].id == "1"
    assert result[0].answer == "New A1"
    assert result[0].source == "file1.md"


def test_update_markdown_file_with_bad_escape_sequences():
    mock_file_content = r"""
Q: Question with \special characters
- Old Answer
<!--ID: 123-->
Some other content
    """
    expected_content = r"""
Q: Question with \special characters
- Answer with \more \special characters
<!--ID: 123-->
Some other content
    """

    cards = parse_cards(mock_file_content, "test.md")
    new_cards = parse_cards(expected_content, "test.md")

    card_to_update = Card(
        new_cards[0].question,
        new_cards[0].answer,
        new_cards[0].id,
        new_cards[0].source,
        cards[0].start_idx,
        cards[0].end_idx,
    )

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        update_card(card_to_update, False)

        mock_file().write.assert_called_once_with(expected_content)


def test_dont_rewrite_latex():
    mock_file_content = r"""
Q: Question with $\frac{1}{2}$
- Old Answer
<!--ID: 456-->
Some other content
    """

    expected_file_content = r"""
Q: Question with $\frac{1}{2}$
- New answer
<!--ID: 456-->
Some other content
    """

    cards = parse_cards(mock_file_content, "test.md")
    new_cards = parse_cards(expected_file_content, "test.md")

    card_to_update = Card(
        new_cards[0].question,
        new_cards[0].answer,
        new_cards[0].id,
        new_cards[0].source,
        cards[0].start_idx,
        cards[0].end_idx,
    )

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        update_card(card_to_update, False)

        mock_file().write.assert_called_once_with(expected_file_content)


def test_update_markdown_file_with_regex_special_characters():
    mock_file_content = """
Q: Question with (parentheses) and [brackets]
- Old Answer
<!--ID: 456-->
Some other content
    """
    expected_content = """
Q: Question with (parentheses) and [brackets]
- New answer with * and + special characters
<!--ID: 456-->
Some other content
    """

    cards = parse_cards(mock_file_content, "test.md")
    new_cards = parse_cards(expected_content, "test.md")

    card_to_update = Card(
        new_cards[0].question,
        new_cards[0].answer,
        new_cards[0].id,
        new_cards[0].source,
        cards[0].start_idx,
        cards[0].end_idx,
    )

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        update_card(card_to_update, False)

        mock_file().write.assert_called_once_with(expected_content)


def test_update_card_with_shifting_indices():
    initial_content = """Q: First Question
- First Answer
<!--ID: 123-->
Some content
Q: Second Question
- Second Answer
<!--ID: 456-->
More content
Q: Third Question
- Third Answer
<!--ID: 789-->
Final content
"""

    # First update
    first_update_content = """Q: First Question
- Updated First Answer
<!--ID: 123-->
Some content
Q: Second Question
- Second Answer
<!--ID: 456-->
More content
Q: Third Question
- Third Answer
<!--ID: 789-->
Final content
"""

    # Second update (notice the indices will have shifted)
    second_update_content = """Q: First Question
- Updated First Answer
<!--ID: 123-->
Some content
Q: Updated Second Question
- Updated Second Answer
<!--ID: 456-->
More content
Q: Third Question
- Third Answer
<!--ID: 789-->
Final content
"""

    with patch("builtins.open", mock_open(read_data=initial_content)) as mock_file:
        # First update
        cards = parse_cards(initial_content, "test.md")
        new_cards = parse_cards(first_update_content, "test.md")
        card_to_update = Card(
            new_cards[0].question,
            new_cards[0].answer,
            new_cards[0].id,
            new_cards[0].source,
            cards[0].start_idx,
            cards[0].end_idx,
        )
        update_card(card_to_update, False)

        # Second update
        mock_file.return_value.read.return_value = first_update_content
        cards = parse_cards(first_update_content, "test.md")
        new_cards = parse_cards(second_update_content, "test.md")
        card_to_update = Card(
            new_cards[1].question,
            new_cards[1].answer,
            new_cards[1].id,
            new_cards[1].source,
            cards[1].start_idx,
            cards[1].end_idx,
        )
        update_card(card_to_update, False)

        # Check final content
        mock_file().write.assert_called_with(second_update_content)
