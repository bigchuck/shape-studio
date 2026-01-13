# Normal Distribution Randomization - Feature Documentation

## Overview

Shape Studio's template system now supports **normal distribution** randomization alongside the existing uniform, choice, and weighted choice distributions. This enhancement allows for more organic variation in dataset generation by clustering parameter values around a mean rather than distributing them uniformly.

## Feature Summary

- **What**: Normal (Gaussian) distribution for randomization parameters
- **Why**: More natural parameter clustering for organic-looking variations
- **How**: Dictionary format with explicit mean/std specification
- **Fallback**: Rejection sampling with 1000 retry limit

## Format

### Dictionary Format

```json
{
  "type": "normal",
  "min": 0.5,
  "max": 1.5,
  "mean": 1.0,
  "std": 0.3
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Must be `"normal"` |
| `min` | number | ✅ | Minimum value (hard limit) |
| `max` | number | ✅ | Maximum value (hard limit) |
| `mean` | number | ✅ | Center of distribution |
| `std` | number | ✅ | Standard deviation (spread) |

### Behavior

- **Values cluster around `mean`**
  - ~68% within mean ± std
  - ~95% within mean ± 2×std
  - ~99.7% within mean ± 3×std

- **Hard boundaries at `min` and `max`**
  - Uses rejection sampling (regenerates if out of range)
  - Fails after 1000 retries with descriptive error

- **Integer vs Float**
  - If both `min` and `max` are integers → result is integer (rounded)
  - Otherwise → result is float

## Usage Examples

### Example 1: Subtle Variation

Most values near 1.0, occasional extremes:

```json
"randomization": {
  "projection": {
    "type": "normal",
    "min": 0.5,
    "max": 1.5,
    "mean": 1.0,
    "std": 0.3
  }
}
```

**Distribution**:
- 68% between 0.7–1.3
- 95% between 0.4–1.6 (but capped at 0.5–1.5)
- Rare values at boundaries

### Example 2: Integer Parameters

Cluster around typical iteration count:

```json
"randomization": {
  "iters": {
    "type": "normal",
    "min": 10,
    "max": 25,
    "mean": 17,
    "std": 4
  }
}
```

**Distribution**:
- 68% between 13–21
- Values are integers (10, 11, 12, ... 25)
- Most common: 16, 17, 18

### Example 3: Tight Clustering

Low variance, values stay close to mean:

```json
"randomization": {
  "depth": {
    "type": "normal",
    "min": 0.8,
    "max": 1.2,
    "mean": 1.0,
    "std": 0.1
  }
}
```

**Distribution**:
- 68% between 0.9–1.1
- 95% between 0.8–1.2 (entire range)
- Very predictable, minimal variation

### Example 4: Wide Spread

High variance, uses full range:

```json
"randomization": {
  "scale": {
    "type": "normal",
    "min": 0.3,
    "max": 1.7,
    "mean": 1.0,
    "std": 0.5
  }
}
```

**Distribution**:
- 68% between 0.5–1.5
- Full range 0.3–1.7 used regularly
- More chaotic variation

### Example 5: Skewed Distribution

Mean away from center:

```json
"randomization": {
  "bias": {
    "type": "normal",
    "min": 0.5,
    "max": 1.5,
    "mean": 1.3,
    "std": 0.2
  }
}
```

**Distribution**:
- Favors high values (1.1–1.5)
- Lower values (0.5–0.9) rare
- Asymmetric around mean

### Example 6: Mixed Distribution Types

Combine normal with uniform and weighted:

```json
"randomization": {
  "projection": {
    "type": "normal",
    "min": 0.5,
    "max": 1.5,
    "mean": 1.0,
    "std": 0.3
  },
  "iters": [10, 25],
  "operation": [
    ["split_offset", 2],
    ["sawtooth", 1]
  ]
}
```

## Choosing Parameters

### Rule of Thumb: Standard Deviation

For a range [min, max]:

- **Tight clustering**: `std = (max - min) / 10` → ~95% uses 20% of range
- **Moderate clustering**: `std = (max - min) / 6` → ~95% uses 67% of range  
- **Wide spread**: `std = (max - min) / 4` → ~95% uses full range
- **Loose bounds**: `std = (max - min) / 3` → frequent boundary hits

### Example Calculations

For `projection: [0.5, 1.5]` (range = 1.0):

| Goal | std | 68% Range | 95% Range |
|------|-----|-----------|-----------|
| Very tight | 0.1 | 0.9–1.1 | 0.8–1.2 |
| Tight | 0.15 | 0.85–1.15 | 0.7–1.3 |
| **Moderate** | **0.25** | **0.75–1.25** | **0.5–1.5** |
| Wide | 0.35 | 0.65–1.35 | 0.3–1.7 (clipped) |

For `iters: [10, 25]` (range = 15):

| Goal | std | 68% Range | 95% Range |
|------|-----|-----------|-----------|
| Very tight | 1.5 | 15–19 | 14–20 |
| Tight | 2.5 | 14–20 | 12–22 |
| **Moderate** | **4** | **13–21** | **9–25** |
| Wide | 5 | 12–22 | 7–27 (clipped) |

## Common Patterns

### Pattern 1: Centered Clustering

```json
"mean": (min + max) / 2,
"std": (max - min) / 6
```

Most values in middle third of range.

### Pattern 2: Bias Toward Maximum

```json
"mean": min + 0.75 * (max - min),
"std": (max - min) / 8
```

Favors high values with occasional low outliers.

### Pattern 3: Bias Toward Minimum

```json
"mean": min + 0.25 * (max - min),
"std": (max - min) / 8
```

Favors low values with occasional high outliers.

### Pattern 4: Full Range Coverage

```json
"mean": (min + max) / 2,
"std": (max - min) / 4
```

Uses entire range regularly, few boundary rejections.

## Comparison with Uniform Distribution

### Uniform: `[0.5, 1.5]`
- All values equally likely
- Flat distribution
- 10% chance of 0.5–0.6
- 10% chance of 1.4–1.5
- Mechanical feeling

### Normal: `{mean: 1.0, std: 0.3, min: 0.5, max: 1.5}`
- Values cluster around 1.0
- Bell curve distribution  
- ~2% chance of 0.5–0.6
- ~2% chance of 1.4–1.5
- Organic feeling

**When to use each**:
- **Uniform**: Equal exploration of parameter space
- **Normal**: Realistic variation around typical values

## Error Handling

### Rejection Sampling Failure

If generation fails after 1000 attempts:

```
ValueError: Normal distribution for 'projection' failed after 1000 attempts
Parameters: mean=1.0, std=2.0, range=[0.5, 1.5]
Consider: (1) reducing std, (2) adjusting mean closer to range center, or (3) widening the range
```

**Common causes**:
1. `std` too large relative to range
2. `mean` far outside [min, max]
3. Very narrow range with large std

**Solutions**:
1. Reduce `std` to (max - min) / 6 or smaller
2. Move `mean` closer to range center
3. Widen [min, max] range

### Invalid Parameters

```
ValueError: Normal distribution for 'iters': std (0) must be positive
ValueError: Normal distribution for 'scale': min (1.5) must be < max (0.5)
ValueError: Normal distribution for 'depth' missing required fields: mean, std
```

All validation errors are descriptive and actionable.

## BATCH Generation

### Command

```bash
BATCH 100 example_normal_distribution.json normal_example output
```

### Expected Results

With normal distribution:
- **Clustering**: Most images similar (near mean)
- **Outliers**: Few very different images (at boundaries)
- **Smooth variation**: Gradual differences between images
- **Natural appearance**: Less mechanical than uniform

With uniform distribution:
- **Spread**: All variations equally likely
- **No clustering**: Flat parameter coverage
- **Abrupt changes**: High variance between images
- **Systematic exploration**: Better for parameter search

## Implementation Details

### Rejection Sampling

1. Generate value from unbounded normal: `random.gauss(mean, std)`
2. Check if value in [min, max]
3. If yes: return value (rounded if integer type)
4. If no: retry (up to 1000 times)
5. If all fail: raise descriptive ValueError

### Why Rejection Sampling?

Alternative approaches:
- **Clipping**: `value = max(min, min(max, gauss()))` → distorts distribution (boundary spikes)
- **Truncated normal**: Requires scipy → extra dependency
- **Rejection sampling**: Simple, correct, fast enough

With reasonable parameters, rejection rate is low (<1% with properly chosen std).

## Testing

### Test 1: Basic Functionality

```bash
RUN example_normal_distribution.json normal_example
```

Should create shape without errors.

### Test 2: Batch Variation

```bash
BATCH 20 example_normal_distribution.json normal_example test
```

Visually inspect output/:
- Most images similar
- Gradual variation
- Few outliers

### Test 3: Tight Clustering

```bash
BATCH 10 example_normal_distribution.json tight_normal test_tight
```

All images should be very similar.

### Test 4: Wide Spread

```bash
BATCH 10 example_normal_distribution.json wide_normal test_wide
```

Images should vary significantly.

### Test 5: Skewed Distribution

```bash
BATCH 10 example_normal_distribution.json skewed_normal test_skewed
```

Most images should use high parameter values.

### Test 6: Mixed Distributions

```bash
BATCH 10 example_normal_distribution.json mixed_distributions test_mixed
```

Should combine normal (projection) with uniform (iters) and weighted (operation).

## Troubleshooting

### Issue: "Failed after 1000 attempts"

**Cause**: std too large, mean outside range, or narrow range

**Solution**:
1. Check: Is mean between min and max?
2. Check: Is std < (max - min) / 3?
3. Try: std = (max - min) / 6 as starting point

### Issue: All values at boundaries

**Cause**: std too large, values always rejected except at extremes

**Solution**: Reduce std significantly (divide by 2 or more)

### Issue: No variation in output

**Cause**: std too small

**Solution**: Increase std (try (max - min) / 6)

### Issue: Distribution looks uniform

**Cause**: Range too wide for std, all values accepted

**Solution**: 
- Use tighter [min, max] range
- Keep std the same

## Best Practices

1. **Start moderate**: `std = (max - min) / 6`
2. **Center the mean**: `mean = (min + max) / 2`
3. **Validate early**: Test with `RUN` before `BATCH`
4. **Inspect visually**: Generate 10-20 samples first
5. **Document choices**: Note why you picked mean/std
6. **Compare distributions**: Run same template with uniform and normal

## Future Enhancements

Possible additions:
- Truncated normal (scipy-based)
- Log-normal distribution
- Beta distribution
- Exponential distribution
- Custom PDF support

Current implementation focuses on most common use case (normal distribution) with zero dependencies.

---

## Summary

Normal distribution randomization enables:
- ✅ More organic variation
- ✅ Realistic parameter clustering
- ✅ Control over spread via std
- ✅ Mixed with existing distributions
- ✅ Explicit, readable syntax
- ✅ Graceful failure with clear errors
- ✅ Zero new dependencies

Perfect for dataset generation where you want subtle variations around typical parameter values rather than uniform exploration of the parameter space.
