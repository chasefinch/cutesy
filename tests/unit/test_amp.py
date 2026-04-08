"""Tests for the AMP attribute processor."""

from cutesy.attribute_processors.amp import AttributeProcessor

MAX_CHARS_PER_LINE = 80


class TestAmpBindingAttributes:
    """AMP binding attributes are processed as code content."""

    def test_bracket_class_binding(self) -> None:
        """[class] gets code-content processing."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="[class]",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  myState.isActive   &&   showIt  ",
        )
        assert result == "myState.isActive && showIt"
        assert errors == []

    def test_bracket_src_binding(self) -> None:
        """[src] gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="[src]",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  items[selectedIndex].url  ",
        )
        assert result == "items[selectedIndex].url"

    def test_bracket_hidden_binding(self) -> None:
        """[hidden] gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="[hidden]",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  !showElement  ",
        )
        assert result == "!showElement"

    def test_data_amp_bind_prefix(self) -> None:
        """Data-amp-bind-* gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="data-amp-bind-class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  myState.classes  ",
        )
        assert result == "myState.classes"


class TestAmpActionAttribute:
    """AMP on attribute is handled by base JS prefix."""

    def test_on_attribute_passes_through(self) -> None:
        """AMP on="" is handled by base processor, not AMP's."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="on",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="tap:lightbox1.open",
        )
        # on= passes through the AMP processor (handled by base)
        assert result == "tap:lightbox1.open"


class TestAmpLayoutAttribute:
    """AMP layout attribute gets strip processing."""

    def test_layout_stripped(self) -> None:
        """Layout attribute gets stripped."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="layout",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  responsive  ",
        )
        assert result == "responsive"
        assert errors == []


class TestAmpPassthrough:
    """Non-AMP attributes pass through unchanged."""

    def test_class_passes_through(self) -> None:
        """Class is not AMP's domain — passes through for base."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  foo   bar  ",
        )
        assert result == "  foo   bar  "

    def test_unknown_attr_left_alone(self) -> None:
        """Non-AMP attributes pass through unchanged."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="title",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="Hello   world",
        )
        assert result == "Hello   world"
