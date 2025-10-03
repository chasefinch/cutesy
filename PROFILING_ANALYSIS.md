# Performance Profiling Analysis for Rust Optimization

**Date**: 2025-10-03  
**Profiling Method**: cProfile over 10 iterations of all test HTML files

## Executive Summary

Based on comprehensive profiling of the Cutesy HTML linter/formatter, the following functions are the top candidates for rewriting as Rust extensions. The profiler ran 220 lint operations (10 iterations × 22 test files) taking **0.151 seconds total**.

---

## Top Hotspots (by Total Time)

### 1. **`linter.py:488(handle_data)` - 23ms (15.2% of total time)**

**Purpose**: Processes HTML text content between tags

**Performance Characteristics**:
- Called 3,900 times (most frequently called hot function)
- Performs intensive regex operations:
  - Trailing whitespace detection/removal
  - Indentation fixing with regex substitution
  - Multiple newline collapsing
  - Horizontal whitespace normalization

**Why Rust?**:
- String manipulation dominates execution time
- Regex compilation and matching happens frequently
- Could use `regex` crate for JIT-compiled patterns
- Manual string scanning in Rust would be faster than Python regex for simple patterns

**Estimated Improvement**: 5-10x speedup

---

### 2. **`linter.py:719(goahead)` - 9ms (6.0% of total time)**

**Purpose**: Main parsing loop that consumes HTML character by character

**Performance Characteristics**:
- Called 440 times
- Heavy use of:
  - `str.startswith()` - 19,624 calls
  - Regex pattern matching - 15,473 calls
  - String slicing operations
  - Character-by-character scanning

**Why Rust?**:
- Inner loop of the parser - prime candidate for optimization
- Byte-level operations in Rust are much faster than Python string operations
- Zero-copy slicing with Rust string views
- Compiled regex patterns with lazy_static would be faster

**Estimated Improvement**: 10-20x speedup

---

### 3. **`linter.py:326(handle_starttag)` - 8ms (5.3% of total time)**

**Purpose**: Processes opening HTML tags and their attributes

**Performance Characteristics**:
- Called 2,020 times
- Triggers expensive `_make_attr_strings()` calls (6ms total)
- Heavy regex use for attribute formatting
- String concatenation and list operations

**Why Rust?**:
- Attribute processing involves many allocations
- Could use arena allocation or string pooling
- Regex operations on attributes could be optimized

**Estimated Improvement**: 5-8x speedup

---

### 4. **`linter.py:846(parse_starttag)` - 7ms (4.6% of total time)**

**Purpose**: Parses start tags using tolerant regex patterns

**Performance Characteristics**:
- Called 2,020 times
- Uses complex regex patterns (`attrfind_tolerant`, `tagfind_tolerant`)
- Many regex match/group operations (5,340 calls)

**Why Rust?**:
- Complex regex patterns compiled once and reused
- Nom parser combinator library could replace regex patterns with faster parsing
- Zero-copy parsing with string views

**Estimated Improvement**: 8-15x speedup

---

### 5. **`linter.py:44(attr_sort)` - 7ms (4.6% of total time)**

**Purpose**: Generates sort keys for HTML attributes based on priority rules

**Performance Characteristics**:
- Called 3,040 times
- Creates large tuples with ~60+ comparisons per call
- Heavy use of `str.startswith()` and `in` checks
- Called from `list.sort()` (4,260 calls taking 1ms each)

**Why Rust?**:
- Could use a hash map for O(1) attribute priority lookup instead of linear checks
- Compile-time sorting with const generics
- More efficient comparison operations

**Estimated Improvement**: 10-20x speedup

---

### 6. **Regex Operations - 15ms combined (10% of total time)**

**Components**:
- `re.compile()` / `__init__.py:330(_compile)` - 7ms (24,862 calls)
- `re.sub()` / `__init__.py:183(sub)` - 5ms (13,740 calls)
- Pattern matching - 6ms (15,473 calls)

**Why Rust?**:
- Python's `re` module has significant overhead
- Rust's `regex` crate uses JIT compilation and is faster
- Could cache compiled patterns with `once_cell` or `lazy_static`
- Many simple patterns (whitespace, newlines) could be replaced with faster byte-scanning

**Estimated Improvement**: 5-15x speedup for regex-heavy operations

---

## Secondary Optimization Targets

### 7. **`linter.py:982(_process)` - 6ms**
Simple string concatenation function called 11,160 times. Could benefit from rope data structure or string builder in Rust.

### 8. **`linter.py:1020(_make_attr_strings)` - 6ms**
Complex attribute formatting with recursive calls and whitespace handling. Good candidate for Rust optimization.

### 9. **`linter.py:934/441(parse_endtag/handle_endtag)` - 6ms combined**
End tag parsing and handling with regex validation.

---

## Module-Level Recommendations

### Core Parsing Engine (`linter.py`)

**Functions to Rewrite**:
1. `goahead()` - main parsing loop
2. `handle_data()` - text content processing
3. `parse_starttag()` - start tag parsing
4. `parse_endtag()` - end tag parsing
5. `attr_sort()` - attribute sorting logic
6. `_make_attr_strings()` - attribute formatting

**Approach**:
- Create a Rust module `cutesy_core` using PyO3
- Expose Python-compatible APIs
- Use `regex` crate for pattern matching
- Consider using `html5ever` tokenizer or custom parser

**Estimated Overall Improvement**: 10-30x faster for parsing-heavy workloads

---

### Attribute Processors

**`attribute_processors/whitespace.py`**:
- Heavy regex use (`STRING_RE`, `MIDDLE_WS_RUN`)
- String manipulation outside/inside quoted strings
- Good candidate for Rust string processing

**`attribute_processors/reindent.py`**:
- Line-by-line indentation calculation
- Regex-based whitespace stripping
- Could be optimized with Rust

**`attribute_processors/class_ordering/tailwind.py`**:
- Complex class parsing and grouping logic
- Heavy use of OrderedDict and list operations
- Regex compilation (3 patterns compiled 14 times)
- Sorting 3,040 times
- **High value target** - Tailwind class sorting is compute-intensive

---

## Concrete Implementation Strategy

### Phase 1: Core Parser (Highest ROI)
1. Rewrite `goahead()` in Rust - main parsing loop
2. Rewrite `handle_data()` - text processing
3. Rewrite `attr_sort()` - attribute ordering
4. Expose via PyO3 as `cutesy_core`

### Phase 2: Attribute Processing
1. Port whitespace normalization to Rust
2. Port class ordering (Tailwind) to Rust
3. Expose as `cutesy_attrs`

### Phase 3: Tag Processing
1. Port `parse_starttag()` and `parse_endtag()`
2. Port `_make_attr_strings()`
3. Integrate with Phase 1

---

## Technology Stack Recommendations

### Rust Crates to Use:
- **PyO3**: Python bindings (essential)
- **regex**: Fast regex engine with JIT compilation
- **once_cell** or **lazy_static**: For cached compiled regex patterns
- **nom**: Parser combinator library (alternative to regex for complex parsing)
- **smartstring** or **compact_str**: Efficient small string optimization
- **ahash**: Fast hashing for HashMap/HashSet operations
- **memchr**: Ultra-fast byte searching (for whitespace, newlines)

### Build System:
- **maturin**: Build and publish Rust-Python packages
- **setuptools-rust**: Alternative build integration

---

## Expected Performance Gains

Based on profiling data and typical Python-to-Rust conversions:

| Component | Current Time | Expected After Rust | Speedup |
|-----------|--------------|---------------------|---------|
| `handle_data()` | 23ms | 2-4ms | 6-12x |
| `goahead()` | 9ms | 0.5-1ms | 9-18x |
| `parse_starttag()` | 7ms | 0.5-1ms | 7-14x |
| `attr_sort()` | 7ms | 0.4-0.7ms | 10-18x |
| Regex operations | 15ms | 1-3ms | 5-15x |
| **Total** | **151ms** | **15-30ms** | **5-10x** |

---

## Testing Strategy

1. **Benchmark before rewrite**: Record baseline performance
2. **Port incrementally**: One function at a time with fallback to Python
3. **Validate correctness**: Run full test suite after each port
4. **Measure improvements**: Use criterion.rs for Rust benchmarks
5. **Profile again**: Identify next bottleneck after Phase 1

---

## Risks and Considerations

1. **API Compatibility**: Must maintain exact behavior for all edge cases
2. **Error Messages**: Rust panics need to be converted to Python exceptions
3. **Maintenance Burden**: Two codebases to maintain during transition
4. **Build Complexity**: Requires Rust toolchain for development/distribution
5. **PyPy Compatibility**: May lose PyPy JIT benefits for pure Python code

---

## Alternative Approaches (Lower Effort, Lower Gain)

Before committing to Rust rewrite, consider:

1. **Optimize Python**:
   - Cache compiled regex patterns at module level
   - Use `re.compile()` with raw strings
   - Replace simple regex with `str` methods where possible
   - Profile with pyinstrument for more detailed insights

2. **Use Cython**:
   - Easier to port Python code
   - Type annotations for speedup
   - Less dramatic gains than Rust (2-5x vs 5-20x)

3. **JIT with PyPy**:
   - May provide 2-5x speedup automatically
   - No code changes required
   - Test compatibility first

---

## Conclusion

The **core parsing loop** (`goahead`, `handle_data`) and **attribute sorting** (`attr_sort`) are the highest-value targets for Rust optimization, representing ~30% of total execution time. A phased approach starting with these functions would yield 5-10x overall performance improvement with manageable implementation complexity.

Recommend starting with Phase 1 (core parser) and measuring results before proceeding to attribute processors.
