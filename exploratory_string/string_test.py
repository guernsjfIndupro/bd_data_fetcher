import csv
import os
import re
import sys

# Add the src directory to the path so we can import the UMAP client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from bd_data_fetcher.api.umap_client import UMapServiceClient

##########################################################
## This script combines all the STRING's channels subscores
## into the final combined STRING score.
## It uses unpacked protein.links.full.xx.txt.gz as input
## which can be downloaded from the download subpage:
##      https://string-db.org/cgi/download.pl
##
## Algorithm updated for versions v12 and up.
##########################################################

def extract_ensp_from_protein_id(protein_id: str) -> str:
    """
    Extract ENSP value from protein ID in format "9606.ENSP00000000233"
    
    Args:
        protein_id: Protein ID in format "9606.ENSP00000000233"
        
    Returns:
        ENSP value without the "9606." prefix
    """
    if protein_id.startswith("9606."):
        return protein_id[5:]  # Remove "9606." prefix
    return protein_id

def normalize_ensp(ensp: str) -> str:
    """
    Normalize ENSP value by removing version suffix (e.g., ".11")
    
    Args:
        ensp: ENSP value that may have version suffix
        
    Returns:
        Normalized ENSP value without version suffix
    """
    # Remove version suffix if present (e.g., ".11")
    return re.sub(r'\.\d+$', '', ensp)

def match_ensp_to_gene(ensp_value: str, protein_mappings: dict[str, str]) -> str:
    """
    Match ENSP value to gene symbol using protein mappings
    
    Args:
        ensp_value: ENSP value to match
        protein_mappings: Dictionary mapping gene symbols to ENSP values
        
    Returns:
        Gene symbol if found, otherwise None
    """
    normalized_ensp = normalize_ensp(ensp_value)

    for gene_symbol, ensp in protein_mappings.items():
        if normalize_ensp(ensp) == normalized_ensp:
            return gene_symbol

    return None

def compute_prior_away(score, prior):
    score = max(score, prior)
    score_no_prior = (score - prior) / (1 - prior)
    return score_no_prior

def main():
    # Initialize UMAP client for protein mapping
    umap_client = UMapServiceClient()

    # Read protein pairs from CSV
    protein_pairs_file = "ProteinPairs.csv"
    if not os.path.exists(protein_pairs_file):
        sys.exit(f"Can't locate protein pairs file {protein_pairs_file}")

    # Read protein pairs
    protein_pairs = []
    with open(protein_pairs_file, encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        print(f"CSV headers: {reader.fieldnames}")
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
        # Use the map_protein function to get complete protein data
        gene_symbols_list = list(all_genes)
        print(f"Mapping {len(gene_symbols_list)} gene symbols...")

        # Get the raw response from the mapping endpoint
        endpoint = "proteins/mapping"
        body = {"protein_ids": [], "uniprotkb_acs": [], "symbols": gene_symbols_list}
        response = umap_client._post(endpoint=endpoint, data=body)

        # Create mapping from gene symbols to ENSP values
        gene_to_ensp = {}
        ensp_to_gene = {}
        gene_to_all_ensps = {}  # Store all ENSP IDs for each gene

        if "data" in response:
            for protein_data in response["data"]:
                primary_symbol = protein_data.get("primary_symbol")
                symbols_list = protein_data.get("symbols", [])
                ensp_ids = protein_data.get("ensp_ids", [])

                if primary_symbol and ensp_ids:
                    # Normalize all ENSP IDs
                    normalized_ensps = [normalize_ensp(ensp_id) for ensp_id in ensp_ids]

                    # Map primary symbol to the first ENSP (for consistency in gene_to_ensp)
                    gene_to_ensp[primary_symbol] = normalized_ensps[0]

                    # Map ALL ENSP IDs to the primary symbol
                    for ensp in normalized_ensps:
                        ensp_to_gene[ensp] = primary_symbol

                    # Store all ENSP IDs for this gene
                    gene_to_all_ensps[primary_symbol] = normalized_ensps

                    # Map all alternative symbols to the first ENSP and store all ENSPs
                    for alt_symbol in symbols_list:
                        if alt_symbol != primary_symbol:  # Avoid duplicate mapping
                            gene_to_ensp[alt_symbol] = normalized_ensps[0]
                            gene_to_all_ensps[alt_symbol] = normalized_ensps

        print(f"Created mappings for {len(gene_to_ensp)} genes")


    except Exception as e:
        print(f"Error fetching protein mappings: {e}")
        return

    # Create a set of ENSP values we're interested in
    target_ensp_values = set()
    for anchor, target in protein_pairs:
        anchor_ensp = gene_to_ensp.get(anchor)
        target_ensp = gene_to_ensp.get(target)

        if anchor_ensp:
            target_ensp_values.add(normalize_ensp(anchor_ensp))
        if target_ensp:
            target_ensp_values.add(normalize_ensp(target_ensp))

    print(f"Looking for {len(target_ensp_values)} ENSP values in STRING data")
    print(f"Sample target ENSP values: {list(target_ensp_values)[:5]}")

    # Original STRING processing logic
    input_file = "9606.protein.links.full.v12.0.txt"

    if not os.path.exists(input_file):
        sys.exit("Can't locate input file %s" % input_file)

    prior = 0.041

    # Open CSV file for writing
    output_file = "protein_scores.csv"
    seen_pairs = set()  # Track unique symbol pairs regardless of order

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = [
            'protein1', 'protein2', 'symbol1', 'symbol2',
            'coexpression_both_prior_corrected',
            'experiments_both_prior_corrected',
            'textmining_both_prior_corrected',
            'combined_score'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        header = True
        for line in open(input_file):
            if header:
                header = False
                continue

            l = line.split()

            ## load the line
            (protein1, protein2,
             neighborhood, neighborhood_transferred,
             fusion, cooccurrence,
             homology,
             coexpression, coexpression_transferred,
             experiments, experiments_transferred,
             database, database_transferred,
             textmining, textmining_transferred,
             initial_combined) = l

            # Extract ENSP values from protein IDs
            ensp1 = extract_ensp_from_protein_id(protein1)
            ensp2 = extract_ensp_from_protein_id(protein2)

            # Check if this pair contains any of our target ENSP values
            normalized_ensp1 = normalize_ensp(ensp1)
            normalized_ensp2 = normalize_ensp(ensp2)

            # Only process if either protein is in our target set
            if (normalized_ensp1 in target_ensp_values or
                normalized_ensp2 in target_ensp_values):

                ## divide by 1000
                neighborhood = float(neighborhood) / 1000
                neighborhood_transferred = float(neighborhood_transferred) / 1000
                fusion = float(fusion) / 1000
                cooccurrence =  float(cooccurrence) / 1000
                homology = float(homology) / 1000
                coexpression = float(coexpression) / 1000
                coexpression_transferred = float(coexpression_transferred) / 1000
                experiments = float(experiments) / 1000
                experiments_transferred = float(experiments_transferred) / 1000
                database = float(database) / 1000
                database_transferred = float(database_transferred) / 1000
                textmining = float(textmining) / 1000
                textmining_transferred = float(textmining_transferred) / 1000
                initial_combined = int(initial_combined)

                ## compute prior away
                neighborhood_prior_corrected                 = compute_prior_away (neighborhood, prior)
                neighborhood_transferred_prior_corrected     = compute_prior_away (neighborhood_transferred, prior)
                fusion_prior_corrected                       = compute_prior_away (fusion, prior)
                cooccurrence_prior_corrected                 = compute_prior_away (cooccurrence, prior)
                coexpression_prior_corrected                 = compute_prior_away (coexpression, prior)
                coexpression_transferred_prior_corrected     = compute_prior_away (coexpression_transferred, prior)
                experiments_prior_corrected                  = compute_prior_away (experiments, prior)
                experiments_transferred_prior_corrected      = compute_prior_away (experiments_transferred, prior)
                database_prior_corrected                     = compute_prior_away (database, prior)
                database_transferred_prior_corrected         = compute_prior_away (database_transferred, prior)
                textmining_prior_corrected                   = compute_prior_away (textmining, prior)
                textmining_transferred_prior_corrected       = compute_prior_away (textmining_transferred, prior)

                ## then, combine the direct and transferred scores for each category:
                neighborhood_both_prior_corrected = 1.0 - (1.0 - neighborhood_prior_corrected) * (1.0 - neighborhood_transferred_prior_corrected)
                coexpression_both_prior_corrected = 1.0 - (1.0 - coexpression_prior_corrected) * (1.0 - coexpression_transferred_prior_corrected)
                experiments_both_prior_corrected = 1.0 - (1.0 - experiments_prior_corrected) * (1.0 - experiments_transferred_prior_corrected)
                database_both_prior_corrected = 1.0 - (1.0 - database_prior_corrected) * (1.0 - database_transferred_prior_corrected)
                textmining_both_prior_corrected = 1.0 - (1.0 - textmining_prior_corrected) * (1.0 - textmining_transferred_prior_corrected)

                ## next, do the 1 - multiplication:
                combined_score_one_minus = (
                    (1.0 - coexpression_prior_corrected) *
                    (1.0 - experiments_prior_corrected) *
                    (1.0 - textmining_prior_corrected) )

                ## and lastly, do the 1 - conversion again, and put back the prior *exactly once*
                combined_score = (1.0 - combined_score_one_minus)            ## 1- conversion
                combined_score *= (1.0 - prior)                              ## scale down
                combined_score += prior                                      ## and add prior.

                ## round
                combined_score = int(combined_score * 1000)

                # Get gene symbols for the proteins (now using normalized ENSP values)
                symbol1 = ensp_to_gene.get(normalize_ensp(ensp1), "Unknown")
                symbol2 = ensp_to_gene.get(normalize_ensp(ensp2), "Unknown")

                if symbol1 == "Unknown" or symbol2 == "Unknown":
                    continue

                # Create a unique key for the symbol pair regardless of order
                symbol_pair = tuple(sorted([symbol1, symbol2]))

                # Only write if we haven't seen this symbol pair before
                if symbol_pair not in seen_pairs:
                    seen_pairs.add(symbol_pair)

                    # Write to CSV
                    row = {
                        'protein1': protein1,
                        'protein2': protein2,
                        'symbol1': symbol1,
                        'symbol2': symbol2,
                        'coexpression_both_prior_corrected': coexpression_both_prior_corrected,
                        'experiments_both_prior_corrected': experiments_both_prior_corrected,
                        'textmining_both_prior_corrected': textmining_both_prior_corrected,
                        'combined_score': combined_score
                    }
                    writer.writerow(row)

    print(f"Results written to {output_file}")

    # Analyze which gene symbols don't map to any ENSP in STRING data
    print("\n" + "="*60)
    print("MISSING GENES ANALYSIS")
    print("="*60)

    # Read STRING data file and collect all ENSP values
    string_ensp_values = set()
    print("Reading STRING data to collect all ENSP values...")

    with open(input_file) as f:
        header = True
        for line in f:
            if header:
                header = False
                continue

            l = line.split()
            if len(l) >= 2:
                protein1 = l[0]
                protein2 = l[1]

                ensp1 = extract_ensp_from_protein_id(protein1)
                ensp2 = extract_ensp_from_protein_id(protein2)

                string_ensp_values.add(normalize_ensp(ensp1))
                string_ensp_values.add(normalize_ensp(ensp2))

    print(f"Found {len(string_ensp_values)} unique ENSP values in STRING data")

    # Find which gene symbols don't map to any ENSP in STRING data
    missing_genes = set()
    for gene in all_genes:
        all_ensps = gene_to_all_ensps.get(gene)
        if not all_ensps:
            missing_genes.add(gene)  # Gene not mapped to any ENSP
        else:
            # Check if any of the ENSP IDs for this gene are in STRING data
            found_in_string = False
            for ensp in all_ensps:
                if ensp in string_ensp_values:
                    found_in_string = True
                    break

            if not found_in_string:
                missing_genes.add(gene)  # Gene mapped to ENSP not in STRING data

    print("\nResults:")
    print(f"Gene symbols found in STRING data: {len(all_genes) - len(missing_genes)}")
    print(f"Gene symbols missing from STRING data: {len(missing_genes)}")

    if missing_genes:
        print("\nGene symbols missing from STRING data:")
        for gene in sorted(missing_genes):
            ensp = gene_to_ensp.get(gene, "Not mapped")
            print(f"  {gene} -> {ensp}")
    else:
        print("\nAll gene symbols from ProteinPairs.csv are found in STRING data!")

    # Display mapping information
    print("\nGene to ENSP mappings for protein pairs:")
    for anchor, target in protein_pairs[:10]:  # Show first 10 pairs
        anchor_ensp = gene_to_ensp.get(anchor, "Not found")
        target_ensp = gene_to_ensp.get(target, "Not found")
        print(f"{anchor} -> {anchor_ensp}")
        print(f"{target} -> {target_ensp}")
        print("---")

if __name__ == "__main__":
    main()




