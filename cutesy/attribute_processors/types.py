"""Processors for attribute strings."""

# Standard Library
from abc import ABC, abstractmethod
from typing import Literal


class BaseAttributeProcessor(ABC):
    """A base class for attribute processors."""

    @abstractmethod
    def process(
        self,
        attr_name: str,
        indentation: str,
        bounding_character: Literal["'", '"'],
        attr_body: str,
    ) -> str:
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
