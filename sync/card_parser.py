import re


class Card:
    def __init__(
        self,
        question: str,
        answer: str,
        id: str,
        source: str,
        start_idx: int,
        end_idx: int,
    ):
        self.question = question
        self.answer = answer
        self.id = str(id)
        self.source = source
        self.start_idx = start_idx
        self.end_idx = end_idx

    def __str__(self):
        return f"""ID: {self.id}
Source: {self.source}
Q: {self.question}
A: {self.answer}"""

    def __repr__(self) -> str:
        return self.__str__()


def parse_cards(content: str, source: str) -> list[Card]:
    card_pattern = re.compile(
        r"Q:\s*(.+?)\n((?:(?!Q:).+\n)+?)<!--ID:\s*(\S+)\s*-->", re.MULTILINE
    )

    cards = []
    for match in card_pattern.finditer(content):
        question = match.group(1).strip()
        answer = match.group(2).strip()
        card_id = match.group(3)
        start_idx = match.start()
        end_idx = match.end()

        card = Card(question, answer, card_id, source, start_idx, end_idx)
        cards.append(card)

    return cards
