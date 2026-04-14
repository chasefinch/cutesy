"""Types to support Cutesy."""

from data_enum import DataEnum


class Rule(DataEnum):
    """A rule to lint against."""

    __members__ = (
        # Temporary preprocessing rules
        "T1",
        # Preprocessing rules
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "P7",
        # Document structure rules
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
        "D10",
        # Formatting rules
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        # Encoding & language rules
        "E1",
        "E2",
        "E3",
        "E4",
        # Plugin rules
        "TW1",
    )

    message: str
    structural: bool


# Temporary preprocessing rules
Rule.T1 = Rule(
    message="Instruction not long enough to generate a placeholder",
    structural=True,
)

# Preprocessing rules
Rule.P1 = Rule(message="{tag} overlaps HTML elements or attributes", structural=True)
Rule.P2 = Rule(message="Expected {tag}", structural=True)
Rule.P3 = Rule(
    message="{tag} doesn't have a matching opening instruction",
    structural=True,
)
Rule.P4 = Rule(message="Malformed processing instruction", structural=True)
Rule.P5 = Rule(message="Extra whitespace in {tag}", structural=False)
Rule.P6 = Rule(message="Expected padding in {tag}", structural=False)
Rule.P7 = Rule(message="Use {tag} instead", structural=True)

# Document structure rules
Rule.D1 = Rule(message="Expected doctype before other HTML elements", structural=False)
Rule.D2 = Rule(
    message="Second declaration found; \u201cdoctype\u201d should be the only declaration",
    structural=False,
)
Rule.D3 = Rule(message="Expected {tag}", structural=False)
Rule.D4 = Rule(
    message="{tag} doesn\u2019t have a matching opening tag",
    structural=False,
)
Rule.D5 = Rule(message="Unnecessary self-closing of {tag}", structural=True)
Rule.D6 = Rule(message="Self-closing of non-void element {tag}", structural=True)
Rule.D7 = Rule(message="Malformed tag", structural=False)
Rule.D8 = Rule(message="Malformed closing tag", structural=False)
Rule.D9 = Rule(message="Expected blank line at end of document", structural=False)
Rule.D10 = Rule(message="Closing tag on void element {tag}", structural=True)

# Formatting rules
Rule.F1 = Rule(message="Doctype not lowercase", structural=False)
Rule.F2 = Rule(message="Trailing whitespace", structural=True)
Rule.F3 = Rule(message="Incorrect indentation", structural=True)
Rule.F4 = Rule(message="Extra vertical whitespace", structural=True)
Rule.F5 = Rule(message="Extra horizontal whitespace", structural=True)
Rule.F6 = Rule(message="Incorrect attribute order", structural=False)
Rule.F7 = Rule(message="{tag} incorrect case", structural=True)
Rule.F8 = Rule(message="Attribute \u201c{attr}\u201d incorrect case", structural=True)
Rule.F9 = Rule(message="Attribute \u201c{attr}\u201d missing quotes", structural=True)
Rule.F10 = Rule(message="Attribute \u201c{attr}\u201d using wrong quotes", structural=True)
Rule.F11 = Rule(message="{tag} contains whitespace", structural=True)
Rule.F12 = Rule(message="Long tag {tag} should be on a new line", structural=False)
Rule.F13 = Rule(message="Nonstandard whitespace in {tag}", structural=True)
Rule.F14 = Rule(message="Expected {tag} attributes on new lines", structural=True)
Rule.F15 = Rule(message="Expected {tag} attributes on a single line", structural=True)
Rule.F16 = Rule(
    message="Attribute \u201c{attr}\u201d contains its own quote character",
    structural=False,
)
Rule.F17 = Rule(message="Incorrect \u201c{attr}\u201d value formatting", structural=False)

# Encoding & language rules
Rule.E1 = Rule(message="Doctype not \u201chtml\u201d", structural=False)
Rule.E2 = Rule(message="Ampersand not represented as \u201c&amp;\u201d", structural=False)
Rule.E3 = Rule(
    message="Left angle bracket not represented as \u201c&lt;\u201d",
    structural=False,
)
Rule.E4 = Rule(
    message="Right angle bracket not represented as \u201c&gt;\u201d",
    structural=False,
)

# Plugin rules
Rule.TW1 = Rule(message="Control instruction overlaps class names", structural=True)
