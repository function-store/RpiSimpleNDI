# Regex-Only Pattern Matching

## What Changed

We've simplified the NDI pattern matching to **only use regex**, removing the complexity of multiple pattern types.

### Before (Multiple Pattern Types):
```python
NDIHandler(
    source_suffix='_led',
    source_pattern='.*_led',
    pattern_type='suffix'  # or 'regex'
)
```

### After (Regex Only):
```python
NDIHandler(
    source_pattern='.*_led'  # Always regex
)
```

## Benefits

✅ **Simpler API** - One pattern type, not two
✅ **More Powerful** - Regex is more flexible than suffix matching
✅ **Cleaner Code** - Removed pattern_type conditionals
✅ **Easier to Understand** - One matching strategy

## Migration Guide

### Config Files

**Old:**
```json
{
  "ndi": {
    "source_suffix": "_led",
    "pattern_type": "suffix"
  }
}
```

**New:**
```json
{
  "ndi": {
    "source_pattern": ".*_led"
  }
}
```

### CLI Usage

The `--source-suffix` flag still works! It's automatically converted to a regex pattern:

```bash
# This:
python3 ndi_receiver.py --source-suffix _led

# Becomes internally:
source_pattern = ".*_led"
```

## Common Patterns

### Match sources ending with "_led"
```json
{"source_pattern": ".*_led"}
```

### Match sources starting with "TouchDesigner"
```json
{"source_pattern": "TouchDesigner.*"}
```

### Match multiple suffixes
```json
{"source_pattern": ".*(led|output|main)"}
```

### Match numbered outputs
```json
{"source_pattern": "out_[0-9]+"}
```

### Match exact names
```json
{"source_pattern": "(projector1|projector2|screen)"}
```

## Pattern Syntax

Regex patterns use Python's `re` module syntax:

- `.` - Any character
- `*` - Zero or more of previous
- `+` - One or more of previous
- `?` - Zero or one of previous
- `[0-9]` - Any digit
- `[a-z]` - Any lowercase letter
- `(a|b)` - a or b
- `^` - Start of string (not needed with fullmatch)
- `$` - End of string (not needed with fullmatch)

## Backward Compatibility

✅ **CLI Flag**: `--source-suffix _led` still works (auto-converted to `.*_led`)
✅ **Default**: If no pattern specified, defaults to `.*_led`

## Examples

### Example 1: LED Sources
```bash
# Config
{"source_pattern": ".*_led"}

# Matches:
- "STUDIO (output_led)" ✓
- "LAPTOP (TouchDesigner_led)" ✓
- "SERVER (main_output)" ✗
```

### Example 2: TouchDesigner
```bash
# Config
{"source_pattern": "TouchDesigner.*"}

# Matches:
- "STUDIO (TouchDesigner_main)" ✓
- "STUDIO (TouchDesigner_out1)" ✓
- "STUDIO (output_led)" ✗
```

### Example 3: Multiple Options
```bash
# Config
{"source_pattern": ".*(projector|screen)"}

# Matches:
- "STUDIO (main_projector)" ✓
- "LAPTOP (big_screen)" ✓
- "SERVER (output_led)" ✗
```

## Testing Your Pattern

```bash
# Test pattern matching
python3 -c "
import re
pattern = re.compile('.*_led', re.IGNORECASE)
test_sources = [
    'output_led',
    'TouchDesigner_led',
    'main_output'
]
for source in test_sources:
    matches = bool(pattern.fullmatch(source))
    print(f'{source}: {\"✓\" if matches else \"✗\"}')
"
```

## Debug Mode

Enable debug logging to see pattern matching in action:

```bash
python3 ndi_receiver.py --config config.led_screen.json --debug
```

You'll see:
```
INFO - Compiled regex pattern: '.*_led' (case_sensitive=False)
INFO - Found source matching pattern '.*_led': STUDIO (output_led)
```

## Invalid Patterns

If you provide an invalid regex pattern, the application will fail with a clear error:

```
ERROR - Invalid regex pattern '.*_led(': missing ), unterminated subpattern
ValueError: Invalid regex pattern: .*_led(
```

Fix your pattern and try again!

## Advanced Features

### Plural Handling

Still supported! Enable with `enable_plural_handling: true`:

```json
{
  "source_pattern": "projector",
  "enable_plural_handling": true
}
```

Matches both `projector` and `projectors`.

### Case Sensitivity

Control with `case_sensitive`:

```json
{
  "source_pattern": "LED",
  "case_sensitive": true  // Only matches "LED", not "led" or "Led"
}
```

Default is `false` (case-insensitive).

