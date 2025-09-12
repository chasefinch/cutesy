"""Processors for attribute strings."""

# Standard Library
from abc import ABC, abstractmethod


class BaseAttributeProcessor(ABC):
    """A base class for attribute processors."""

    @abstractmethod
    def process(
        self,
        attr_name: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        attr_body: str,
    ) -> str:
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
