import panel as pn
import os
from pathlib import Path
import weasyprint
from weasyprint import HTML, CSS

# Configure Panel
pn.extension('bootstrap')

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
            'flex-direction': 'row'
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
    
    # Define the data for each row - using same images for both rows
    row_data = [
        {
            'image_paths': [
                "umap_volcano_plot_replicate_set_966.png",
                "umap_volcano_plot_replicate_set_957.png", 
                "sigmoidal_curve_Calu-1.png"
            ],
            'vertical_text': "Cell Line 1"
        },
        {
            'image_paths': [
                "umap_volcano_plot_replicate_set_966.png",
                "umap_volcano_plot_replicate_set_957.png", 
                "sigmoidal_curve_Calu-1.png"
            ],
            'vertical_text': "Cell Line 2"
        }
    ]
    
    # Create rows
    rows = []
    for i, data in enumerate(row_data):
        row = create_umap_row(
            image_paths=data['image_paths'],
            vertical_text=data['vertical_text'],
            current_dir=current_dir,
            show_headers=(i == 0)  # Show headers only for the first row
        )
        rows.append(row)
    
    # Combine all rows with spacing optimized for PDF
    main_layout = pn.Column(
        *rows,
        sizing_mode="fixed",
        width=870,
        styles={'gap': '20px'}
    )
    
    return main_layout

def export_to_pdf_weasyprint(layout, output_path="umap_report.pdf"):
    """
    Export the Panel layout to PDF using weasyprint.
    """
    try:
        # Save as HTML first
        html_path = "umap_report.html"
        layout.save(html_path)
        
        # Convert HTML to PDF using weasyprint
        html_doc = HTML(filename=html_path)
        css = CSS(string='''
            @page {
                size: A4;
                margin: 0.5in;
            }
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: white;
            }
            .bk-root {
                font-family: Arial, sans-serif;
            }
            .bk-panel-models-layout-Column, .bk-panel-models-layout-Row {
                display: flex !important;
            }
            .bk-panel-models-layout-Row {
                flex-direction: row !important;
            }
            .bk-panel-models-layout-Column {
                flex-direction: column !important;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            /* Ensure vertical text renders properly */
            .vertical-text {
                writing-mode: vertical-rl !important;
                text-orientation: mixed !important;
                transform: rotate(180deg) !important;
            }
        ''')
        
        html_doc.write_pdf(output_path, stylesheets=[css])
        
        print(f"PDF successfully created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error exporting to PDF: {e}")
        print("Falling back to HTML export...")
        return html_path

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
    report.show()
    
    # Export to PDF
    pdf_path = export_to_pdf_weasyprint(report)
    
    return report, pdf_path

if __name__ == "__main__":
    report, pdf_path = main() 