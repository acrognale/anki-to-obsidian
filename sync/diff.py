import difflib


def diff(
    old_content: str,
    new_content: str,
    *,
    use_loguru_colors: bool = False,
    context_lines: int = 3,
) -> str:
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    differ = difflib.Differ()
    diff_lines = list(differ.compare(old_lines, new_lines))

    if use_loguru_colors:
        green = "<GREEN>"
        red = "<RED>"
        endcolor = "</GREEN></RED>"
    else:
        green = "\033[32m"
        red = "\033[31m"
        endcolor = "\033[0m"

    output = []
    in_diff = False
    context_buffer = []

    for line in diff_lines:
        if line.startswith("  "):
            if in_diff:
                output.append(line)
            else:
                context_buffer.append(line)
                if len(context_buffer) > context_lines:
                    context_buffer.pop(0)
        elif line.startswith("- ") or line.startswith("+ "):
            if not in_diff:
                output.extend(context_buffer)
                context_buffer = []
            in_diff = True
            output.append(f"{red if line.startswith('- ') else green}{line}{endcolor}")

        if in_diff and len(output) > context_lines * 2:
            in_diff = False

    return "\n".join(output)
