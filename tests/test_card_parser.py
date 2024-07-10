from sync.card_parser import Card, parse_cards


def test_card_initialization():
    card = Card("What is Python?", "A programming language", "1", "test.md", 0, 3)
    assert card.question == "What is Python?"
    assert card.answer == "A programming language"
    assert card.id == "1"
    assert card.source == "test.md"
    assert card.start_idx == 0
    assert card.end_idx == 3


def test_card_str_representation():
    card = Card("What is Python?", "A programming language", "1", "test.md", 0, 3)
    expected_str = """ID: 1
Source: test.md
Q: What is Python?
A: A programming language"""
    assert str(card) == expected_str


def test_parse_cards_single_card():
    content = """Q: What is Python?
- A high-level programming language
- Known for its readability and simplicity
<!--ID: 123-->"""
    cards = parse_cards(content, "test.md")
    assert len(cards) == 1
    assert cards[0].question == "What is Python?"
    assert (
        cards[0].answer
        == "- A high-level programming language\n- Known for its readability and simplicity"
    )
    assert cards[0].id == "123"
    assert cards[0].source == "test.md"
    assert cards[0].start_idx == 0
    assert cards[0].end_idx == len(content)


def test_parse_cards_multiple_cards():
    content = """Q: What is Python?
- A high-level programming language
- Known for its readability and simplicity
<!--ID: 1-->

Q: Who created Python?
- Guido van Rossum
<!--ID: 2-->

Q: When was Python first released?
- 1991
<!--ID: 3-->"""
    cards = parse_cards(content, "test.md")
    assert len(cards) == 3
    assert cards[0].question == "What is Python?"
    assert (
        cards[0].answer
        == "- A high-level programming language\n- Known for its readability and simplicity"
    )
    assert cards[0].id == "1"
    assert cards[1].question == "Who created Python?"
    assert cards[1].answer == "- Guido van Rossum"
    assert cards[1].id == "2"
    assert cards[2].question == "When was Python first released?"
    assert cards[2].answer == "- 1991"
    assert cards[2].id == "3"


def test_parse_cards_no_valid_cards():
    content = "This is some content without any valid cards."
    cards = parse_cards(content, "test.md")
    assert len(cards) == 0


def test_parse_cards_missing_id():
    content = """Q: What is Python?
- A high-level programming language

Q: Who created Python?
- Guido van Rossum
<!--ID: 2-->"""
    cards = parse_cards(content, "test.md")
    assert len(cards) == 1
    assert cards[0].question == "Who created Python?"
    assert cards[0].answer == "- Guido van Rossum"
    assert cards[0].id == "2"


def test_random_bullets():
    content = r"""- Mathematical Perspective: Consider the chain rule when computing gradients. For an RNN, this involves multiplying many Jacobian matrices together: $\frac{\partial L}{\partial W} = \sum_{t=1}^T \frac{\partial L}{\partial y_T} \frac{\partial y_T}{\partial h_T} \frac{\partial h_T}{\partial h_t} \frac{\partial h_t}{\partial W}$ Where $\frac{\partial h_T}{\partial h_t} = \prod_{i=t}^{T-1} \frac{\partial h_{i+1}}{\partial h_i}$ This product of many terms (potentially hundreds or thousands for long sequences) can result in extremely small values if each term is less than 1
- Activation Function Role: Common activation functions like tanh or sigmoid have gradients in the range (0,1). Repeated multiplication of these small values leads to exponential decay of the gradient.
- Architectural Implications: This problem led to the development of architectures like LSTMs and GRUs, which use gating mechanisms to better control the flow of information and gradients through the network.
"""

    cards = parse_cards(content, "test.md")
    assert len(cards) == 0


def test_text_after_card():
    content = """
Q: Old Question
- New Answer
<!--ID: 123-->
Some other content
Q: Another Question
- Another Answer
    """

    cards = parse_cards(content, "test.md")
    assert len(cards) == 1
    assert cards[0].question == "Old Question"
    assert cards[0].answer == "- New Answer"
    assert cards[0].id == "123"
    assert cards[0].source == "test.md"
