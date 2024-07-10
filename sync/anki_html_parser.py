import re

from markdownify import markdownify as md

from sync.diff import diff


def anki_to_md(html: str) -> str:
    # replace <anki-mathjax> with $$
    html = html.replace("\\(", "$").replace("\\)", "$")
    html = html.replace("\\[", "$$").replace("\\]", "$$")

    # remove the very last a tag
    html = re.sub(r"<a href=.*?>Obsidian</a>", "", html)

    # Convert HTML to Markdown
    markdown = md(
        html,
        bullets=["-"],
        escape_misc=False,
        escape_underscores=False,
        escape_asterisks=False,
    )

    # Strip empty lines or lines that only contain whitespace
    markdown = "\n".join(line for line in markdown.splitlines() if line.strip())

    return markdown
