import panel as pn
import os
from pathlib import Path
import asyncio
import tempfile
import base64
from io import BytesIO

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

async def export_to_pdf_playwright(layout, output_path="umap_report.pdf"):
    """
    Export the Panel layout to PDF using Playwright to render the actual HTML.
    This preserves the exact visual appearance of the Panel layout.
    """
    try:
        print("=== PLAYWRIGHT PDF EXPORT ===")
        
        # Save Panel layout to HTML
        html_path = "umap_report_temp.html"
        print(f"1. Saving Panel layout to HTML: {html_path}")
        layout.save(html_path)
        
        if not os.path.exists(html_path):
            print("❌ ERROR: HTML file was not created")
            return None
        
        # Read the HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"2. HTML file size: {len(html_content)} characters")
        
        # Create enhanced HTML with proper styling for PDF
        enhanced_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UMAP Analysis Report</title>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 0.5in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: white;
                    line-height: 1.4;
                }}
                /* Ensure Panel elements are visible */
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
                /* Print-specific styles */
                @media print {{
                    body {{
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }}
                    .vertical-text {{
                        background-color: #e3f2fd !important;
                    }}
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Save enhanced HTML
        enhanced_html_path = "umap_report_enhanced.html"
        with open(enhanced_html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
        print(f"3. Enhanced HTML saved: {enhanced_html_path}")
        
        # Use Playwright to render HTML and generate PDF
        print("4. Starting Playwright browser...")
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                # Set viewport for better rendering
                await page.set_viewport_size({"width": 1200, "height": 800})
                
                # Load the HTML content
                print("5. Loading HTML content...")
                await page.set_content(enhanced_html)
                
                # Wait for content to load
                await page.wait_for_load_state('networkidle')
                
                # Generate PDF
                print("6. Generating PDF...")
                await page.pdf(
                    path=output_path,
                    format='A4',
                    landscape=True,
                    margin={
                        'top': '0.5in',
                        'right': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.5in'
                    },
                    print_background=True,
                    prefer_css_page_size=True
                )
                
                await browser.close()
                
        except ImportError:
            print("❌ Playwright not available - trying alternative methods")
            return None
        
        # Check if PDF was created
        if os.path.exists(output_path):
            pdf_size = os.path.getsize(output_path)
            print(f"✅ PDF successfully created with Playwright: {output_path} (size: {pdf_size} bytes)")
            
            if pdf_size < 1000:
                print("⚠️  WARNING: PDF file seems too small, may be empty")
                return None
            
            return output_path
        else:
            print("❌ ERROR: PDF file was not created")
            return None
        
    except Exception as e:
        print(f"❌ Error exporting to PDF with Playwright: {e}")
        import traceback
        traceback.print_exc()
        return None

def export_to_pdf_playwright_sync(layout, output_path="umap_report.pdf"):
    """
    Synchronous wrapper for Playwright PDF export.
    """
    try:
        return asyncio.run(export_to_pdf_playwright(layout, output_path))
    except Exception as e:
        print(f"❌ Error in Playwright sync wrapper: {e}")
        return None

def export_to_html(layout, output_path="umap_report.html"):
    """
    Export the Panel layout to HTML as a fallback option.
    """
    try:
        print("=== HTML EXPORT ===")
        layout.save(output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ HTML successfully created: {output_path} (size: {file_size} bytes)")
            return output_path
        else:
            print("❌ HTML file was not created")
            return None
            
    except Exception as e:
        print(f"❌ Error exporting to HTML: {e}")
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
    # report.show()

    print("Attempting PDF export with Playwright...")
    pdf_path = export_to_pdf_playwright_sync(report)
    
    if pdf_path and pdf_path.endswith('.pdf'):
        print(f"✅ PDF successfully created: {pdf_path}")
    else:
        print("❌ PDF export failed")
        print("🔄 Attempting HTML export as fallback...")
        html_path = export_to_html(report)
        if html_path:
            print(f"✅ HTML export successful: {html_path}")
    
    return report, pdf_path

if __name__ == "__main__":
    report, pdf_path = main() 