#!/usr/bin/env python3
"""Test script to verify StringGraph CLI integration."""

import logging
from pathlib import Path

from bd_data_fetcher.cli.graphing import CSVGraphAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_string_integration():
    """Test the StringGraph integration with CSVGraphAnalyzer."""
    
    # Test parameters
    data_dir = "TROP2"
    anchor_protein = "TACSTD2"
    
    print("Testing StringGraph CLI integration...")
    print(f"Data directory: {data_dir}")
    print(f"Anchor protein: {anchor_protein}")
    
    try:
        # Create analyzer
        analyzer = CSVGraphAnalyzer(data_dir, anchor_protein)
        
        # Test STRING data availability check
        print("\n1. Testing STRING data availability check...")
        string_available = analyzer._check_string_data_availability()
        print(f"STRING data available: {string_available}")
        
        # Test CSV directory analysis
        print("\n2. Testing CSV directory analysis...")
        data_type_mapping = analyzer.analyze_csv_directory()
        print(f"Found data types: {list(data_type_mapping.keys())}")
        
        # Test graph generation (without actually generating files)
        print("\n3. Testing graph generation setup...")
        print("This would generate graphs for:")
        for data_type in data_type_mapping.keys():
            print(f"  - {data_type}")
        
        if string_available:
            print("  - STRING protein-protein interactions")
        
        print("\n✅ StringGraph CLI integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        raise


if __name__ == "__main__":
    test_string_integration() 