"""Types to support Cutesy."""

from data_enum import DataEnum


class Rule(DataEnum):
    """A rule to lint against."""

    primary_attribute = "code"
    data_attributes = ("message", "structural")


# Temporary preprocessing rules
Rule("T1", "Instruction not long enough to generate a placeholder", structural=True)

# Preprocessing rules
Rule("P1", "{tag} overlaps HTML elements or attributes", structural=True)
Rule("P2", "Expected {tag}", structural=True)  # Expected closing instruction
Rule("P3", "{tag} doesn’t have a matching opening instruction", structural=True)
Rule("P4", "Malformed processing instruction", structural=True)
Rule("P5", "Extra whitespace in {tag}", structural=False)
Rule("P6", "Expected padding in {tag}", structural=False)

# Document structure rules
Rule("D1", "Expected doctype before other HTML elements", structural=False)
Rule(
    "D2",
    "Second declaration found; “doctype” should be the only declaration",
    structural=False,
)
Rule("D3", "Expected {tag}", structural=False)  # Expected closing tag
Rule("D4", "{tag} doesn’t have a matching opening tag", structural=False)
Rule("D5", "Unnecessary self-closing of {tag}", structural=True)
Rule("D6", "Self-closing of non-void element {tag}", structural=True)
Rule("D7", "Malformed tag", structural=False)
Rule("D8", "Malformed closing tag", structural=False)
Rule("D9", "Expected blank line at end of document", structural=False)

# Formatting rules
Rule("F1", "Doctype not lowercase", structural=False)
Rule("F2", "Trailing whitespace", structural=True)
Rule("F3", "Incorrect indentation", structural=True)
Rule("F4", "Extra vertical whitespace", structural=True)
Rule("F5", "Extra horizontal whitespace", structural=True)
Rule("F6", "Incorrect attribute order", structural=False)
Rule("F7", "{tag} not lowercase", structural=True)
Rule("F8", "Attribute “{attr}” not lowercase", structural=True)
Rule("F9", "Attribute “{attr}” missing quotes", structural=True)
Rule("F10", "Attribute “{attr}” using wrong quotes", structural=True)
Rule("F11", "{tag} contains whitespace", structural=True)
Rule("F12", "Long tag {tag} should be on a new line", structural=False)
Rule("F13", "Nonstandard whitespace in {tag}", structural=True)
Rule("F14", "Expected {tag} attributes on new lines", structural=True)
Rule("F15", "Expected {tag} attributes on a single line", structural=True)
Rule("F16", "Attribute “{attr}” contains its own quote character", structural=False)
Rule("F17", "Incorrect “{attr}” value formatting", structural=False)

# Encoding & language rules
Rule("E1", "Doctype not “html”", structural=False)
Rule("E2", "Ampersand not represented as “&amp;”", structural=False)
Rule("E3", "Left angle bracket not represented as “&lt;”", structural=False)
Rule("E4", "Right angle bracket not represented as “&gt;”", structural=False)
