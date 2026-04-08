# Cutesy Rules Reference

Cutesy is a linter and formatter for HTML that enforces consistent code style and structure. This comprehensive guide covers all rules Cutesy uses to analyze your HTML documents.

## Table of Contents

- [Understanding Rules](#understanding-rules)
- [Temporary Preprocessing Rules (T)](#temporary-preprocessing-rules-t)
- [Preprocessing Rules (P)](#preprocessing-rules-p)
- [Document Structure Rules (D)](#document-structure-rules-d)
- [Formatting Rules (F)](#formatting-rules-f)
- [Encoding & Language Rules (E)](#encoding--language-rules-e)
- [Rule Summary Table](#rule-summary-table)

---

## Understanding Rules

### Rule Categories

| Category | Description | Example Rules |
|----------|-------------|---------------|
| **T** | Temporary preprocessing (internal) | T1 |
| **P** | Template language processing | P1-P6 |
| **D** | Document structure & validity | D1-D9 |
| **F** | Formatting & style | F1-F17 |
| **E** | Encoding & HTML5 compliance | E1-E4 |

### Rule Attributes

Each rule has two key attributes:

**Fixable**
- ✅ **Yes**: Cutesy can automatically fix this issue
- 🟡 **Sometimes**: Cutesy can fix this issue in some cases
- ❌ **No**: Requires manual correction

**Structural**
- ✅ **Yes**: Critical issue that affects document validity
- ❌ **No**: Style preference that can be ignored

### Rule Behavior

- **In `--fix` mode**: All fixable rules are automatically corrected
- **Structural rules**: Cannot be ignored (with `--ignore`) in `--fix` mode

---

## Temporary Preprocessing Rules (T)

> ℹ️ **Note**: These are internal rules used during template processing. You typically won't encounter them directly.

<details>
<summary><strong>T1: Instruction not long enough to generate a placeholder</strong></summary>

**Fixable:** No | **Structural:** No

Internal rule used when template instructions are too short for processing placeholders.

</details>

---

## Preprocessing Rules (P)

> 🎯 **When you'll see these**: Using template languages like Django templates with `--extras=django`

<details>
<summary><strong>P1: Template instruction overlaps HTML elements</strong></summary>

**Fixable:** No | **Structural:** Yes

Template syntax interferes with HTML parsing.

**❌ Problem:**
```html
<div{% if x %} class='test'{% endif %}>
```

**💡 Solution:** Restructure template logic outside of HTML tags.

</details>

<details>
<summary><strong>P2: Missing closing template instruction</strong></summary>

**Fixable:** No | **Structural:** Yes

Template block not properly closed.

**❌ Problem:**
```html
{% if condition %}
<p>content</p>
<!-- Missing {% endif %} -->
```

**✅ Solution:**
```html
{% if condition %}
<p>content</p>
{% endif %}
```

</details>

<details>
<summary><strong>P3: Unmatched closing template instruction</strong></summary>

**Fixable:** No | **Structural:** Yes

Closing template instruction without matching opener.

**❌ Problem:**
```html
<p>content</p>
{% endif %}  <!-- No matching {% if %} -->
```

</details>

<details>
<summary><strong>P4: Malformed template instruction</strong></summary>

**Fixable:** No | **Structural:** Yes

Invalid template syntax.

**❌ Problem:**
```html
{% %}  <!-- Empty instruction -->
```

</details>

<details>
<summary><strong>P5: Extra whitespace in template instruction</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
{%  if  condition  %}
```

**✅ Fixed:**
```html
{% if condition %}
```

</details>

<details>
<summary><strong>P6: Missing padding in template instruction</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
{%if condition%}
```

**✅ Fixed:**
```html
{% if condition %}
```

</details>

---

## Document Structure Rules (D)

> 🎯 **When you'll see these**: Document structure and HTML validity issues

<details>
<summary><strong>D1: Doctype must come first</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<html></html>
<!doctype html>  <!-- Should be first -->
```

**✅ Solution:** Move doctype to the beginning of the document.

</details>

<details>
<summary><strong>D2: Multiple doctype declarations</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<!doctype html>
<!doctype html>  <!-- Duplicate -->
```

</details>

<details>
<summary><strong>D3: Missing closing tag</strong></summary>

**Fixable:** No | **Structural:** No

Improper tag nesting or missing closing tags.

**❌ Problem:**
```html
<div><span><p>content</p></div></span>  <!-- Wrong order -->
```

</details>

<details>
<summary><strong>D4: Unmatched closing tag</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<p>content</p></div>  <!-- No opening <div> -->
```

</details>

<details>
<summary><strong>D5: Unnecessary self-closing syntax</strong></summary>

**Fixable:** Yes | **Structural:** Yes

Void elements don't need self-closing syntax in HTML5.

**❌ Problem:**
```html
<br/> <img src="..."/>
```

**✅ Fixed:**
```html
<br> <img src="...">
```

</details>

<details>
<summary><strong>D6: Invalid self-closing of non-void element</strong></summary>

**Fixable:** Yes | **Structural:** Yes

**❌ Problem:**
```html
<div/>  <!-- div needs closing tag -->
```

**✅ Fixed:**
```html
<div></div>
```

</details>

<details>
<summary><strong>D7: Malformed opening tag</strong></summary>

**Fixable:** No | **Structural:** Yes

**❌ Problem:**
```html
<div class="test>content</div>  <!-- Unclosed quote -->
```

</details>

<details>
<summary><strong>D8: Malformed closing tag</strong></summary>

**Fixable:** No | **Structural:** Yes

**❌ Problem:**
```html
<div>content</div body>  <!-- Invalid syntax -->
```

</details>

<details>
<summary><strong>D9: Missing final newline</strong></summary>

**Fixable:** Yes | **Structural:** No

Files should end with a newline character.

**❌ Problem:**
```html
<!doctype html>
<html><body></body></html>
```

**✅ Fixed:**
```html
<!doctype html>
<html><body></body></html>

```

</details>

---

## Formatting Rules (F)

> 🎯 **When you'll see these**: Code style and formatting issues

### Basic Formatting

<details>
<summary><strong>F1: Doctype should be lowercase</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<!DOCTYPE HTML>
```

**✅ Fixed:**
```html
<!doctype html>
```

</details>

<details>
<summary><strong>F2: Trailing whitespace</strong></summary>

**Fixable:** Yes | **Structural:** Yes

Lines shouldn't end with spaces or tabs.

**❌ Problem:**
```html
<div>content
</div>
```

**✅ Fixed:**
```html
<div>content
</div>
```

</details>

<details>
<summary><strong>F3: Incorrect indentation</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div>
  <p>Wrong indentation</p>
</div>
```

**✅ Fixed:**
```html
<div>
    <p>Correct indentation</p>
</div>
```

</details>

<details>
<summary><strong>F4: Too much vertical whitespace</strong></summary>

**Fixable:** Yes | **Structural:** No

Maximum one blank line between elements.

**❌ Problem:**
```html
<div>



<p>Too many blank lines above</p>
</div>
```

**✅ Fixed:**
```html
<div>

<p>One blank line maximum</p>
</div>
```

</details>

<details>
<summary><strong>F5: Too much horizontal whitespace</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div>text  with    extra   spaces</div>
```

**✅ Fixed:**
```html
<div>text with extra spaces</div>
```

</details>

### Tag and Attribute Formatting

<details>
<summary><strong>F6: Incorrect attribute order</strong></summary>

**Fixable:** Yes | **Structural:** No

Attributes should follow a consistent order.

**❌ Problem:**
```html
<div style="color: red" id="main" class="test">
```

**✅ Fixed:**
```html
<div id="main" class="test" style="color: red">
```

</details>

<details>
<summary><strong>F7: Tag names should use correct casing</strong></summary>

**Fixable:** Yes | **Structural:** No

In HTML, tag names should be lowercase. In foreign content (SVG and MathML), tag names should use their spec-correct casing (which may include camelCase).

**❌ Problem (HTML):**
```html
<DIV><P>Content</P></DIV>
```

**✅ Fixed:**
```html
<div><p>Content</p></div>
```

**❌ Problem (SVG):**
```html
<svg><clippath id="a"><rect></rect></clippath></svg>
```

**✅ Fixed:**
```html
<svg><clipPath id="a"><rect></rect></clipPath></svg>
```

</details>

<details>
<summary><strong>F8: Attribute names should use correct casing</strong></summary>

**Fixable:** Yes | **Structural:** No

In HTML, attribute names should be lowercase. In foreign content (SVG and MathML), attribute names should use their spec-correct casing.

**❌ Problem (HTML):**
```html
<div CLASS="test" ID="main">
```

**✅ Fixed:**
```html
<div class="test" id="main">
```

**❌ Problem (SVG):**
```html
<svg viewbox="0 0 100 100">
```

**✅ Fixed:**
```html
<svg viewBox="0 0 100 100">
```

</details>

<details>
<summary><strong>F9: Attribute values need quotes</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div class=test id=main>
```

**✅ Fixed:**
```html
<div class="test" id="main">
```

</details>

<details>
<summary><strong>F10: Attribute using wrong quote type</strong></summary>

**Fixable:** No | **Structural:** Yes

**❌ Problem:**
```html
<div title='He said "hello"'>
```

**✅ Correct:**
```html
<div title="He said 'hello'">
```

</details>

### Tag Structure and Spacing

<details>
<summary><strong>F11: Tag contains extra whitespace</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div ></div >
```

**✅ Fixed:**
```html
<div></div>
```

</details>

<details>
<summary><strong>F12: Long tag should start on new line</strong></summary>

**Fixable:** Yes | **Structural:** No

Tags with many attributes should start on a new line.

**❌ Problem:**
```html
<p>text</p><div attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5">
```

**✅ Fixed:**
```html
<p>text</p>
<div attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5">
```

</details>

<details>
<summary><strong>F13: Non-standard whitespace in tag</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div	class="test"  id="main">  <!-- Tab and multiple spaces -->
```

**✅ Fixed:**
```html
<div class="test" id="main">
```

</details>

### Attribute Line Wrapping

<details>
<summary><strong>F14: Long attributes should wrap to new lines</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div>
    <span attr1="value1" attr2="value2" attr3="value3" attr4="value4" attr5="value5" attr6="value6">
</div>
```

**✅ Fixed:**
```html
<div>
    <span
        attr1="value1"
        attr2="value2"
        attr3="value3"
        attr4="value4"
        attr5="value5"
        attr6="value6"
    >
</div>
```

</details>

<details>
<summary><strong>F15: Short attributes should stay on one line</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div
    id="test"
    class="small"
>content</div>
```

**✅ Fixed:**
```html
<div id="test" class="small">content</div>
```

</details>

### Attribute Value Formatting

<details>
<summary><strong>F16: Attribute contains unescaped quotes</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<div title="Say "hello" world">
```

**✅ Fixed:**
```html
<div title="Say &quot;hello&quot; world">
```

</details>

<details>
<summary><strong>F17: Attribute value formatting</strong></summary>

**Fixable:** Yes | **Structural:** No

**❌ Problem:**
```html
<div class="  test   class  ">
```

**✅ Fixed:**
```html
<div class="test class">
```

</details>

---

## Encoding & Language Rules (E)

> 🎯 **When you'll see these**: HTML5 compliance and character encoding issues

<details>
<summary><strong>E1: Non-HTML5 doctype</strong></summary>

**Fixable:** No | **Structural:** No

Only HTML5 doctype is supported.

**❌ Problem:**
```html
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
<!doctype html5>
<!doctype HTML>
```

**✅ Correct:**
```html
<!doctype html>
```

</details>

<details>
<summary><strong>E2: Unescaped ampersand</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<div>Tom & Jerry</div>
<div>Johnson & Johnson</div>
```

**✅ Fixed:**
```html
<div>Tom &amp; Jerry</div>
<div>Johnson &amp; Johnson</div>
```

</details>

<details>
<summary><strong>E3: Unescaped left angle bracket</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<div>5 < 10 is true</div>
```

**✅ Should be:**
```html
<div>5 &lt; 10 is true</div>
```

</details>

<details>
<summary><strong>E4: Unescaped right angle bracket</strong></summary>

**Fixable:** No | **Structural:** No

**❌ Problem:**
```html
<div>10 > 5 is true</div>
```

**✅ Should be:**
```html
<div>10 &gt; 5 is true</div>
```

</details>

---

## Rule Summary Table

| Rule | Name | Fixable | Structural | Category |
|------|------|---------|------------|----------|
| T1 | Instruction placeholder too short | ❌ | ✅ | Internal |
| P1 | Template overlaps HTML | ❌ | ✅ | Template |
| P2 | Missing closing template instruction | ❌ | ✅ | Template |
| P3 | Unmatched closing template instruction | ❌ | ✅ | Template |
| P4 | Malformed template instruction | ❌ | ✅ | Template |
| P5 | Extra whitespace in template | ❌ | ❌ | Template |
| P6 | Missing template padding | ❌ | ❌ | Template |
| D1 | Doctype must come first | ❌ | ❌ | Structure |
| D2 | Multiple doctype declarations | ❌ | ❌ | Structure |
| D3 | Missing closing tag | ❌ | ❌ | Structure |
| D4 | Unmatched closing tag | ❌ | ❌ | Structure |
| D5 | Unnecessary self-closing | ✅ | ✅ | Structure |
| D6 | Invalid self-closing | ✅ | ✅ | Structure |
| D7 | Malformed opening tag | ❌ | ❌ | Structure |
| D8 | Malformed closing tag | ❌ | ❌ | Structure |
| D9 | Missing final newline | ✅ | ❌ | Structure |
| F1 | Doctype case | ✅ | ❌ | Format |
| F2 | Trailing whitespace | ✅ | ✅ | Format |
| F3 | Incorrect indentation | ✅ | ✅ | Format |
| F4 | Extra vertical whitespace | ✅ | ✅ | Format |
| F5 | Extra horizontal whitespace | ✅ | ✅ | Format |
| F6 | Attribute order | ✅ | ❌ | Format |
| F7 | Tag name casing | ✅ | ✅ | Format |
| F8 | Attribute name casing | ✅ | ✅ | Format |
| F9 | Missing attribute quotes | ✅ | ✅ | Format |
| F10 | Wrong quote type | ❌ | ✅ | Format |
| F11 | Tag whitespace | ✅ | ✅ | Format |
| F12 | Long tag line break | ✅ | ❌ | Format |
| F13 | Non-standard tag whitespace | ✅ | ✅ | Format |
| F14 | Attributes need wrapping | ✅ | ✅ | Format |
| F15 | Attributes should not wrap | ✅ | ✅ | Format |
| F16 | Unescaped quotes in attributes | ❌ | ❌ | Format |
| F17 | Attribute value formatting | ✅ | ❌ | Format |
| E1 | Non-HTML5 doctype | ❌ | ❌ | Encoding |
| E2 | Unescaped ampersand | ❌ | ❌ | Encoding |
| E3 | Unescaped left angle bracket | ❌ | ❌ | Encoding |
| E4 | Unescaped right angle bracket | ❌ | ❌ | Encoding |
| TW1 | Control instruction overlaps class names | X | X | TailwindCSS |

---

## Using This Reference

### For Developers
1. **See an error code?** Use the table above to jump to the specific rule
2. **Want to ignore a rule?** Use `--ignore=RULE_CODE` (e.g., `--ignore=F1`)
3. **Structural issues?** These need manual fixing - Cutesy can't auto-fix them
4. **Template issues?** Make sure you're using `--extras=django` for Django templates

---

*This reference covers all rules in Cutesy. For installation and configuration help, see [installation.md](installation.md) and [configuration.md](configuration.md).*
