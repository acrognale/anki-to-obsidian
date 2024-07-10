import argparse
import json
import logging
import os

import requests

from sync.anki_html_parser import anki_to_md
from sync.card_parser import Card, parse_cards
from sync.diff import diff

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s"
)


def get_deck_notes(deck_name):
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"deck:{deck_name}"},
    }
    response = requests.post("http://localhost:8765", json=payload)
    return json.loads(response.text)["result"]


def get_note_info(note_id: str):
    payload = {"action": "notesInfo", "version": 6, "params": {"notes": [note_id]}}
    response = requests.post("http://localhost:8765", json=payload)
    return json.loads(response.text)["result"][0]


def get_card_diff(card: Card) -> tuple[str, str]:
    with open(card.source, "r") as file:
        content = file.read()

    # Reparse the card to get the correct indices
    parsed_cards = parse_cards(content, card.source)
    updated_card = next((c for c in parsed_cards if c.id == card.id), None)

    if not updated_card:
        logging.error(f"Card with ID {card.id} not found in {card.source}")
        return "", ""

    old_content = content[updated_card.start_idx : updated_card.end_idx].strip()
    new_content = f"Q: {card.question}\n{card.answer}\n<!--ID: {card.id}-->"

    return old_content, new_content


def update_card(
    card: Card,
    dryrun: bool,
):
    with open(card.source, "r") as file:
        content = file.read()

    # Reparse the card to get the correct indices
    parsed_cards = parse_cards(content, card.source)
    updated_card = next((c for c in parsed_cards if c.id == card.id), None)

    if not updated_card:
        logging.error(f"Card with ID {card.id} not found in {card.source}")

        return

    updated_content = (
        content[: updated_card.start_idx]
        + f"Q: {card.question}\n{card.answer}\n<!--ID: {card.id}-->"
        + content[updated_card.end_idx :]
    )

    if dryrun:
        with open("test.md", "w") as file:
            file.write(updated_content)
        return

    with open(card.source, "w") as file:
        file.write(updated_content)


def load_all_cards_in_dir(dir: str) -> dict[str, Card]:
    logging.info(f"Loading cards from {dir}")
    cards = {}
    for root, dirs, files in os.walk(dir):
        for file_path in files:
            if file_path.endswith(".md"):
                with open(os.path.join(root, file_path), "r") as file:
                    content = file.read()
                for card in parse_cards(content, os.path.join(root, file_path)):
                    cards[card.id] = card
    logging.info(f"Loaded {len(cards)} cards from {dir}")
    return cards


def get_anki_cards(deck_name: str) -> dict[str, Card]:
    logging.info(f"Getting cards from Anki deck {deck_name}")
    note_ids = get_deck_notes(deck_name)
    cards = {}
    for note_id in note_ids:
        note_info = get_note_info(note_id)
        cards[str(note_id)] = Card(
            anki_to_md(note_info["fields"]["Front"]["value"]),
            anki_to_md(note_info["fields"]["Back"]["value"]),
            note_id,
            "",
            0,
            0,
        )
    logging.info(f"Got {len(cards)} cards from Anki deck {deck_name}")
    return cards


def get_changed_cards(
    obsidian_cards: dict[str, Card], anki_cards: dict[str, Card]
) -> list[Card]:
    changed_cards = []
    for anki_card in anki_cards.values():
        if anki_card.id in obsidian_cards:
            obsidian_card = obsidian_cards[anki_card.id]
            if (
                anki_card.question != obsidian_card.question
                or anki_card.answer != obsidian_card.answer
            ):
                changed_cards.append(
                    Card(
                        anki_card.question,
                        anki_card.answer,
                        anki_card.id,
                        obsidian_card.source,
                        obsidian_card.start_idx,
                        obsidian_card.end_idx,
                    )
                )
    return changed_cards


def sync_anki_to_markdown(
    deck_name: str, markdown_dir: str, dryrun: bool, interactive: bool
):
    logging.info(f"Syncing Anki deck {deck_name} to Markdown files in {markdown_dir}")
    anki_cards = get_anki_cards(deck_name)
    obsidian_cards = load_all_cards_in_dir(markdown_dir)
    changed_cards = get_changed_cards(obsidian_cards, anki_cards)

    for card in changed_cards:
        logging.info(f"Updating card {card.id} in {card.source}")
        if interactive:
            prev, new = get_card_diff(card)
            print(f"Card ID: {card.id}")
            print(diff(prev, new, context_lines=2))
            user_input = input("Do you want to sync this card? (y/n): ").lower().strip()
            if user_input != "y":
                logging.info(f"Skipping card {card.id}")
                continue
        update_card(card, dryrun)

    logging.info(f"Synced {len(changed_cards)} cards from Anki to Markdown files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", type=str, default="Default")
    parser.add_argument(
        "--dir", type=str, default="/Users/anthony/Documents/obsidian/vault"
    )
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument(
        "--interactive", action="store_true", help="Prompt for each card before syncing"
    )

    args = parser.parse_args()
    sync_anki_to_markdown(args.deck, args.dir, args.dryrun, args.interactive)
