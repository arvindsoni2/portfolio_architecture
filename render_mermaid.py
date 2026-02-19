"""
render_mermaid.py — Render a .mmd file to PNG using Playwright + local Mermaid.js
Usage: python3 render_mermaid.py input.mmd output.png
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

MERMAID_JS = "/home/claude/.npm-global/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/mermaid/dist/mermaid.min.js"

def render_mermaid(mmd_path: str, png_path: str):
    mmd_src = Path(mmd_path).read_text()

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ background: #FFFFFF; margin: 0; padding: 32px; font-family: Arial, sans-serif; display: inline-block; }}
    .mermaid {{ display: block; }}
    .mermaid svg {{ max-width: none !important; }}
  </style>
</head>
<body>
  <div class="mermaid">
{mmd_src}
  </div>
  <script src="file://{MERMAID_JS}"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      flowchart: {{ useMaxWidth: false, htmlLabels: true }},
      themeVariables: {{
        primaryColor: '#DEEAF1',
        primaryTextColor: '#1A1A1A',
        primaryBorderColor: '#2E75B6',
        lineColor: '#2E75B6',
        secondaryColor: '#F0F4F8',
        tertiaryColor: '#EAF3EA',
        background: '#FFFFFF',
        fontSize: '14px',
        fontFamily: 'Arial'
      }}
    }});
    mermaid.run().then(function() {{
      document.body.dataset.ready = '1';
    }});
  </script>
</body>
</html>"""

    html_path = png_path.replace('.png', '_tmp.html')
    Path(html_path).write_text(html)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Large viewport to capture full diagram height at high DPI
        ctx = browser.new_context(viewport={"width": 3000, "height": 4000}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(f"file://{Path(html_path).absolute()}")
        page.wait_for_function("document.body.dataset.ready === '1'", timeout=15000)
        page.wait_for_timeout(600)

        # Get bounding box of the rendered SVG
        svg = page.query_selector('svg')
        if svg:
            bbox = svg.bounding_box()
        else:
            bbox = {"x": 0, "y": 0, "width": 1200, "height": 800}

        pad = 32
        # page.screenshot uses CSS pixels; device_scale_factor doubles the physical pixels
        page.screenshot(
            path=png_path,
            clip={
                "x":      max(0, bbox["x"] - pad),
                "y":      max(0, bbox["y"] - pad),
                "width":  bbox["width"]  + pad * 2,
                "height": bbox["height"] + pad * 2,
            }
        )
        browser.close()

    Path(html_path).unlink()
    print(f"Rendered: {png_path}  (SVG: {int(bbox['width'])}x{int(bbox['height'])} CSS px)")

if __name__ == "__main__":
    render_mermaid(sys.argv[1], sys.argv[2])
