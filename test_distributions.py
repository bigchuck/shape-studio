#!/usr/bin/env python3
"""
Distribution Testing Tool for Shape Studio
Tests uniform and normal distributions with histogram output
"""
import random
import sys
from collections import defaultdict


def generate_normal_sample(min_val, max_val, mean, std, max_retries=1000):
    """Generate a single normal distribution sample with rejection sampling"""
    for attempt in range(max_retries):
        value = random.gauss(mean, std)
        if min_val <= value <= max_val:
            return value
    raise ValueError(f"Failed after {max_retries} attempts")


def generate_uniform_sample(min_val, max_val):
    """Generate a single uniform distribution sample"""
    return random.uniform(min_val, max_val)


def bucketize(value, min_val, max_val, num_buckets):
    """Determine which bucket a value falls into (0 to num_buckets-1)"""
    if value < min_val:
        return -1  # Below range
    if value > max_val:
        return num_buckets  # Above range
    
    bucket_width = (max_val - min_val) / num_buckets
    bucket = int((value - min_val) / bucket_width)
    
    # Handle edge case where value == max_val
    if bucket >= num_buckets:
        bucket = num_buckets - 1
    
    return bucket


def print_histogram(buckets, min_val, max_val, num_buckets, total_samples):
    """Print ASCII histogram of bucket counts"""
    bucket_width = (max_val - min_val) / num_buckets
    
    # Find max count for scaling
    max_count = max(buckets.values()) if buckets else 1
    bar_width = 50  # Max width of ASCII bars
    
    print("\n" + "=" * 70)
    print("DISTRIBUTION HISTOGRAM")
    print("=" * 70)
    print(f"Total samples: {total_samples}")
    print(f"Bucket width: {bucket_width:.4f}")
    print()
    
    # Print buckets
    for i in range(num_buckets):
        bucket_min = min_val + i * bucket_width
        bucket_max = min_val + (i + 1) * bucket_width
        count = buckets[i]
        percentage = (count / total_samples * 100) if total_samples > 0 else 0
        
        # ASCII bar
        bar_length = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = "█" * bar_length
        
        print(f"[{bucket_min:6.3f} - {bucket_max:6.3f}]: {count:5d} ({percentage:5.2f}%) {bar}")
    
    # Print out-of-range counts if any
    if -1 in buckets or num_buckets in buckets:
        print()
        print("OUT OF RANGE:")
        if -1 in buckets:
            print(f"  Below {min_val}: {buckets[-1]} samples")
        if num_buckets in buckets:
            print(f"  Above {max_val}: {buckets[num_buckets]} samples")
    
    print("=" * 70)


def print_statistics(samples, min_val, max_val, mean, std):
    """Print statistical summary"""
    if not samples:
        print("No samples to analyze")
        return
    
    actual_min = min(samples)
    actual_max = max(samples)
    actual_mean = sum(samples) / len(samples)
    
    # Calculate standard deviation
    variance = sum((x - actual_mean) ** 2 for x in samples) / len(samples)
    actual_std = variance ** 0.5
    
    print("\n" + "=" * 70)
    print("STATISTICAL SUMMARY")
    print("=" * 70)
    print(f"Expected range:  [{min_val:.4f}, {max_val:.4f}]")
    print(f"Actual range:    [{actual_min:.4f}, {actual_max:.4f}]")
    print(f"Expected mean:   {mean:.4f}")
    print(f"Actual mean:     {actual_mean:.4f}")
    print(f"Expected std:    {std:.4f}")
    print(f"Actual std:      {actual_std:.4f}")
    print("=" * 70)


def test_uniform(min_val, max_val, num_samples, num_buckets):
    """Test uniform distribution"""
    print("\n" + "=" * 70)
    print("UNIFORM DISTRIBUTION TEST")
    print("=" * 70)
    print(f"Range: [{min_val}, {max_val}]")
    print(f"Samples: {num_samples}")
    print(f"Buckets: {num_buckets}")
    
    samples = []
    buckets = defaultdict(int)
    
    for _ in range(num_samples):
        value = generate_uniform_sample(min_val, max_val)
        samples.append(value)
        bucket = bucketize(value, min_val, max_val, num_buckets)
        buckets[bucket] += 1
    
    print_histogram(buckets, min_val, max_val, num_buckets, num_samples)
    
    # For uniform, mean should be center, std should be range/sqrt(12)
    expected_mean = (min_val + max_val) / 2
    expected_std = (max_val - min_val) / (12 ** 0.5)
    print_statistics(samples, min_val, max_val, expected_mean, expected_std)


def test_normal(min_val, max_val, mean, std, num_samples, num_buckets):
    """Test normal distribution"""
    print("\n" + "=" * 70)
    print("NORMAL DISTRIBUTION TEST")
    print("=" * 70)
    print(f"Range: [{min_val}, {max_val}]")
    print(f"Mean: {mean}")
    print(f"Std Dev: {std}")
    print(f"Samples: {num_samples}")
    print(f"Buckets: {num_buckets}")
    
    samples = []
    buckets = defaultdict(int)
    failed = 0
    
    for _ in range(num_samples):
        try:
            value = generate_normal_sample(min_val, max_val, mean, std)
            samples.append(value)
            bucket = bucketize(value, min_val, max_val, num_buckets)
            buckets[bucket] += 1
        except ValueError:
            failed += 1
    
    if failed > 0:
        print(f"\nWARNING: {failed} samples failed to generate (exceeded retry limit)")
    
    print_histogram(buckets, min_val, max_val, num_buckets, len(samples))
    print_statistics(samples, min_val, max_val, mean, std)


def print_usage():
    """Print usage instructions"""
    print("Distribution Testing Tool for Shape Studio")
    print()
    print("USAGE:")
    print("  Uniform distribution:")
    print("    python test_distributions.py uniform <min> <max> [samples] [buckets]")
    print()
    print("  Normal distribution:")
    print("    python test_distributions.py normal <min> <max> <mean> <std> [samples] [buckets]")
    print()
    print("EXAMPLES:")
    print("  python test_distributions.py uniform 0.5 1.5")
    print("  python test_distributions.py uniform 0.5 1.5 10000 20")
    print("  python test_distributions.py normal 0.5 1.5 1.0 0.3")
    print("  python test_distributions.py normal 10 25 17 4 5000 15")
    print()
    print("DEFAULT VALUES:")
    print("  samples: 10000")
    print("  buckets: 10")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    dist_type = sys.argv[1].lower()
    
    if dist_type == "uniform":
        if len(sys.argv) < 4:
            print("ERROR: Uniform requires min and max")
            print_usage()
            sys.exit(1)
        
        min_val = float(sys.argv[2])
        max_val = float(sys.argv[3])
        num_samples = int(sys.argv[4]) if len(sys.argv) > 4 else 10000
        num_buckets = int(sys.argv[5]) if len(sys.argv) > 5 else 10
        
        test_uniform(min_val, max_val, num_samples, num_buckets)
    
    elif dist_type == "normal":
        if len(sys.argv) < 6:
            print("ERROR: Normal requires min, max, mean, and std")
            print_usage()
            sys.exit(1)
        
        min_val = float(sys.argv[2])
        max_val = float(sys.argv[3])
        mean = float(sys.argv[4])
        std = float(sys.argv[5])
        num_samples = int(sys.argv[6]) if len(sys.argv) > 6 else 10000
        num_buckets = int(sys.argv[7]) if len(sys.argv) > 7 else 10
        
        test_normal(min_val, max_val, mean, std, num_samples, num_buckets)
    
    else:
        print(f"ERROR: Unknown distribution type '{dist_type}'")
        print("Must be 'uniform' or 'normal'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()