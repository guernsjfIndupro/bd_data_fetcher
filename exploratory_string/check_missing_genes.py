#!/usr/bin/env python3
"""
Check which gene symbols from all_genes don't map to any ENSP IDs in the STRING links file.
"""

import os
import sys
import csv
import re
from typing import Set

# Add the src directory to the path so we can import the UMAP client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from bd_data_fetcher.api.umap_client import UMapServiceClient

def extract_ensp_from_protein_id(protein_id: str) -> str:
    """Extract ENSP value from protein ID in format "9606.ENSP00000000233""""
    if protein_id.startswith("9606."):
        return protein_id[5:]  # Remove "9606." prefix
    return protein_id

def normalize_ensp(ensp: str) -> str:
    """Normalize ENSP value by removing version suffix (e.g., ".11")"""
    return re.sub(r'\.\d+$', '', ensp)

def main():
    # Initialize UMAP client
    umap_client = UMapServiceClient()
    
    # Read protein pairs from CSV
    protein_pairs_file = "ProteinPairs.csv"
    if not os.path.exists(protein_pairs_file):
        sys.exit(f"Can't locate protein pairs file {protein_pairs_file}")
    
    # Get all unique gene symbols from protein pairs
    all_genes = set()
    with open(protein_pairs_file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            all_genes.add(row['Anchor Target'])
            all_genes.add(row['Pair Target'])
    
    print(f"Found {len(all_genes)} unique gene symbols in ProteinPairs.csv")
    
    # Get protein mappings from UMAP service
    print("Fetching protein mappings from UMAP service...")
    gene_symbols_list = list(all_genes)
    
    endpoint = "proteins/mapping"
    body = {"protein_ids": [], "uniprotkb_acs": [], "symbols": gene_symbols_list}
    response = umap_client._post(endpoint=endpoint, data=body)
    
    # Create mapping from gene symbols to ENSP values
    gene_to_ensp = {}
    
    if "data" in response:
        for protein_data in response["data"]:
            primary_symbol = protein_data.get("primary_symbol")
            symbols_list = protein_data.get("symbols", [])
            ensp_ids = protein_data.get("ensp_ids", [])
            
            if primary_symbol and ensp_ids:
                # Use the first ENSP ID from the list and normalize it
                ensp_value = ensp_ids[0]
                normalized_ensp = normalize_ensp(ensp_value)
                
                # Map primary symbol to ENSP
                gene_to_ensp[primary_symbol] = normalized_ensp
                
                # Map all alternative symbols to the same ENSP
                for alt_symbol in symbols_list:
                    if alt_symbol != primary_symbol:
                        gene_to_ensp[alt_symbol] = normalized_ensp
    
    print(f"Created mappings for {len(gene_to_ensp)} gene symbols")
    
    # Get all ENSP values from our target proteins
    target_ensp_values = set()
    for gene in all_genes:
        ensp = gene_to_ensp.get(gene)
        if ensp:
            target_ensp_values.add(ensp)
    
    print(f"Looking for {len(target_ensp_values)} ENSP values in STRING data")
    
    # Read STRING data file and collect all ENSP values
    string_file = "9606.protein.links.full.v12.0.txt"
    if not os.path.exists(string_file):
        sys.exit(f"Can't locate STRING file {string_file}")
    
    print("Reading STRING data to collect all ENSP values...")
    string_ensp_values = set()
    
    with open(string_file, 'r') as f:
        header = True
        for line in f:
            if header:
                header = False
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                protein1 = parts[0]
                protein2 = parts[1]
                
                ensp1 = extract_ensp_from_protein_id(protein1)
                ensp2 = extract_ensp_from_protein_id(protein2)
                
                string_ensp_values.add(normalize_ensp(ensp1))
                string_ensp_values.add(normalize_ensp(ensp2))
    
    print(f"Found {len(string_ensp_values)} unique ENSP values in STRING data")
    
    # Find which gene symbols don't map to any ENSP in STRING data
    missing_genes = set()
    for gene in all_genes:
        ensp = gene_to_ensp.get(gene)
        if not ensp:
            missing_genes.add(gene)  # Gene not mapped to any ENSP
        elif ensp not in string_ensp_values:
            missing_genes.add(gene)  # Gene mapped to ENSP not in STRING data
    
    print(f"\nResults:")
    print(f"Gene symbols found in STRING data: {len(all_genes) - len(missing_genes)}")
    print(f"Gene symbols missing from STRING data: {len(missing_genes)}")
    
    if missing_genes:
        print(f"\nGene symbols missing from STRING data:")
        for gene in sorted(missing_genes):
            ensp = gene_to_ensp.get(gene, "Not mapped")
            print(f"  {gene} -> {ensp}")
    else:
        print("\nAll gene symbols from ProteinPairs.csv are found in STRING data!")

if __name__ == "__main__":
    main() 