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
    Export the Panel layout to PDF using weasyprint with proper implementation.
    """
    try:
        print("=== WEASYPRINT PDF EXPORT ===")
        
        # Save as HTML first
        html_path = "umap_report.html"
        print(f"1. Saving Panel layout to HTML: {html_path}")
        layout.save(html_path)
        
        # Check if HTML file was created and has content
        if not os.path.exists(html_path):
            print("❌ ERROR: HTML file was not created")
            return None
            
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            print(f"2. HTML file size: {len(html_content)} characters")
            
            if len(html_content) < 100:
                print("❌ WARNING: HTML file seems too small")
                print(f"HTML content: {html_content[:500]}...")
                return None
            
            print("✅ HTML file looks valid")
        
        # Create a proper HTML document for WeasyPrint
        print("3. Creating enhanced HTML for WeasyPrint...")
        
        # Extract the body content from Panel's HTML
        # Panel saves HTML that needs to be embedded in a proper document
        enhanced_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UMAP Analysis Report</title>
            <style>
                @page {{
                    size: A4;
                    margin: 0.5in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: white;
                    line-height: 1.4;
                }}
                /* Panel-specific styles */
                .bk-root {{
                    font-family: Arial, sans-serif !important;
                }}
                .bk-panel-models-layout-Column, .bk-panel-models-layout-Row {{
                    display: flex !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                }}
                .bk-panel-models-layout-Row {{
                    flex-direction: row !important;
                }}
                .bk-panel-models-layout-Column {{
                    flex-direction: column !important;
                }}
                /* Image handling */
                img {{
                    max-width: 100% !important;
                    height: auto !important;
                    display: block !important;
                }}
                .bk-pane-png {{
                    display: block !important;
                }}
                /* Vertical text */
                .vertical-text {{
                    writing-mode: vertical-rl !important;
                    text-orientation: mixed !important;
                    transform: rotate(180deg) !important;
                }}
                /* Ensure all Panel elements are visible */
                .bk {{
                    display: block !important;
                }}
                /* Force proper sizing */
                .bk-panel-models-layout-Column, .bk-panel-models-layout-Row {{
                    width: auto !important;
                    height: auto !important;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Save the enhanced HTML
        enhanced_html_path = "umap_report_enhanced.html"
        with open(enhanced_html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
        print(f"4. Enhanced HTML saved: {enhanced_html_path}")
        
        # Convert HTML to PDF using weasyprint
        print("5. Converting to PDF with WeasyPrint...")
        
        # Use HTML from string instead of filename for better control
        html_doc = HTML(string=enhanced_html)
        
        # Create CSS for PDF - minimal and focused
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 0.5in;
            }
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: white;
            }
            .bk-root {
                font-family: Arial, sans-serif !important;
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
                max-width: 100% !important;
                height: auto !important;
            }
            .vertical-text {
                writing-mode: vertical-rl !important;
                text-orientation: mixed !important;
                transform: rotate(180deg) !important;
            }
        ''')
        
        print("6. Writing PDF...")
        html_doc.write_pdf(output_path, stylesheets=[pdf_css])
        
        # Check if PDF was created
        if os.path.exists(output_path):
            pdf_size = os.path.getsize(output_path)
            print(f"✅ PDF successfully created: {output_path} (size: {pdf_size} bytes)")
            
            if pdf_size < 1000:
                print("⚠️  WARNING: PDF file seems too small, may be empty")
                # Check if it's a valid PDF
                try:
                    with open(output_path, 'rb') as f:
                        pdf_content = f.read(100)
                        if b'%PDF' not in pdf_content:
                            print("❌ ERROR: File is not a valid PDF")
                            return None
                        else:
                            print("✅ File is a valid PDF")
                except Exception as e:
                    print(f"❌ Error checking PDF: {e}")
            
            return output_path
        else:
            print("❌ ERROR: PDF file was not created")
            return None
        
    except Exception as e:
        print(f"❌ Error exporting to PDF with WeasyPrint: {e}")
        import traceback
        traceback.print_exc()
        return None

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


    print("Attempting PDF export with enhanced WeasyPrint...")
    pdf_path = export_to_pdf_weasyprint(report)
    
    if pdf_path and pdf_path.endswith('.pdf'):
        print(f"✅ PDF successfully created: {pdf_path}")
    elif pdf_path and pdf_path.endswith('.html'):
        print(f"⚠️  PDF export failed, HTML saved: {pdf_path}")
    else:
        print("❌ PDF export completely failed")
    
    return report, pdf_path

if __name__ == "__main__":
    report, pdf_path = main() 