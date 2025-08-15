from pathlib import Path
import pandas as pd

import panel as pn

# Import the reusable PDF exporter
from bd_data_fetcher.panel.pdf_exporter import export_panel_to_html, export_panel_to_pdf

# Configure Panel
pn.extension('bootstrap')

def load_umap_data():
    """
    Load umap_data.csv and extract unique replicate set information.
    
    Returns:
        dict: Dictionary mapping cell lines to their Ir and RFT replicate set IDs
    """
    # Path to the CSV file
    csv_path = Path(__file__).parent.parent.parent.parent.parent / "MET" / "umap_data.csv"
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Get unique combinations of replicate set ID, cell line, and chemistry
    unique_data = df[['Replicate Set ID', 'Cell Line', 'Chemistry']].drop_duplicates()
    
    # Build mappings: cell_line -> {Ir: replicate_set_id, RFT: replicate_set_id}
    cell_line_mappings = {}
    
    for _, row in unique_data.iterrows():
        cell_line = row['Cell Line']
        replicate_set_id = row['Replicate Set ID']
        chemistry = row['Chemistry']
        
        if cell_line not in cell_line_mappings:
            cell_line_mappings[cell_line] = {}
        
        cell_line_mappings[cell_line][chemistry] = replicate_set_id
    
    return cell_line_mappings

def get_image_paths(cell_line, cell_line_mappings, current_dir):
    """
    Get the image paths for a given cell line.
    
    Args:
        cell_line (str): Name of the cell line
        cell_line_mappings (dict): Mappings from cell line to replicate set IDs
        current_dir (Path): Directory containing the images
        
    Returns:
        list: List of 3 image paths [Ir_umap, RFT_umap, sigmoidal] or None if any image is missing
    """
    mappings = cell_line_mappings.get(cell_line, {})
    
    # Get Ir and RFT replicate set IDs
    ir_replicate_id = mappings.get('Ir')
    rft_replicate_id = mappings.get('RFT')
    
    # Build image paths
    ir_umap_path = f"umaps/zoomed_volcano_plot_{ir_replicate_id}.png" if ir_replicate_id else None
    rft_umap_path = f"umaps/zoomed_volcano_plot_{rft_replicate_id}.png" if rft_replicate_id else None
    sigmoidal_path = f"sigmoidals/sigmoidal_curve_{cell_line}.png"
    
    # Check if all files exist before adding to list
    image_paths = []
    
    if ir_umap_path and (current_dir / ir_umap_path).exists():
        image_paths.append(ir_umap_path)
    else:
        print(f"Warning: Ir UMAP image not found for {cell_line} (replicate set {ir_replicate_id})")
        return None
    
    if rft_umap_path and (current_dir / rft_umap_path).exists():
        image_paths.append(rft_umap_path)
    else:
        print(f"Warning: RFT UMAP image not found for {cell_line} (replicate set {rft_replicate_id})")
        return None
    
    if (current_dir / sigmoidal_path).exists():
        image_paths.append(sigmoidal_path)
    else:
        print(f"Warning: Sigmoidal curve image not found for {cell_line}")
        return None
    
    # Only return the list if we have all 3 images
    if len(image_paths) == 3:
        return image_paths
    else:
        return None

def create_umap_row(image_paths, vertical_text, current_dir=None, show_headers=False):
    """
    Create a reusable Panel layout row with vertical text and three images in a light blue band.
    
    Args:
        image_paths (list): List of 3 image file paths
        vertical_text (str): Text to display vertically
        current_dir (Path, optional): Directory containing images. If None, uses current file's directory.
        show_headers (bool): Whether to show header labels above images
    
    Returns:
        pn.Column: Panel column with the layout
    """
    if current_dir is None:
        current_dir = Path(__file__).parent

    # Create image widgets optimized for PDF - larger sizes for better visibility
    umap_1_img = pn.pane.PNG(str(current_dir / image_paths[0]), width=250, height=200, sizing_mode="fixed", fixed_aspect=False)
    umap_2_img = pn.pane.PNG(str(current_dir / image_paths[1]), width=250, height=200, sizing_mode="fixed", fixed_aspect=False)
    sigmoidal_img = pn.pane.PNG(str(current_dir / image_paths[2]), width=250, height=200, sizing_mode="fixed", fixed_aspect=False)

    # Create vertical text using HTML with CSS transform
    vertical_text_pane = pn.pane.HTML(
        f'''
        <div class="vertical-text" style="
            writing-mode: vertical-rl; 
            text-orientation: mixed; 
            transform: rotate(180deg);
            font-size: 22px; 
            font-weight: bold; 
            color: #2c3e50; 
            height: 200px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 6px;
            margin-right: 15px;
        ">
            {vertical_text}
        </div>
        ''',
        width=55,
        height=200,
        sizing_mode="fixed",
        styles={'display': 'flex', 'align-items': 'center'}
    )

    # Create header labels if requested
    if show_headers:
        header_1 = pn.pane.Markdown("**Ir**", width=250, height=30, sizing_mode="fixed", styles={'text-align': 'center', 'margin': '0'})
        header_2 = pn.pane.Markdown("**RFT**", width=250, height=30, sizing_mode="fixed", styles={'text-align': 'center', 'margin': '0'})
        header_3 = pn.pane.Markdown("**WCE**", width=250, height=30, sizing_mode="fixed", styles={'text-align': 'center', 'margin': '0'})

        # Create header row
        header_row = pn.Row(
            pn.pane.HTML('<div style="width: 55px;"></div>', width=55, height=30, sizing_mode="fixed"),  # Spacer for vertical text
            header_1,
            header_2,
            header_3,
            sizing_mode="fixed",
            width=870,
            height=30,
            styles={
                'gap': '8px',
                'justify-content': 'center',
                'align-items': 'center',
                'display': 'flex'
            }
        )

    # Create the images row with tighter spacing for PDF
    images_row = pn.Row(
        umap_1_img,
        umap_2_img,
        sigmoidal_img,
        sizing_mode="fixed",
        width=800,
        height=200,
        styles={
            'gap': '8px',
            'justify-content': 'center',
            'align-items': 'center',
            'display': 'flex'
        }
    )

    # Create the main layout without the light blue container
    main_layout = pn.Row(
        vertical_text_pane,
        images_row,
        sizing_mode="fixed",
        width=870,
        height=220,
        styles={
            'gap': '15px',
            'align-items': 'center',
            'justify-content': 'center',
            'padding': '15px',
            'display': 'flex',
            'flex-direction': 'row',
            'page-break-inside': 'avoid',
            'break-inside': 'avoid',
            'margin-bottom': '20px'
        }
    )

    # Return with or without headers
    if show_headers:
        return pn.Column(
            header_row,
            main_layout,
            sizing_mode="fixed",
            width=870,
            styles={'gap': '0px'}
        )
    else:
        return main_layout

def create_umap_layout():
    """
    Create a Panel layout with multiple rows of vertical text and three images.
    """
    # Get the current directory where the images are located
    current_dir = Path(__file__).parent
    
    # Load the UMAP data and build mappings
    cell_line_mappings = load_umap_data()
    
    # Get all cell lines that have both Ir and RFT data
    valid_cell_lines = []
    total_cell_lines = 0
    
    for cell_line, mappings in cell_line_mappings.items():
        if 'Ir' in mappings and 'RFT' in mappings:
            total_cell_lines += 1
            image_paths = get_image_paths(cell_line, cell_line_mappings, current_dir)
            if image_paths:
                valid_cell_lines.append({
                    'cell_line': cell_line,
                    'image_paths': image_paths
                })
                print(f"✓ Added {cell_line} with images: {image_paths}")
            else:
                print(f"✗ Skipped {cell_line} - missing images")
    
    print(f"Found {len(valid_cell_lines)} cell lines with complete data out of {total_cell_lines} total cell lines with Ir/RFT data")
    
    # Create rows for each valid cell line with page break controls
    rows = []
    for i, data in enumerate(valid_cell_lines):
        row = create_umap_row(
            image_paths=data['image_paths'],
            vertical_text=data['cell_line'],
            current_dir=current_dir,
            show_headers=(i == 0)  # Show headers only for the first row
        )
        
        # Add page break control every 2 rows (after the 2nd, 4th, 6th, etc.)
        if i > 0 and i % 2 == 0:
            # Add a page break spacer
            page_break_spacer = pn.pane.HTML(
                '<div style="page-break-before: always; break-before: page; height: 0; margin: 0; padding: 0;"></div>',
                width=870,
                height=0,
                sizing_mode="fixed"
            )
            rows.append(page_break_spacer)
        
        rows.append(row)

    # Combine all rows with spacing optimized for PDF and page break controls
    main_layout = pn.Column(
        *rows,
        sizing_mode="fixed",
        width=870,
        styles={
            'gap': '20px',
            'page-break-inside': 'avoid',
            'break-inside': 'avoid'
        }
    )

    return main_layout

# PDF export functions are now handled by the reusable pdf_exporter module

def create_full_report():
    """
    Create a complete report with title and layout.
    """
    # Create the main layout
    layout = create_umap_layout()

    # Create a complete report
    report = pn.Column(
        layout,
        sizing_mode="stretch_width",
        styles={'padding': '20px'}
    )

    return report

def main():
    """
    Main function to create and display the layout.
    """
    # Create the full report
    report = create_full_report()

    # Show the app
    # report.show()

    print("Attempting PDF export with reusable Playwright exporter...")
    pdf_path = export_panel_to_pdf(
        layout=report,
        output_path="umap_report.pdf",
        title="UMAP Analysis Report",
        page_size="A4",
        orientation="landscape",
        margin=0.5,
        print_background=True
    )

    if pdf_path and pdf_path.endswith('.pdf'):
        print(f"✅ PDF successfully created: {pdf_path}")
    else:
        print("❌ PDF export failed")
        print("🔄 Attempting HTML export as fallback...")
        html_path = export_panel_to_html(report, "umap_report.html")
        if html_path:
            print(f"✅ HTML export successful: {html_path}")

    return report, pdf_path

if __name__ == "__main__":
    report, pdf_path = main()
