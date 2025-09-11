"""Class sorting to accommodate the Tailwind CSS framework."""

from typing import Literal

from . import BaseAttributeProcessor


class AttributeProcessor(BaseAttributeProcessor):
    """Sort classes according to the Tailwind style."""

    def process(
        self,
        attr_name: str,
        indentation: str,
        bounding_character: Literal["'", '"'],
        attr_body: str,
    ) -> str:
        """Update the class attribute body with sorted classes."""
        print(attr_body)
        return attr_body
