from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import textwrap
import os
import logging

logger = logging.getLogger(__name__)


def _find_system_font(preferred_names=None):
    """Try to locate a TTF font on the system from a list of preferred names."""
    if preferred_names is None:
        preferred_names = [
            "DejaVuSans.ttf",
            "DejaVuSans.ttf",  # common on Linux
            "Arial.ttf",
            "arial.ttf",
            "Times New Roman.ttf",
            "Verdana.ttf",
        ]

    # Common Windows fonts directory
    candidates = []
    if os.name == 'nt':
        win_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        for name in preferred_names:
            candidates.append(os.path.join(win_fonts, name))
    else:
        # Check common Unix locations
        for loc in ['/usr/share/fonts/truetype', '/usr/local/share/fonts', '/usr/share/fonts']:
            for name in preferred_names:
                candidates.append(os.path.join(loc, name))

    # Also check current working directory
    for name in preferred_names:
        candidates.append(os.path.join(os.getcwd(), name))

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def text_to_pdf(text: str, output_path: str, title: str = "Daily Report", font_path: str = None):
    """Create a UTF-8-capable PDF using ReportLab and a TTF font.

    If `font_path` is not provided, the function will try to auto-detect a suitable TTF.
    """
    # Determine font to use
    if font_path and os.path.exists(font_path):
        chosen_font = font_path
    else:
        chosen_font = _find_system_font()

    if not chosen_font:
        logger.warning("No TTF font found on system; falling back to built-in fonts which may not support all UTF-8 characters.")
        font_name = 'Helvetica'
    else:
        font_name = 'CustomUTF8'
        try:
            pdfmetrics.registerFont(TTFont(font_name, chosen_font))
        except Exception as e:
            logger.error(f"Failed to register TTF font {chosen_font}: {e}")
            font_name = 'Helvetica'

    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont(font_name, 16)
    margin_left = 20 * mm
    y = height - 20 * mm
    c.drawString(margin_left, y, title)
    y -= 8 * mm

    c.setFont(font_name, 10)
    wrapper = textwrap.TextWrapper(width=100)

    for paragraph in text.split('\n'):
        if not paragraph.strip():
            y -= 4 * mm
            continue
        lines = wrapper.wrap(paragraph)
        for line in lines:
            if y < 20 * mm:
                c.showPage()
                c.setFont(font_name, 10)
                y = height - 20 * mm
            c.drawString(margin_left, y, line)
            y -= 5 * mm

    c.save()
