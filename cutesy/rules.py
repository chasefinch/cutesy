"""Types to support Cutesy."""

from data_enum import DataEnum


class Rule(DataEnum):
    """A rule to lint against."""

    primary_attribute = "code"
    data_attributes = ("message",)


# Temporary preprocessing rules
Rule("T1", "Instruction not long enough to generate a placeholder")

# Preprocessing rules
Rule("P1", "{tag} overlaps HTML elements or attributes")
Rule("P2", "Expected {tag}")  # Expected closing instruction
Rule("P3", "{tag} doesn’t have a matching opening instruction")
Rule("P4", "Malformed processing instruction")
Rule("P5", "Extra whitespace in {tag}")
Rule("P6", "Expected padding in {tag}")

# Document structure rules
Rule("D1", "Expected doctype before other HTML elements")
Rule("D2", "Second declaration found; “doctype” should be the only declaration")
Rule("D3", "Expected {tag}")  # Expected closing tag
Rule("D4", "{tag} doesn’t have a matching opening tag")
Rule("D5", "Unnecessary self-closing of {tag}")
Rule("D6", "Self-closing of non-void element {tag}")
Rule("D7", "Malformed tag")
Rule("D8", "Malformed closing tag")
Rule("D9", "Expected blank line at end of document")

# Formatting rules
Rule("F1", "Doctype not lowercase")
Rule("F2", "Trailing whitespace")
Rule("F3", "Incorrect indentation")
Rule("F4", "Extra vertical whitespace")
Rule("F5", "Extra horizontal whitespace")
Rule("F6", "Incorrect attribute order")
Rule("F7", "{tag} not lowercase")
Rule("F8", "Attribute “{attr}” not lowercase")
Rule("F9", "Attribute “{attr}” missing quotes")
Rule("F10", "Attribute “{attr}” using wrong quotes")
Rule("F11", "{tag} contains whitespace")
Rule("F12", "Long tag {tag} should be on a new line")
Rule("F13", "Nonstandard whitespace in {tag}")
Rule("F14", "Expected {tag} attributes on new lines")
Rule("F15", "Expected {tag} attributes on a single line")
Rule("F16", "Attribute “{attr}” contains its own quote character")
Rule("F17", "Incorrect “{attr}” value formatting")

# Encoding & language rules
Rule("E1", "Doctype not “html”")
Rule("E2", "Ampersand not represented as “&amp;”")
Rule("E3", "Left angle bracket not represented as “&lt;”")
Rule("E4", "Right angle bracket not represented as “&gt;”")
