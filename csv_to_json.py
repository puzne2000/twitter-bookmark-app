#!/usr/bin/env python3
"""
csv_to_json.py

This script reads all CSV files from the ./input folder and merges them into a single
JSON file at ./output/merged.json. Each row from the CSV files becomes a value in the
JSON array, with column names as keys.

Usage:
    python csv_to_json.py

Requirements:
    - Python 3.6+
    - pandas (for CSV reading)
    - os (standard library)
    - json (standard library)

The script will:
1. Create ./output directory if it doesn't exist
2. Read all .csv files from ./input directory
3. Merge all rows into a single JSON array
4. Save the result to ./output/merged.json
"""

import pandas as pd
import json
import os
from pathlib import Path

def main():
    # Define input and output paths
    input_folder = Path("./input")
    output_folder = Path("./output")
    output_file = output_folder / "merged.json"
    
    # Create output directory if it doesn't exist
    output_folder.mkdir(exist_ok=True)
    
    # Check if input folder exists
    if not input_folder.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        print("Please create the './input' folder and place your CSV files there.")
        return
    
    # Get all CSV files from input folder
    csv_files = list(input_folder.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in '{input_folder}'.")
        print("Please place CSV files in the './input' folder.")
        return
    
    print(f"Found {len(csv_files)} CSV file(s):")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    
    # List to store all data
    all_data = []
    
    # Process each CSV file
    for csv_file in csv_files:
        try:
            print(f"\nProcessing {csv_file.name}...")
            
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Convert DataFrame to list of dictionaries
            file_data = df.to_dict('records')
            
            # Add source file information to each record
            for record in file_data:
                record['_source_file'] = csv_file.name
            
            # Extend the main data list
            all_data.extend(file_data)
            
            print(f"  Added {len(file_data)} records from {csv_file.name}")
            
        except Exception as e:
            print(f"  Error processing {csv_file.name}: {e}")
            continue
    
    if not all_data:
        print("\nNo data was successfully processed from any CSV files.")
        return
    
    # Write merged data to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSuccessfully merged {len(all_data)} records from {len(csv_files)} file(s)")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"\nError writing output file: {e}")

if __name__ == "__main__":
    main() 