import panel as pn
import os
from pathlib import Path
import weasyprint
from weasyprint import HTML, CSS

# Configure Panel
pn.extension('bootstrap')

def create_umap_layout():
    """
    Create a Panel layout with vertical "Cell Line" text and three images in a single light blue band.
    """
    # Get the current directory where the images are located
    current_dir = Path(__file__).parent
    
    # Define image paths
    umap_1_path = current_dir / "umap_volcano_plot_replicate_set_966.png"
    umap_2_path = current_dir / "umap_volcano_plot_replicate_set_957.png"
    sigmoidal_path = current_dir / "sigmoidal_curve_Calu-1.png"
    
    # Create image widgets with better sizing
    umap_1_img = pn.pane.PNG(str(umap_1_path), width=280, height=220)
    umap_2_img = pn.pane.PNG(str(umap_2_path), width=280, height=220)
    sigmoidal_img = pn.pane.PNG(str(sigmoidal_path), width=280, height=220)
    
    # Create vertical "Cell Line" text using HTML with CSS transform
    vertical_text = pn.pane.HTML(
        '''
        <div class="vertical-text" style="
            writing-mode: vertical-rl; 
            text-orientation: mixed; 
            transform: rotate(180deg);
            font-size: 24px; 
            font-weight: bold; 
            color: #2c3e50; 
            height: 220px; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            margin-right: 20px;
        ">
            Cell Line
        </div>
        ''',
        width=60,
        height=220,
        styles={'display': 'flex', 'align-items': 'center'}
    )
    
    # Create the images row with better spacing
    images_row = pn.Row(
        umap_1_img,
        umap_2_img,
        sigmoidal_img,
        width=900,
        height=220,
        styles={
            'gap': '25px', 
            'justify-content': 'center', 
            'align-items': 'center', 
            'flex': '1',
            'display': 'flex'
        }
    )
    
    # Create the main layout in a single light blue band
    main_layout = pn.Row(
        vertical_text,
        images_row,
        width=1100,
        height=240,
        styles={
            'gap': '20px', 
            'align-items': 'center', 
            'justify-content': 'center',
            'padding': '20px',
            'background-color': '#e3f2fd',  # Light blue color
            'border-radius': '12px',
            'box-shadow': '0 4px 8px rgba(0,0,0,0.1)',
            'border': '1px solid #bbdefb',
            'display': 'flex',
            'flex-direction': 'row',
            'min-height': '240px'
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