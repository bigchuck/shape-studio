# Phase 2 Testing Guide

## Test Environment Setup

### Prerequisites
- Phase 2 executor modifications applied
- Example JSON files copied to `scripts/` directory
- Shape Studio running

### Test Files
- `structured_commands.json` - Basic tests
- `all_shapes_structured.json` - Command coverage
- `datasets_phase2.json` - Real-world usage
- `phase2_edge_cases.json` - Edge case testing

---

## Test Categories

### 1. Basic Functionality Tests

#### Test 1.1: Phase 1 Backward Compatibility
**Command:**
```bash
RUN structured_commands.json all_string_still_works
```

**Expected:**
- Section executes successfully
- Shape created on WIP
- No errors about format

**Validates:** Phase 1 files work unchanged

---

#### Test 1.2: Simple Structured Command
**Command:**
```bash
RUN structured_commands.json flexible_types_demo
```

**Expected:**
- PROC command executes
- Arrays converted to strings
- Numbers converted to strings
- Shape appears on WIP

**Validates:** Basic structured format works

---

#### Test 1.3: Mixed Format in Same Section
**Command:**
```bash
RUN structured_commands.json mixed_format_workflow
```

**Expected:**
- Both structured and string commands execute
- Background and foreground shapes created
- Z-ordering applied correctly
- No format conflicts

**Validates:** Mixed string/dict commands work together

---

### 2. Parameter Type Conversion Tests

#### Test 2.1: Array to String Conversion
**Create test file `test_arrays.json`:**
```json
{
  "array_test": {
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {
          "VERTICES": [5, 8],
          "BOUNDS": [100, 100, 600, 600],
          "DEPTH_RANGE": [0.3, 0.7]
        }
      }
    ]
  }
}
```

**Command:**
```bash
RUN test_arrays.json array_test
```

**Expected:**
- [5, 8] becomes "5,8"
- [100, 100, 600, 600] becomes "100,100,600,600"
- Shape created successfully

**Validates:** Array conversion

---

#### Test 2.2: Number to String Conversion
**Create test file `test_numbers.json`:**
```json
{
  "number_test": {
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {
          "VERTICES": 7,
          "BOUNDS": "100,100,600,600",
          "ITERATIONS": 15
        }
      },
      {
        "command": "WIDTH",
        "name": "test",
        "width": 3
      },
      {
        "command": "ALPHA",
        "name": "test",
        "alpha": 0.5
      }
    ]
  }
}
```

**Expected:**
- Integer 7 becomes "7"
- Integer 15 becomes "15"
- Integer 3 becomes "3"
- Float 0.5 becomes "0.5"

**Validates:** Number conversion

---

### 3. RAND() Functionality Tests

#### Test 3.1: RAND() in Structured Format
**Command:**
```bash
RUN structured_commands.json randomized_structured
```

**Expected:**
- RAND() functions evaluated
- Different values each execution
- Valid ranges respected

**Validates:** RAND() works in structured params

---

#### Test 3.2: BATCH with Structured RAND()
**Command:**
```bash
BATCH 5 datasets_phase2.json dataset_organic_varied test_batch
```

**Expected:**
- 5 images generated
- Each image different (RAND() varying)
- All images valid

**Validates:** RAND() evaluation per iteration

---

### 4. Underscore Comment Tests

#### Test 4.1: Comments Ignored
**Create test file `test_comments.json`:**
```json
{
  "comment_test": {
    "commands": [
      "CLEAR WIP ALL",
      {
        "_comment": "This should be ignored",
        "_author": "Test",
        "_version": "1.0",
        "command": "POLY",
        "name": "test",
        "points": [[100,100], [200,100], [200,200]],
        "_note": "Triangle"
      }
    ]
  }
}
```

**Expected:**
- Underscore fields silently ignored
- Polygon created successfully
- No errors about unknown parameters

**Validates:** Underscore field filtering

---

#### Test 4.2: All-Underscore Command Error
**Create test file `test_all_underscore.json`:**
```json
{
  "bad_section": {
    "commands": [
      {
        "_comment": "Only underscores",
        "_note": "This should error"
      }
    ]
  }
}
```

**Expected:**
- Error: "all fields ignored"
- Clear error message

**Validates:** All-underscore detection

---

### 5. Command Coverage Tests

#### Test 5.1: Shape Creation Commands
**Command:**
```bash
RUN all_shapes_structured.json structured_poly
RUN all_shapes_structured.json structured_line
```

**Expected:**
- POLY with array points works
- LINE with array start/end works

**Validates:** Shape creation commands

---

#### Test 5.2: Transform Commands
**Command:**
```bash
RUN all_shapes_structured.json transformation_structured
```

**Expected:**
- MOVE, ROTATE, SCALE execute
- Structured format works for transforms

**Validates:** Transform commands

---

### 6. Validation Tests

#### Test 6.1: Missing "command" Field
**Create test file `test_missing_command.json`:**
```json
{
  "bad_section": {
    "commands": [
      {
        "method": "dynamic_polygon",
        "name": "test"
      }
    ]
  }
}
```

**Expected:**
- Error: "missing 'command' field"
- Clear error message

**Validates:** Command field validation

---

#### Test 6.2: Invalid Command Type
**Create test file `test_invalid_type.json`:**
```json
{
  "bad_section": {
    "commands": [
      123,
      ["array", "command"]
    ]
  }
}
```

**Expected:**
- Error: "must be string or dict"
- Clear error message for each

**Validates:** Type validation

---

### 7. Case Insensitivity Tests

#### Test 7.1: Lowercase Commands
**Create test file `test_case.json`:**
```json
{
  "case_test": {
    "commands": [
      "clear wip all",
      {
        "command": "proc",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {"VERTICES": 5, "BOUNDS": [100,100,300,300]}
      },
      {"command": "color", "name": "test", "color": "blue"}
    ]
  }
}
```

**Expected:**
- Lowercase "proc" works
- Lowercase "color" works
- String commands case-insensitive (existing)

**Validates:** Case insensitivity

---

### 8. Real-World Usage Tests

#### Test 8.1: Parameter Exploration Workflow
**Commands:**
```bash
RUN datasets_phase2.json explore_vertices_5
RUN datasets_phase2.json explore_vertices_8
RUN datasets_phase2.json explore_vertices_12
```

**Expected:**
- Each creates different vertex count shape
- Easy to compare results
- Clear documentation in sections

**Validates:** Exploration workflow

---

#### Test 8.2: Depth Range Comparison
**Commands:**
```bash
RUN datasets_phase2.json explore_depth_shallow
RUN datasets_phase2.json explore_depth_medium
RUN datasets_phase2.json explore_depth_deep
```

**Expected:**
- Visual difference in depth effects
- Same vertices/iterations, only depth varies
- Clear progressive difference

**Validates:** Structured params aid comparison

---

#### Test 8.3: Dataset Generation
**Command:**
```bash
BATCH 25 datasets_phase2.json dataset_organic_varied test_dataset
```

**Expected:**
- 25 unique images generated
- Clear variation in shapes
- All images valid PNG files
- Randomization working correctly

**Validates:** Production dataset workflow

---

#### Test 8.4: Complex Composition
**Command:**
```bash
RUN datasets_phase2.json layered_composition_structured
```

**Expected:**
- Multiple layers created
- Z-ordering correct (bg behind fg)
- Transparency applied
- All shapes visible

**Validates:** Complex multi-shape workflow

---

### 9. Edge Case Tests

#### Test 9.1: Empty Params Dict
**Create test file `test_empty_params.json`:**
```json
{
  "empty_test": {
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {}
      }
    ]
  }
}
```

**Expected:**
- Executor error about missing required params
- Error from PROC validator, not Phase 2 code

**Validates:** Empty params handling

---

#### Test 9.2: Deeply Nested Underscore Comments
**Create test file `test_nested_comments.json`:**
```json
{
  "nested_test": {
    "commands": [
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "test",
        "params": {
          "_section": "Main params",
          "VERTICES": 5,
          "_subsection": "Position",
          "BOUNDS": [100, 100, 300, 300],
          "_end": "Done"
        }
      }
    ]
  }
}
```

**Expected:**
- All underscore fields in params ignored
- PROC executes with VERTICES and BOUNDS only

**Validates:** Nested comment filtering

---

#### Test 9.3: Mixed Types in Points Array
**Create test file `test_mixed_points.json`:**
```json
{
  "mixed_test": {
    "commands": [
      {
        "command": "POLY",
        "name": "test",
        "points": [
          [100, 100],
          [200.5, 100],
          [200, 200.5]
        ]
      }
    ]
  }
}
```

**Expected:**
- Integers and floats both handled
- Polygon created successfully

**Validates:** Type flexibility

---

### 10. Integration Tests

#### Test 10.1: Phase 1 and Phase 2 in Same File
**Create test file `test_mixed_phases.json`:**
```json
{
  "phase1_section": {
    "description": "All strings",
    "commands": [
      "CLEAR WIP ALL",
      "PROC dynamic_polygon s1 VERTICES=5 BOUNDS=100,100,300,300",
      "COLOR s1 red"
    ]
  },
  "phase2_section": {
    "description": "All structured",
    "commands": [
      "CLEAR WIP ALL",
      {
        "command": "PROC",
        "method": "dynamic_polygon",
        "name": "s2",
        "params": {"VERTICES": 5, "BOUNDS": [100,100,300,300]}
      },
      {"command": "COLOR", "name": "s2", "color": "blue"}
    ]
  }
}
```

**Expected:**
- Both sections work
- Can run either independently

**Validates:** Phase coexistence

---

#### Test 10.2: RUN then BATCH with Same File
**Commands:**
```bash
RUN datasets_phase2.json dataset_organic_varied
BATCH 10 datasets_phase2.json dataset_organic_varied test_batch
```

**Expected:**
- RUN creates single instance
- BATCH creates 10 variations
- Both use same section definition

**Validates:** Multi-use sections

---

## Test Results Template

### Test Run: [Date]

**Environment:**
- Shape Studio version: _____
- Python version: _____
- OS: _____

**Results:**

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| 1.1 | Phase 1 compat | ⬜ | |
| 1.2 | Simple structured | ⬜ | |
| 1.3 | Mixed format | ⬜ | |
| 2.1 | Array conversion | ⬜ | |
| 2.2 | Number conversion | ⬜ | |
| 3.1 | RAND() structured | ⬜ | |
| 3.2 | BATCH RAND() | ⬜ | |
| 4.1 | Comments ignored | ⬜ | |
| 4.2 | All-underscore error | ⬜ | |
| 5.1 | Shape commands | ⬜ | |
| 5.2 | Transform commands | ⬜ | |
| 6.1 | Missing command error | ⬜ | |
| 6.2 | Invalid type error | ⬜ | |
| 7.1 | Case insensitive | ⬜ | |
| 8.1 | Exploration workflow | ⬜ | |
| 8.2 | Depth comparison | ⬜ | |
| 8.3 | Dataset generation | ⬜ | |
| 8.4 | Complex composition | ⬜ | |
| 9.1 | Empty params | ⬜ | |
| 9.2 | Nested comments | ⬜ | |
| 9.3 | Mixed types | ⬜ | |
| 10.1 | Phase coexistence | ⬜ | |
| 10.2 | Multi-use sections | ⬜ | |

**Legend:** ✅ Pass | ❌ Fail | ⬜ Not Run

**Summary:**
- Tests passed: __ / 23
- Tests failed: __
- Critical issues: __

---

## Regression Testing

After Phase 2 implementation, verify:

### Phase 1 Functionality
- [ ] All Phase 1 example files work unchanged
- [ ] Text .txt scripts work unchanged
- [ ] RUN command with .txt files
- [ ] BATCH command with .txt files

### Core Commands
- [ ] All shape creation commands
- [ ] All transform commands
- [ ] All styling commands
- [ ] All canvas commands
- [ ] All storage commands

### UI
- [ ] Command log shows commands correctly
- [ ] Errors display clearly
- [ ] Canvas updates properly
- [ ] Zoom/rulers/grid work

---

## Performance Testing

### Test P1: Large Section
Create section with 100+ commands. Verify reasonable execution time.

### Test P2: Large BATCH
Run BATCH 500 with structured commands. Verify no memory issues.

### Test P3: Complex PROC
PROC with all parameters in structured format. Verify no overhead.

---

## Known Issues / Edge Cases

Document any discovered issues:

1. **Issue:** _____
   **Workaround:** _____
   **Priority:** _____

2. **Issue:** _____
   **Workaround:** _____
   **Priority:** _____

---

## Sign-Off

**Tested by:** _____  
**Date:** _____  
**Phase 2 Status:** ⬜ Ready for Release | ⬜ Needs Work  
**Notes:** _____
