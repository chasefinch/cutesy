# Cutesy Rules Reference

Cutesy is a linter and formatter for HTML that enforces consistent code style and structure. It analyzes your HTML documents and applies a comprehensive set of rules to ensure clean, maintainable code. Rules are organized into categories based on their purpose, and each rule has a unique code for easy identification in error reports.

This document provides a complete reference of all Cutesy rules, their purpose, and examples of code that would trigger each rule.

## Rule Categories

- **T-rules**: Temporary preprocessing rules (internal)
- **P-rules**: Preprocessing rules for dynamic template languages (Django, etc.)
- **D-rules**: Document structure rules
- **F-rules**: Formatting and style rules
- **E-rules**: Encoding and language rules

## Rule Attributes

Each rule has two important attributes that determine how it behaves:

### Fixable
- **Yes**: Rule violations can be automatically corrected by Cutesy
- **No**: Rule violations require manual intervention to resolve

### Structural
- **Yes**: Rule must be fixed when in `--fix` mode
- **No**: Rule addresses optional style or formatting preferences

---

## Temporary Preprocessing Rules (T)

### T1: Instruction not long enough to generate a placeholder
**Fixable:** No
**Structural:** Yes

*Internal rule used during template preprocessing*

This rule is used internally by the preprocessor when dynamic template instructions are too short to generate proper placeholders.

---

## Preprocessing Rules (P)

These rules apply to dynamic template languages like Django templates that mix HTML with template syntax.

### P1: {tag} overlaps HTML elements or attributes
**Fixable:** No
**Structural:** Yes

Template instructions that interfere with HTML tag parsing.

**Example:**
```html
<div{% if x %} class='test'{% endif %}>
```

### P2: Expected {tag}
**Fixable:** No
**Structural:** Yes

Missing closing template instruction.

**Example:**
```html
{% if condition %}
<p>content</p>
<!-- Missing {% endif %} -->
```

### P3: {tag} doesn't have a matching opening instruction
**Fixable:** No
**Structural:** Yes

Closing template instruction without matching opening instruction.

**Example:**
```html
<p>content</p>
{% endif %}  <!-- No matching {% if %} -->
```

### P4: Malformed processing instruction
**Fixable:** No
**Structural:** Yes

Template instruction with invalid syntax.

**Example:**
```html
{% %}  <!-- Empty instruction -->
```

### P5: Extra whitespace in {tag}
**Fixable:** Yes
**Structural:** No

Template instruction contains unnecessary whitespace.

**Example:**
```html
{%  if  condition  %}  <!-- Extra spaces -->
```

**Fixed:**
```html
{% if condition %}
```

### P6: Expected padding in {tag}
**Fixable:** Yes
**Structural:** No

Template instruction missing required padding spaces.

**Example:**
```html
{%if condition%}  <!-- Missing spaces -->
```

**Fixed:**
```html
{% if condition %}
```

---

## Document Structure Rules (D)

These rules ensure proper HTML document structure and valid tag nesting.

### D1: Expected doctype before other HTML elements
**Fixable:** No
**Structural:** Yes

HTML elements appear before the doctype declaration.

**Example:**
```html
<html></html>
<!doctype html>  <!-- Doctype should come first -->
```

### D2: Second declaration found; "doctype" should be the only declaration
**Fixable:** No
**Structural:** Yes

Multiple doctype declarations in a single document.

**Example:**
```html
<!doctype html>
<!doctype html>  <!-- Duplicate doctype -->
```

### D3: Expected {tag}
**Fixable:** No
**Structural:** Yes

Missing closing tag due to improper nesting.

**Example:**
```html
<div><span><p>content</p></div></span>  <!-- Wrong closing order -->
```

### D4: {tag} doesn't have a matching opening tag
**Fixable:** No
**Structural:** Yes

Closing tag without corresponding opening tag.

**Example:**
```html
<p>content</p></div>  <!-- No opening <div> -->
```

### D5: Unnecessary self-closing of {tag}
**Fixable:** Yes
**Structural:** Yes

Void elements don't need explicit self-closing syntax.

**Example:**
```html
<br/>  <!-- Unnecessary / -->
```

**Fixed:**
```html
<br>
```

### D6: Self-closing of non-void element {tag}
**Fixable:** Yes
**Structural:** Yes

Non-void elements should not be self-closed.

**Example:**
```html
<div/>  <!-- div is not a void element -->
```

**Fixed:**
```html
<div></div>
```

### D7: Malformed tag
**Fixable:** No
**Structural:** Yes

Tag with invalid syntax.

**Example:**
```html
<div class="test>content</div>  <!-- Unclosed quote -->
```

### D8: Malformed closing tag
**Fixable:** No
**Structural:** Yes

Closing tag with invalid syntax.

**Example:**
```html
<div>content</div body>  <!-- Invalid closing tag -->
```

### D9: Expected blank line at end of document
**Fixable:** Yes
**Structural:** No

HTML documents should end with a newline.

**Example:**
```html
<!doctype html>
<html><body></body></html>  <!-- Missing final newline -->
```

**Fixed:**
```html
<!doctype html>
<html><body></body></html>
```

---

## Formatting Rules (F)

These rules enforce consistent formatting and style conventions.

### F1: Doctype not lowercase
**Fixable:** Yes
**Structural:** No

Doctype declaration should be lowercase.

**Example:**
```html
<!DOCTYPE HTML>  <!-- Uppercase -->
```

**Fixed:**
```html
<!doctype html>
```

### F2: Trailing whitespace
**Fixable:** Yes
**Structural:** No

Lines should not end with whitespace characters.

**Example:**
```html
<div>  ⎵⎵
</div>
```

**Fixed:**
```html
<div>
</div>
```

### F3: Incorrect indentation
**Fixable:** Yes
**Structural:** No

Elements should be properly indented.

**Example:**
```html
<div>
  <p></p>  <!-- Wrong indentation (spaces instead of tabs) -->
</div>
```

**Fixed:**
```html
<div>
	<p></p>
</div>
```

### F4: Extra vertical whitespace
**Fixable:** Yes
**Structural:** No

No more than one blank line between elements.

**Example:**
```html
<div>


<p></p>  <!-- Too many blank lines -->
</div>
```

**Fixed:**
```html
<div>

<p></p>
</div>
```

### F5: Extra horizontal whitespace
**Fixable:** Yes
**Structural:** No

Multiple consecutive spaces should be collapsed.

**Example:**
```html
<div>text  with  extra  spaces</div>  <!-- Multiple spaces -->
```

**Fixed:**
```html
<div>text with extra spaces</div>
```

### F6: Incorrect attribute order
**Fixable:** Yes
**Structural:** No

Attributes should follow a consistent ordering convention.

**Example:**
```html
<div style="color: red" id="main" class="test"></div>  <!-- Wrong order -->
```

**Fixed:**
```html
<div id="main" class="test" style="color: red"></div>
```

### F7: {tag} not lowercase
**Fixable:** Yes
**Structural:** No

HTML tags should be lowercase.

**Example:**
```html
<DIV><P></P></DIV>  <!-- Uppercase tags -->
```

**Fixed:**
```html
<div><p></p></div>
```

### F8: Attribute "{attr}" not lowercase
**Fixable:** Yes
**Structural:** No

Attribute names should be lowercase.

**Example:**
```html
<div CLASS="test"></div>  <!-- Uppercase attribute -->
```

**Fixed:**
```html
<div class="test"></div>
```

### F9: Attribute "{attr}" missing quotes
**Fixable:** Yes
**Structural:** No

Attribute values should be quoted.

**Example:**
```html
<div class=test></div>  <!-- Unquoted value -->
```

**Fixed:**
```html
<div class="test"></div>
```

### F10: Attribute "{attr}" using wrong quotes
**Fixable:** Yes
**Structural:** No

Attributes containing double quotes should use single quotes.

**Example:**
```html
<div title='He said "hello"'></div>  <!-- Should use double quotes -->
```

**Fixed:**
```html
<div title="He said &quot;hello&quot;"></div>
```

### F11: {tag} contains whitespace
**Fixable:** Yes
**Structural:** No

Tags should not contain internal whitespace.

**Example:**
```html
<div></div >  <!-- Space before closing bracket -->
```

**Fixed:**
```html
<div></div>
```

### F12: Long tag {tag} should be on a new line
**Fixable:** Yes
**Structural:** No

Tags with many attributes should start on a new line.

**Example:**
```html
<p>text</p><div attr0="value0" attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5" attr6="value6" attr7="value7" attr8="value8" attr9="value9">content</div>
```

**Fixed:**
```html
<p>text</p>
<div attr0="value0" attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5" attr6="value6" attr7="value7" attr8="value8" attr9="value9">content</div>
```

### F13: Nonstandard whitespace in {tag}
**Fixable:** Yes
**Structural:** No

Tags should use standard spaces between attributes.

**Example:**
```html
<div	class="test"  id="main"></div>  <!-- Tab and multiple spaces -->
```

**Fixed:**
```html
<div class="test" id="main"></div>
```

### F14: Expected {tag} attributes on new lines
**Fixable:** Yes
**Structural:** No

Long tags should have attributes wrapped to new lines.

**Example:**
```html
<div>
	<span attr0="value0" attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5" attr6="value6" attr7="value7" attr8="value8" attr9="value9">content</span>
</div>
```

**Fixed:**
```html
<div>
	<span
		attr0="value0"
		attr1="value1"
		attr2="value2"
		attr3="value3"
		attr4="value4"
		attr5="value5"
		attr6="value6"
		attr7="value7"
		attr8="value8"
		attr9="value9"
	>content</span>
</div>
```

### F15: Expected {tag} attributes on a single line
**Fixable:** Yes
**Structural:** No

Short tags with few attributes should be on a single line.

**Example:**
```html
<div
	id="test"
	class="small"
>content</div>  <!-- Should be on one line -->
```

**Fixed:**
```html
<div id="test" class="small">content</div>
```

### F16: Attribute "{attr}" contains its own quote character
**Fixable:** Yes
**Structural:** No

Attribute values should not contain raw quote characters that match the bounding quotes.

**Example:**
```html
<div title="Say "hello" world">content</div>  <!-- Raw quotes inside -->
```

**Fixed:**
```html
<div title="Say &quot;hello&quot; world">content</div>
```

### F17: Incorrect "{attr}" value formatting
**Fixable:** Yes
**Structural:** No

Attribute values should be properly formatted with correct whitespace.

**Example:**
```html
<div class="  test  class  ">content</div>  <!-- Extra whitespace -->
```

**Fixed:**
```html
<div class="test class">content</div>
```

---

## Encoding & Language Rules (E)

These rules ensure proper HTML5 compliance and character encoding.

### E1: Doctype not "html"
**Fixable:** No
**Structural:** Yes

Doctype should be the standard HTML5 doctype.

**Example:**
```html
<!doctype html5>  <!-- Should be just "html" -->
```

### E2: Ampersand not represented as "&amp;"
**Fixable:** Yes
**Structural:** No

Ampersands in text content should be properly escaped.

**Example:**
```html
<div>Tom & Jerry</div>  <!-- Unescaped ampersand -->
```

**Fixed:**
```html
<div>Tom &amp; Jerry</div>
```

### E3: Left angle bracket not represented as "&lt;"
**Fixable:** No
**Structural:** Yes

Left angle brackets in text content should be escaped.

**Example:**
```html
<div>5 < 10</div>  <!-- Unescaped < -->
```

**Should be:**
```html
<div>5 &lt; 10</div>
```

### E4: Right angle bracket not represented as "&gt;"
**Fixable:** No
**Structural:** Yes

Right angle brackets in text content should be escaped.

**Example:**
```html
<div>10 > 5</div>  <!-- Unescaped > -->
```

**Should be:**
```html
<div>10 &gt; 5</div>
```

---

## Rule Reference Summary

This document describes Cutesy's comprehensive rule system. Each rule is designed to enforce consistent, valid HTML while providing clear feedback about issues in your code.

### Understanding Rule Attributes

When Cutesy reports rule violations, understanding the rule's **Fixable** and **Structural** attributes helps you understand:

- **Whether the issue can be automatically resolved** (Fixable vs Nonfixable)
- **How critical the issue is** (Structural vs Nonstructural)
- **How the rule behaves in different modes** (check vs fix mode)

Structural rules that are nonfixable represent serious document validity issues that require careful manual correction. Nonstructural rules typically address code style and maintainability concerns.

Use the `--fix` flag to automatically resolve all fixable rule violations while reviewing nonfixable issues manually.
