#!/usr/bin/env python3
"""
PID2Graph Dataset Download Script
Downloads the PID2Graph benchmark dataset from Zenodo.
"""
import os
import sys
import argparse
import hashlib
from pathlib import Path

# Zenodo URL
ZENODO_RECORD = "14803338"
DATASET_URL = f"https://zenodo.org/records/{ZENODO_RECORD}/files/PID2Graph.zip?download=1"
EXPECTED_MD5 = "90f782220de97e7e249d2595c49ddc1c"
DATASET_SIZE_GB = 9.3


def check_disk_space(path: Path, required_gb: float = 15.0) -> bool:
    """Check if there's enough disk space."""
    import shutil
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024**3)
    print(f"Available disk space: {free_gb:.1f} GB")
    return free_gb >= required_gb


def verify_md5(filepath: Path, expected: str) -> bool:
    """Verify MD5 checksum of downloaded file."""
    print(f"Verifying MD5 checksum...")
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    actual = md5.hexdigest()
    if actual == expected:
        print(f"✅ MD5 verified: {actual}")
        return True
    else:
        print(f"❌ MD5 mismatch: expected {expected}, got {actual}")
        return False


def download_dataset(output_dir: Path, full: bool = True):
    """Download the PID2Graph dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not check_disk_space(output_dir, required_gb=15.0):
        print(f"❌ Not enough disk space. Need at least 15GB (dataset is {DATASET_SIZE_GB}GB)")
        sys.exit(1)

    zip_path = output_dir / "PID2Graph.zip"

    if zip_path.exists():
        print(f"Dataset already exists at {zip_path}")
        if verify_md5(zip_path, EXPECTED_MD5):
            print("Using existing download.")
        else:
            print("Re-downloading due to checksum mismatch...")
            zip_path.unlink()

    if not zip_path.exists():
        print(f"Downloading PID2Graph dataset ({DATASET_SIZE_GB}GB)...")
        print(f"URL: {DATASET_URL}")
        print("This may take a while...")

        try:
            import urllib.request

            def progress_hook(count, block_size, total_size):
                percent = min(count * block_size * 100 / total_size, 100)
                downloaded = count * block_size / (1024**3)
                total = total_size / (1024**3)
                sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded:.2f}/{total:.2f} GB)")
                sys.stdout.flush()

            urllib.request.urlretrieve(DATASET_URL, zip_path, reporthook=progress_hook)
            print("\n✅ Download complete!")

        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            print("\nManual download instructions:")
            print(f"1. Visit: https://zenodo.org/records/{ZENODO_RECORD}")
            print(f"2. Download PID2Graph.zip")
            print(f"3. Place it in: {output_dir}")
            sys.exit(1)

        if not verify_md5(zip_path, EXPECTED_MD5):
            print("❌ Download corrupted. Please try again.")
            sys.exit(1)

    # Extract
    print("Extracting dataset...")
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(output_dir)
    print("✅ Extraction complete!")

    # Show structure
    print("\nDataset structure:")
    for item in (output_dir / "PID2Graph").iterdir():
        if item.is_dir():
            count = len(list(item.glob("**/*")))
            print(f"  {item.name}/: {count} files")


def create_sample_subset(data_dir: Path, sample_count: int = 10):
    """Create a small sample subset for testing."""
    sample_dir = data_dir / "sample"
    sample_dir.mkdir(exist_ok=True)

    print(f"\nNote: Full dataset download required first.")
    print(f"After download, sample subset will be created at: {sample_dir}")
    print(f"Sample size: {sample_count} images")


def main():
    parser = argparse.ArgumentParser(description="Download PID2Graph dataset")
    parser.add_argument("--full", action="store_true", help="Download full dataset (9.3GB)")
    parser.add_argument("--sample", action="store_true", help="Download sample only (for testing)")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / args.output

    print("=" * 60)
    print("PID2Graph Dataset Download")
    print("=" * 60)
    print(f"Zenodo Record: {ZENODO_RECORD}")
    print(f"Dataset Size: {DATASET_SIZE_GB} GB")
    print(f"Output: {output_dir}")
    print("=" * 60)

    if args.sample:
        create_sample_subset(output_dir)
    elif args.full:
        download_dataset(output_dir, full=True)
    else:
        print("\nUsage:")
        print("  python download.py --full    # Download full dataset (9.3GB)")
        print("  python download.py --sample  # Create sample subset")
        print("\nNote: The dataset is 9.3GB. Ensure you have enough disk space.")


if __name__ == "__main__":
    main()
