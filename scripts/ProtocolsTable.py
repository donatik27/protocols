#!/usr/bin/env python3
"""
Protocols to CSV Converter

This script collects all Protocol files in a directory and generates a CSV file
for upload to a DB
"""

#import libraries
import argparse
import csv
import json
import os

from pathlib import Path
from typing import List, Dict, Any

# Define a function to parse JSON protocol files
def parse_protocol_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parse a single JSON file and extract the required fields.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract common fields
        name = data.get('name', '')
        description = data.get('description', '') \
            .replace('"', '') \
            .replace('\n', '')

        # Get first category or empty string if no categories
        categories = data.get('categories', [])
        if not categories:
            raise Exception(f"missing category for {name}")
        first_category = categories[0]
        parts = first_category.split('::')
        if len(parts) < 2:
            raise Exception(f"invalid category format '{first_category}' in {name}, expected 'type::subtype'")

        type, subtype = parts[0], parts[1]

        # Get addresses
        addresses = data.get('addresses', {})

        # Create rows - one for each address
        rows = []
        for contract_name, address in addresses.items():
            row = {
                'name': name,
                'ctype': type,
                'csubtype': subtype,
                'contract': contract_name,
                'address': address.lower()
            }
            rows.append(row)

        return rows

    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error processing {file_path}: {e}")
        return []

# Define a function to collect protocol files in a given directory
def collect_protocol_files(directory: str) -> List[str]:
    """
    Collect all protocol files in the specified directory.
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
    if not directory_path.is_dir():
        raise NotADirectoryError(f"'{directory}' is not a directory")

    json_files = list(directory_path.glob('*.json'))
    return [str(f) for f in json_files]

# Define a function to write data to a CSV files
def write_csv(rows: List[Dict[str, str]], output_file: str) -> None:
    """
    Write the extracted data to a CSV file.
    """
    if not rows:
        print("No data to write to CSV")
        return

    fieldnames = ['name', 'ctype', 'csubtype', 'contract', 'address']
    rows = sorted(rows, key=lambda x: (x['ctype'], x['csubtype'], x['name']))

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully wrote {len(rows)} rows to {output_file}")

# Define a function to collect protocol files in a given directory and then parse the JSON protocol files, and write data to a CSV file
def main():
    """Main function to parse arguments and process files."""
    parser = argparse.ArgumentParser(
        description='Convert protocol files to a CSV for DB upload')
    parser.add_argument(
        '-s','--src',
        default='testnet',
        help='Directory containing protocol files to process'
    )
    parser.add_argument(
        '-o', '--out',
        default='./protocols.csv',
        help='Output CSV file name (default: output.csv)'
    )
    args = parser.parse_args()
    src = os.path.expanduser(args.src)
    out = os.path.expanduser(args.out)

    try:
        protocol_files = collect_protocol_files(src)
        print(f"Found {len(protocol_files)} protocol files")

        # Process all JSON files
        all_rows = []
        for file in protocol_files:
            print(f"Processing {file}...")
            rows = parse_protocol_file(file)
            all_rows.extend(rows)

        # Write to CSV
        write_csv(all_rows, out)

    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
