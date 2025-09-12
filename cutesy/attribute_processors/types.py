"""Processors for attribute strings."""

# Standard Library
from abc import ABC, abstractmethod
from ..preprocessors import BasePreprocessor


class BaseAttributeProcessor(ABC):
    """A base class for attribute processors."""

    @abstractmethod
    def process(
        self,
        attr_name: str,
        position: (int, int),
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        preprocessor: BasePreprocessor | None,
        attr_body: str,
    ) -> str:
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
