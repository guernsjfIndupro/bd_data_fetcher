"""
PDF Exporter Module for Panel Layouts

This module provides a reusable interface for converting Panel HTML layouts to PDF
using Playwright. It preserves the exact visual appearance of Panel layouts including
styling, images, and layout structure.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Union
import panel as pn


class PanelPDFExporter:
    """
    A reusable class for exporting Panel layouts to PDF using Playwright.
    
    This class handles the conversion of Panel HTML layouts to high-quality PDFs
    while preserving the exact visual appearance, styling, and layout structure.
    """
    
    def __init__(self, 
                 page_size: str = "A4",
                 orientation: str = "landscape",
                 margin: float = 0.5,
                 print_background: bool = True):
        """
        Initialize the PDF exporter.
        
        Args:
            page_size: PDF page size (e.g., "A4", "Letter")
            orientation: Page orientation ("portrait" or "landscape")
            margin: Margin size in inches
            print_background: Whether to include background colors and images
        """
        self.page_size = page_size
        self.orientation = orientation
        self.margin = margin
        self.print_background = print_background
        
    async def _export_to_pdf_async(self, 
                                  layout: pn.layout.Panel,
                                  output_path: str,
                                  title: Optional[str] = None) -> Optional[str]:
        """
        Asynchronously export a Panel layout to PDF using Playwright.
        
        Args:
            layout: Panel layout to export
            output_path: Path where the PDF should be saved
            title: Optional title for the PDF document
            
        Returns:
            Path to the generated PDF file, or None if failed
        """
        try:
            print("=== PLAYWRIGHT PDF EXPORT ===")
            
            # Save Panel layout to temporary HTML
            temp_html_path = f"{output_path}_temp.html"
            print(f"1. Saving Panel layout to HTML: {temp_html_path}")
            layout.save(temp_html_path)
            
            if not os.path.exists(temp_html_path):
                print("❌ ERROR: HTML file was not created")
                return None
            
            # Read the HTML content
            with open(temp_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"2. HTML file size: {len(html_content)} characters")
            
            # Create enhanced HTML with proper styling for PDF
            enhanced_html = self._create_enhanced_html(html_content, title)
            
            # Save enhanced HTML
            enhanced_html_path = f"{output_path}_enhanced.html"
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
                        format=self.page_size,
                        landscape=(self.orientation == "landscape"),
                        margin={
                            'top': f'{self.margin}in',
                            'right': f'{self.margin}in',
                            'bottom': f'{self.margin}in',
                            'left': f'{self.margin}in'
                        },
                        print_background=self.print_background,
                        prefer_css_page_size=True
                    )
                    
                    await browser.close()
                    
            except ImportError:
                print("❌ Playwright not available")
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
    
    def _create_enhanced_html(self, html_content: str, title: Optional[str] = None) -> str:
        """
        Create enhanced HTML with proper styling for PDF generation.
        
        Args:
            html_content: Original Panel HTML content
            title: Optional title for the document
            
        Returns:
            Enhanced HTML string with PDF-specific styling
        """
        doc_title = title or "Panel Layout Report"
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{doc_title}</title>
            <style>
                @page {{
                    size: {self.page_size} {self.orientation};
                    margin: {self.margin}in;
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
    
    def export_to_pdf(self, 
                     layout: pn.layout.Panel,
                     output_path: str,
                     title: Optional[str] = None) -> Optional[str]:
        """
        Export a Panel layout to PDF.
        
        Args:
            layout: Panel layout to export
            output_path: Path where the PDF should be saved
            title: Optional title for the PDF document
            
        Returns:
            Path to the generated PDF file, or None if failed
        """
        try:
            return asyncio.run(self._export_to_pdf_async(layout, output_path, title))
        except Exception as e:
            print(f"❌ Error in PDF export: {e}")
            return None
    
    def export_to_html(self, 
                      layout: pn.layout.Panel,
                      output_path: str) -> Optional[str]:
        """
        Export a Panel layout to HTML as a fallback option.
        
        Args:
            layout: Panel layout to export
            output_path: Path where the HTML should be saved
            
        Returns:
            Path to the generated HTML file, or None if failed
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


def export_panel_to_pdf(layout: pn.layout.Panel,
                       output_path: str,
                       title: Optional[str] = None,
                       page_size: str = "A4",
                       orientation: str = "landscape",
                       margin: float = 0.5,
                       print_background: bool = True) -> Optional[str]:
    """
    Convenience function to export a Panel layout to PDF.
    
    Args:
        layout: Panel layout to export
        output_path: Path where the PDF should be saved
        title: Optional title for the PDF document
        page_size: PDF page size (e.g., "A4", "Letter")
        orientation: Page orientation ("portrait" or "landscape")
        margin: Margin size in inches
        print_background: Whether to include background colors and images
        
    Returns:
        Path to the generated PDF file, or None if failed
    """
    exporter = PanelPDFExporter(
        page_size=page_size,
        orientation=orientation,
        margin=margin,
        print_background=print_background
    )
    return exporter.export_to_pdf(layout, output_path, title)


def export_panel_to_html(layout: pn.layout.Panel,
                        output_path: str) -> Optional[str]:
    """
    Convenience function to export a Panel layout to HTML.
    
    Args:
        layout: Panel layout to export
        output_path: Path where the HTML should be saved
        
    Returns:
        Path to the generated HTML file, or None if failed
    """
    exporter = PanelPDFExporter()
    return exporter.export_to_html(layout, output_path) 