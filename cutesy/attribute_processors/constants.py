"""Constants related to attribute processing."""

TOKEN_ATTRIBUTES = frozenset(
    {
        "class",
        "rel",
        "accept",
        "accept-charset",
        "headers",
        "sandbox",
        "sizes",
        "slot",
        "allow",
        "aria-describedby",
        "aria-labelledby",
    },
)


NUMERIC_ATTRIBUTES = frozenset(
    {
        "width",
        "height",
        "rowspan",
        "colspan",
        "tabindex",
        "maxlength",
        "size",
        "min",
        "max",
        "step",
    },
)  # Also "value" when on an input of type number


ENUMERATED_ATTRIBUTES = frozenset(
    {"type", "kind", "scope", "wrap", "method", "shape", "crossorigin", "preload"},
)


PRESENCE_ATTRIBUTES = frozenset(
    {
        "disabled",
        "checked",
        "required",
        "readonly",
        "hidden",
        "multiple",
        "autofocus",
        "selected",
        "novalidate",
        "async",
        "defer",
    },
)


URI_ATTRIBUTES = frozenset(
    {
        "href",
        "src",
        "action",
        "formaction",
        "poster",
        "manifest",
        "background",
        "usemap",
        "longdesc",
    },
)

JS_ATTRIBUTE_PREFIXES = frozenset({"on"})
