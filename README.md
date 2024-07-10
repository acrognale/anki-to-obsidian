# anki-to-obsidian

There are multiple plugins that exist for Obsidian that allow users to sync _from_ Obsidian to Anki, but I couldn't find any that allowed users to sync _to_ Obsidian from Anki. Sometimes I just want to edit a card in Anki from my phone without having to find the corresponding card in Obisdian or remember to do it later.

This project provides a tool to synchronize Anki flashcards with Obsidian markdown files. It allows you to keep your Anki cards and Obsidian notes in sync, making it easier to manage your knowledge base across both platforms.

## Features

- Sync Anki cards to Obsidian markdown files
- Update existing cards in Obsidian with changes from Anki
- Support for multiple decks and markdown files
- Dry run option for testing changes without applying them
- Interactive mode for reviewing changes before applying

## Limitations

- It's _very_ tailored to my custom workflow. I use the following question and answer structure for my cards:

```
Q: the question
- answer line one
- answer line two
<!--ID: 123-->
```

I use the [Obsidian_to_Anki](https://github.com/ObsidianToAnki/Obsidian_to_Anki) plugin to sync my Obsidian vault to Anki, and then use this tool to sync my Anki cards back to Obsidian.

I'll probably add cloze support in the future, but probably won't add other card types as I don't use them.

If you have a different question and answer structure, you'll need to modify the code to support it-- you can change the regex in `sync/card_parser.py` to match your structure, however this will break the unit tests if you wish to run them.

## Installation

1. Ensure you have Python 3.9 or higher installed.
2. Clone this repository:

```bash
git clone https://github.com/acrognale/anki-to-obsidian.git
cd anki-to-obsidian
```

3. Install the required dependencies using Poetry:

```
poetry install
```

## Usage

To run the sync process, use the following command:

```

poetry run python -m sync.main --deck "Your Deck Name" --dir "/path/to/your/obsidian/vault" [--dryrun] [--interactive]

```

Options:

- `--deck`: Specify the name of the Anki deck to sync (default: "Default")
- `--dir`: Specify the path to your Obsidian vault (default: "/Users/anthony/Documents/obsidian/vault")
- `--dryrun`: Run the sync process without making any changes (for testing)
- `--interactive`: Prompt for confirmation before syncing each card

## How it works

1. The script retrieves all cards from the specified Anki deck.
2. It then scans the specified Obsidian directory for markdown files containing card information.
3. The script compares the Anki cards with the Obsidian cards and identifies any changes.
4. For each changed card, it updates the corresponding markdown file in Obsidian.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
