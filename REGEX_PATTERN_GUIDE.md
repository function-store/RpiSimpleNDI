# Regex Pattern Matching Guide

## Overview

The NDI receiver now supports flexible pattern matching for NDI sources, adapted from the TouchDesigner NDINamedRouterExt implementation.

## Configuration Options

### Basic Options

```json
{
  "ndi": {
    "source_pattern": "_led",          // Pattern to match
    "pattern_type": "suffix",          // "suffix" or "regex"
    "enable_plural_handling": false,   // Auto-handle singular/plural
    "case_sensitive": false            // Case-sensitive matching
  }
}
```

### Pattern Types

#### 1. Suffix Matching (Default - Backwards Compatible)

```json
{
  "source_pattern": "_led",
  "pattern_type": "suffix"
}
```

**Matches:**
- ✅ `MACBOOK (output_led)`
- ✅ `STUDIO (TouchDesigner_led)`
- ❌ `LAPTOP (main_output)`

#### 2. Regex Matching (Advanced)

```json
{
  "source_pattern": ".*_led",
  "pattern_type": "regex"
}
```

**Powerful regex patterns:**

**Match any source ending with `_led`:**
```json
{
  "source_pattern": ".*_led",
  "pattern_type": "regex"
}
```

**Match TouchDesigner sources:**
```json
{
  "source_pattern": "TouchDesigner.*",
  "pattern_type": "regex"
}
```

**Match multiple suffixes:**
```json
{
  "source_pattern": ".*(led|output|main)",
  "pattern_type": "regex"
}
```

**Match specific names:**
```json
{
  "source_pattern": "(projector|screen)_[0-9]+",
  "pattern_type": "regex"
}
```

### Plural Handling

Automatically match both singular and plural forms:

```json
{
  "source_pattern": "projector",
  "pattern_type": "regex",
  "enable_plural_handling": true
}
```

**Matches:**
- ✅ `STUDIO (projector)`
- ✅ `STUDIO (projectors)`

**How it works:**
- Pattern `projector` → Transformed to `projectors?`
- Pattern `screen` → Transformed to `screens?`
- Pattern `display.*` → Not transformed (already has special chars)

### Case Sensitivity

```json
{
  "source_pattern": "LED",
  "case_sensitive": true   // Exact case match
}
```

vs

```json
{
  "source_pattern": "led",
  "case_sensitive": false  // Matches "LED", "led", "Led", etc.
}
```

## Examples

### Example 1: Studio Setup (Multiple Patterns)

```json
{
  "ndi": {
    "source_pattern": "(projector|screen)_led",
    "pattern_type": "regex",
    "case_sensitive": false
  }
}
```

**Matches:**
- ✅ `STUDIO (projector_led)`
- ✅ `STUDIO (screen_led)`
- ✅ `LAPTOP (PROJECTOR_LED)` (case-insensitive)

### Example 2: TouchDesigner Outputs

```json
{
  "ndi": {
    "source_pattern": "TouchDesigner_(out[0-9]+|main)",
    "pattern_type": "regex"
  }
}
```

**Matches:**
- ✅ `STUDIO (TouchDesigner_out1)`
- ✅ `STUDIO (TouchDesigner_out2)`
- ✅ `STUDIO (TouchDesigner_main)`

### Example 3: Any LED Source

```json
{
  "ndi": {
    "source_pattern": ".*led.*",
    "pattern_type": "regex",
    "case_sensitive": false
  }
}
```

**Matches:**
- ✅ `STUDIO (main_led_output)`
- ✅ `LAPTOP (LED_screen)`
- ✅ `SERVER (ledwall_01)`

### Example 4: Numbered Projectors with Plurals

```json
{
  "ndi": {
    "source_pattern": "projector_[0-9]+",
    "pattern_type": "regex",
    "enable_plural_handling": true
  }
}
```

**Matches:**
- ✅ `STUDIO (projector_1)`
- ✅ `STUDIO (projectors_1)` (plural handling)
- ✅ `STUDIO (projector_42)`

## NDI Source Name Format

NDI sources are formatted as: `"COMPUTERNAME (SourceName)"`

The pattern matches against **SourceName only** (the part inside parentheses).

Examples:
- Full name: `"MACBOOK (TouchDesigner_led)"`
- Pattern matches against: `TouchDesigner_led`

## Migration from Old Suffix

### Old Config (still works):
```json
{
  "ndi": {
    "source_suffix": "_led"
  }
}
```

### New Equivalent:
```json
{
  "ndi": {
    "source_pattern": "_led",
    "pattern_type": "suffix"
  }
}
```

### Upgrade to Regex:
```json
{
  "ndi": {
    "source_pattern": ".*_led",
    "pattern_type": "regex"
  }
}
```

## Testing Your Pattern

```bash
# Test with debug output
python3 ndi_receiver.py --config config.regex_example.json --debug

# List sources to see what's available
python3 list_ndi_sources.py

# Test pattern manually
python3 -c "
import re
pattern = re.compile('.*_led', re.IGNORECASE)
sources = ['TouchDesigner_led', 'main_output', 'screen_LED']
for s in sources:
    print(f'{s}: {bool(pattern.fullmatch(s))}')
"
```

## Common Patterns Cheat Sheet

| Use Case | Pattern | Type | Example Match |
|----------|---------|------|---------------|
| Any LED source | `.*led.*` | regex | `main_led_out` |
| Ends with _led | `.*_led` | regex | `output_led` |
| TouchDesigner | `TouchDesigner.*` | regex | `TouchDesigner_main` |
| Numbered outputs | `out_[0-9]+` | regex | `out_1`, `out_42` |
| Multiple suffixes | `.*(led\|output)` | regex | `main_led`, `main_output` |
| Exact names | `(proj1\|proj2)` | regex | `proj1`, `proj2` |

## Benefits

✅ **Flexible** - Match complex source naming schemes
✅ **Powerful** - Full regex support for advanced patterns
✅ **Backwards Compatible** - Old `source_suffix` still works
✅ **Case Insensitive** - Optional case-sensitive matching
✅ **Plural Handling** - Automatically match singular/plural
✅ **Proven** - Adapted from production TouchDesigner code

## Troubleshooting

**Pattern not matching?**
1. Check pattern syntax with Python regex tester
2. Enable debug logging: `--debug`
3. Verify source name format with `list_ndi_sources.py`
4. Remember: pattern matches the part inside parentheses only

**Invalid regex error?**
- Falls back to suffix matching automatically
- Check logs for error message
- Test pattern: `python3 -c "import re; re.compile('YOUR_PATTERN')"`

