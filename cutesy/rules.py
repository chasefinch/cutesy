"""Types to support Cutesy."""

from data_enum import DataEnum


class Rule(DataEnum):
    """A rule to lint against."""

    primary_attribute = "code"
    data_attributes = ("message", "fixable", "structural")


# Temporary preprocessing rules
Rule("T1", "Instruction not long enough to generate a placeholder", fixable=False, structural=True)

# Preprocessing rules
Rule("P1", "{tag} overlaps HTML elements or attributes", fixable=False, structural=True)
Rule("P2", "Expected {tag}", fixable=False, structural=True)  # Expected closing instruction
Rule("P3", "{tag} doesn’t have a matching opening instruction", fixable=False, structural=True)
Rule("P4", "Malformed processing instruction", fixable=False, structural=True)
Rule("P5", "Extra whitespace in {tag}", fixable=False, structural=False)
Rule("P6", "Expected padding in {tag}", fixable=False, structural=False)

# Document structure rules
Rule("D1", "Expected doctype before other HTML elements", fixable=False, structural=False)
Rule(
    "D2",
    "Second declaration found; “doctype” should be the only declaration",
    fixable=False,
    structural=False,
)
Rule("D3", "Expected {tag}", fixable=False, structural=False)  # Expected closing tag
Rule("D4", "{tag} doesn’t have a matching opening tag", fixable=False, structural=False)
Rule("D5", "Unnecessary self-closing of {tag}", fixable=True, structural=True)
Rule("D6", "Self-closing of non-void element {tag}", fixable=True, structural=True)
Rule("D7", "Malformed tag", fixable=False, structural=True)
Rule("D8", "Malformed closing tag", fixable=False, structural=True)
Rule("D9", "Expected blank line at end of document", fixable=True, structural=False)

# Formatting rules
Rule("F1", "Doctype not lowercase", fixable=True, structural=False)
Rule("F2", "Trailing whitespace", fixable=True, structural=True)
Rule("F3", "Incorrect indentation", fixable=True, structural=True)
Rule("F4", "Extra vertical whitespace", fixable=True, structural=True)
Rule("F5", "Extra horizontal whitespace", fixable=True, structural=True)
Rule("F6", "Incorrect attribute order", fixable=True, structural=False)
Rule("F7", "{tag} not lowercase", fixable=True, structural=True)
Rule("F8", "Attribute “{attr}” not lowercase", fixable=True, structural=True)
Rule("F9", "Attribute “{attr}” missing quotes", fixable=True, structural=True)
Rule("F10", "Attribute “{attr}” using wrong quotes", fixable=False, structural=True)
Rule("F11", "{tag} contains whitespace", fixable=True, structural=True)
Rule("F12", "Long tag {tag} should be on a new line", fixable=True, structural=False)
Rule("F13", "Nonstandard whitespace in {tag}", fixable=True, structural=True)
Rule("F14", "Expected {tag} attributes on new lines", fixable=True, structural=True)
Rule("F15", "Expected {tag} attributes on a single line", fixable=True, structural=True)
Rule("F16", "Attribute “{attr}” contains its own quote character", fixable=False, structural=False)
Rule("F17", "Incorrect “{attr}” value formatting", fixable=True, structural=False)

# Encoding & language rules
Rule("E1", "Doctype not “html”", fixable=False, structural=False)
Rule("E2", "Ampersand not represented as “&amp;”", fixable=False, structural=False)
Rule("E3", "Left angle bracket not represented as “&lt;”", fixable=False, structural=False)
Rule("E4", "Right angle bracket not represented as “&gt;”", fixable=False, structural=False)
