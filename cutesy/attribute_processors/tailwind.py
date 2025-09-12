"""Class sorting to accommodate the Tailwind CSS framework."""

from . import BaseAttributeProcessor


class AttributeProcessor(BaseAttributeProcessor):
    """Sort classes according to the Tailwind style."""

    def process(
        self,
        attr_name: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        attr_body: str,
    ) -> str:
        """Update the class attribute body with sorted classes."""
        return attr_body
