"""Processors for attribute strings."""

from abc import ABC, abstractmethod

from ..preprocessors import BasePreprocessor
from ..types import Error


class BaseAttributeProcessor(ABC):
    """A base class for attribute processors."""

    position: tuple[int, int]

    @abstractmethod
    def process(
        self,
        attr_name: str,
        position: tuple[int, int],
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        max_chars_per_line: int,
        max_items_per_line: int,
        bounding_character: str,
        preprocessor: BasePreprocessor | None,
        attr_body: str,
    ) -> tuple[str, list[Error]]:
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
