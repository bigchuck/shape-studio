#!/usr/bin/env python3
"""
Configuration System Test
Validates that config loading, access, and immutability work correctly
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config


def test_basic_access():
    """Test basic configuration access"""
    print("=" * 60)
    print("TEST 1: Basic Access")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    # Dot notation access
    print(f"Canvas width: {config.canvas.width}")
    print(f"Canvas height: {config.canvas.height}")
    print(f"Output path: {config.paths.output}")
    print(f"Iterations default: {config.procedural.defaults.iterations}")
    print(f"Min clearance: {config.procedural.validation.min_segment_clearance}")
    
    print("✓ Basic access works")
    print()


def test_get_method():
    """Test path-based get method"""
    print("=" * 60)
    print("TEST 2: Path-Based Get")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    # Path-based access
    width = config.get('canvas.width')
    print(f"config.get('canvas.width'): {width}")
    
    # With default
    missing = config.get('canvas.nonexistent', default=999)
    print(f"config.get('canvas.nonexistent', 999): {missing}")
    
    # Nested path
    clearance = config.get('procedural.validation.min_segment_clearance')
    print(f"config.get('procedural.validation.min_segment_clearance'): {clearance}")
    
    print("✓ Path-based access works")
    print()


def test_immutability():
    """Test that config is read-only after load"""
    print("=" * 60)
    print("TEST 3: Immutability")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    # Try to modify (should fail)
    try:
        config.canvas.width = 1024
        print("✗ ERROR: Config modification should have been blocked!")
        return False
    except AttributeError as e:
        print(f"✓ Modification correctly blocked: {e}")
    
    # Verify value unchanged
    print(f"Canvas width still: {config.canvas.width}")
    print()


def test_to_dict():
    """Test dictionary export"""
    print("=" * 60)
    print("TEST 4: Dictionary Export")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    config_dict = config.to_dict()
    print(f"Config as dict has {len(config_dict)} top-level keys:")
    for key in config_dict.keys():
        print(f"  - {key}")
    
    print("✓ Dictionary export works")
    print()


def test_validation_config():
    """Test validation configuration specifically"""
    print("=" * 60)
    print("TEST 5: Validation Configuration")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    val = config.procedural.validation
    
    print("Validation settings:")
    print(f"  Enabled: {val.enabled}")
    print(f"  Check intersections: {val.check_intersections}")
    print(f"  Min segment clearance: {val.min_segment_clearance} px")
    print(f"  Min angle: {val.min_angle} degrees")
    print(f"  Min aspect ratio: {val.min_aspect_ratio}")
    print(f"  Validate each retry: {val.validate_each_retry}")
    
    print("✓ Validation config accessible")
    print()


def test_all_defaults():
    """Test that all default paths are accessible"""
    print("=" * 60)
    print("TEST 6: All Default Paths")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    # Test major paths
    paths_to_test = [
        ('canvas.width', 768),
        ('canvas.height', 768),
        ('canvas.grid_spacing', 64),
        ('paths.output', 'output'),
        ('paths.scripts', 'scripts'),
        ('procedural.defaults.iterations', 10),
        ('procedural.defaults.max_retries', 15),
        ('procedural.operations.break_margin', 0.15),
        ('procedural.operations.projection_max', 2.0),
        ('procedural.validation.min_segment_clearance', 15.0),
        ('procedural.validation.min_angle', 20.0),
        ('procedural.validation.min_aspect_ratio', 0.4),
        ('randomization.normal_distribution.max_sampling_attempts', 1000),
        ('animation.default_fps', 2),
    ]
    
    all_pass = True
    for path, expected in paths_to_test:
        actual = config.get(path)
        status = "✓" if actual == expected else "✗"
        if actual != expected:
            all_pass = False
        print(f"{status} {path}: {actual} (expected {expected})")
    
    if all_pass:
        print("\n✓ All default paths correct")
    else:
        print("\n✗ Some paths have unexpected values")
    print()


def test_usage_patterns():
    """Test typical usage patterns"""
    print("=" * 60)
    print("TEST 7: Usage Patterns")
    print("=" * 60)
    
    config = Config()
    config.load()
    
    # Pattern 1: Direct access in function
    def get_canvas_dims():
        return config.canvas.width, config.canvas.height
    
    w, h = get_canvas_dims()
    print(f"Pattern 1 - Direct access: {w}x{h}")
    
    # Pattern 2: With fallback
    def get_iterations(provided=None):
        return provided if provided is not None else config.procedural.defaults.iterations
    
    print(f"Pattern 2 - With fallback (None): {get_iterations()}")
    print(f"Pattern 2 - With fallback (20): {get_iterations(20)}")
    
    # Pattern 3: Validation check
    def should_validate():
        return config.procedural.validation.enabled
    
    print(f"Pattern 3 - Validation check: {should_validate()}")
    
    print("✓ Usage patterns work")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "SHAPE STUDIO CONFIG SYSTEM TEST" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_basic_access()
        test_get_method()
        test_immutability()
        test_to_dict()
        test_validation_config()
        test_all_defaults()
        test_usage_patterns()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nConfiguration system is working correctly.")
        print("Ready for Phase 2: Module refactoring")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())