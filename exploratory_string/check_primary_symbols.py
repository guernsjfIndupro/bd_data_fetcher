#!/usr/bin/env python3
"""
Script to check which protein symbols from ProteinPairs.csv are not using their primary symbol.
"""

import os
import sys
import csv
from typing import Dict, List, Set

# Add the src directory to the path so we can import the UMAP client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from bd_data_fetcher.api.umap_client import UMapServiceClient

def main():
    # Initialize UMAP client
    umap_client = UMapServiceClient()
    
    # Read protein pairs from CSV
    protein_pairs_file = "ProteinPairs.csv"
    if not os.path.exists(protein_pairs_file):
        sys.exit(f"Can't locate protein pairs file {protein_pairs_file}")
    
    # Read protein pairs
    protein_pairs = []
    with open(protein_pairs_file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            anchor_target = row['Anchor Target']
            pair_target = row['Pair Target']
            protein_pairs.append((anchor_target, pair_target))
    
    print(f"Read {len(protein_pairs)} protein pairs from {protein_pairs_file}")
    
    # Get all unique gene symbols from protein pairs
    all_genes = set()
    for anchor, target in protein_pairs:
        all_genes.add(anchor)
        all_genes.add(target)
    
    print(f"Found {len(all_genes)} unique gene symbols")
    
    # Get protein mappings from UMAP service
    print("Fetching protein mappings from UMAP service...")
    try:
        gene_symbols_list = list(all_genes)
        print(f"Mapping {len(gene_symbols_list)} gene symbols...")
        
        endpoint = "proteins/mapping"
        body = {"protein_ids": [], "uniprotkb_acs": [], "symbols": gene_symbols_list}
        response = umap_client._post(endpoint=endpoint, data=body)
        
        # Create mapping from gene symbols to their primary symbols
        symbol_to_primary = {}
        primary_symbols = set()
        
        if "data" in response:
            for protein_data in response["data"]:
                primary_symbol = protein_data.get("primary_symbol")
                symbols_list = protein_data.get("symbols", [])
                
                if primary_symbol and symbols_list:
                    # Map all symbols (including primary) to the primary symbol
                    for symbol in symbols_list:
                        symbol_to_primary[symbol] = primary_symbol
                    
                    primary_symbols.add(primary_symbol)
        
        print(f"Created mappings for {len(symbol_to_primary)} gene symbols")
        print(f"Found {len(primary_symbols)} unique primary symbols")
        
        # Check which symbols in our data are not primary symbols
        non_primary_symbols = []
        primary_symbols_used = []
        
        for gene in all_genes:
            if gene in symbol_to_primary:
                primary_symbol = symbol_to_primary[gene]
                if gene != primary_symbol:
                    non_primary_symbols.append((gene, primary_symbol))
                else:
                    primary_symbols_used.append(gene)
            else:
                print(f"Warning: {gene} not found in UMAP mapping response")
        
        # Display results
        print(f"\n" + "="*60)
        print("PRIMARY SYMBOL ANALYSIS")
        print("="*60)
        
        print(f"\nSummary:")
        print(f"Total unique genes in ProteinPairs.csv: {len(all_genes)}")
        print(f"Genes using primary symbols: {len(primary_symbols_used)}")
        print(f"Genes using non-primary symbols: {len(non_primary_symbols)}")
        
        if non_primary_symbols:
            print(f"\nGenes using non-primary symbols:")
            print(f"{'Symbol in CSV':<20} {'Primary Symbol':<20}")
            print("-" * 40)
            for symbol, primary in sorted(non_primary_symbols):
                print(f"{symbol:<20} {primary:<20}")
        else:
            print(f"\nAll genes in ProteinPairs.csv are using their primary symbols!")
        
        if primary_symbols_used:
            print(f"\nGenes using primary symbols:")
            for symbol in sorted(primary_symbols_used):
                print(f"  {symbol}")
        
        # Show some examples of symbol mappings
        print(f"\nSample symbol mappings from UMAP:")
        count = 0
        for protein_data in response["data"][:5]:  # Show first 5
            primary_symbol = protein_data.get("primary_symbol")
            symbols_list = protein_data.get("symbols", [])
            if primary_symbol and symbols_list:
                print(f"  Primary: {primary_symbol}")
                print(f"  All symbols: {symbols_list}")
                print("  ---")
                count += 1
                if count >= 5:
                    break
        
    except Exception as e:
        print(f"Error fetching protein mappings: {e}")
        return

if __name__ == "__main__":
    main() 