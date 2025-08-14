import panel as pn
import os
from pathlib import Path
import weasyprint
from weasyprint import HTML, CSS

# Configure Panel
pn.extension('bootstrap')

def create_umap_layout():
    """
    Create a Panel layout with vertical line, "Cell Line" text, and three images in a row.
    """
    # Get the current directory where the images are located
    current_dir = Path(__file__).parent
    
    # Define image paths
    umap_1_path = current_dir / "umap_volcano_plot_replicate_set_951.png"
    umap_2_path = current_dir / "umap_volcano_plot_replicate_set_957.png"
    sigmoidal_path = current_dir / "sigmoidal_curve_BxPC-3.png"
    
    # Create image widgets with better sizing
    umap_1_img = pn.pane.PNG(str(umap_1_path), width=280, height=220)
    umap_2_img = pn.pane.PNG(str(umap_2_path), width=280, height=220)
    sigmoidal_img = pn.pane.PNG(str(sigmoidal_path), width=280, height=220)
    
    # Create the vertical line using CSS
    vertical_line = pn.pane.HTML(
        '<div style="width: 4px; height: 120px; background-color: #2c3e50; margin-right: 15px; border-radius: 2px;"></div>',
        width=24,
        height=120
    )
    
    # Create "Cell Line" text with better styling
    cell_line_text = pn.pane.Markdown(
        "**Cell Line**",
        width=120,
        height=120,
        styles={
            'font-size': '20px', 
            'font-weight': 'bold', 
            'color': '#2c3e50',
            'display': 'flex', 
            'align-items': 'center',
            'margin-left': '10px'
        }
    )
    
    # Create the left section with vertical line and text
    left_section = pn.Column(
        vertical_line,
        cell_line_text,
        width=160,
        height=120,
        styles={'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'}
    )
    
    # Create the images row with better spacing
    images_row = pn.Row(
        umap_1_img,
        umap_2_img,
        sigmoidal_img,
        width=900,
        height=220,
        styles={'gap': '25px', 'justify-content': 'flex-start', 'align-items': 'center'}
    )
    
    # Create the main layout
    main_layout = pn.Row(
        left_section,
        images_row,
        width=1080,
        height=220,
        styles={
            'gap': '25px', 
            'align-items': 'center', 
            'padding': '25px',
            'background-color': '#f8f9fa',
            'border-radius': '8px',
            'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
        }
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
                margin: 1in;
            }
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }
            .bk-root {
                font-family: Arial, sans-serif;
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
        pn.pane.Markdown(
            "# UMAP Analysis Report", 
            styles={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '30px'}
        ),
        pn.pane.Markdown(
            "**Analysis Date:** " + str(Path().cwd().name),
            styles={'text-align': 'center', 'color': '#7f8c8d', 'margin-bottom': '20px'}
        ),
        layout,
        pn.pane.Markdown("---"),
        pn.pane.Markdown(
            "*Generated using Panel and WeasyPrint*",
            styles={'text-align': 'center', 'color': '#95a5a6', 'font-style': 'italic'}
        ),
        width=1200,
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