"""Executive 1-Page PDF Report Generator for B2C Product Founders.

Uses ReportLab to generate an elegant, publication-ready single-page A4 PDF report
containing executive summary, KPI scorecards, embedded trend chart, strategic insights,
and actionable product recommendations. Full Unicode support (Cyrillic, Polish, Czech).
"""

import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Register Unicode TrueType Fonts (Bundled or System)
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
REGULAR_FONT = "DejaVuSans"
BOLD_FONT = "DejaVuSans-Bold"
OBLIQUE_FONT = "DejaVuSans-Oblique"

try:
    regular_path = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
    bold_path = os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf")
    oblique_path = os.path.join(FONTS_DIR, "DejaVuSans-Oblique.ttf")

    if not os.path.exists(regular_path):
        regular_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        oblique_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"

    if os.path.exists(regular_path):
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", oblique_path))
    else:
        REGULAR_FONT = "Helvetica"
        BOLD_FONT = "Helvetica-Bold"
        OBLIQUE_FONT = "Helvetica-Oblique"
except Exception:
    REGULAR_FONT = "Helvetica"
    BOLD_FONT = "Helvetica-Bold"
    OBLIQUE_FONT = "Helvetica-Oblique"


class ReportGenerator:
    """Builds a single-page A4 executive PDF report with full Unicode support."""

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.page_width, self.page_height = A4  # 595.27 x 841.89 pt

    def generate_pdf_report(
        self,
        topic: str,
        target_langs: List[str],
        period_str: str,
        kpis: Dict[str, Any],
        chart_image_path: Optional[str],
        strategic_findings: List[str],
        recommendation: str,
        limitations: List[str],
        output_filename: str = "market_insight_report.pdf",
    ) -> str:
        """Generate a strictly 1-page executive PDF report."""
        pdf_path = os.path.join(self.output_dir, output_filename)

        margin = 28
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=22,
            bottomMargin=18,
        )

        content_width = self.page_width - (2 * margin)  # ~539.27 pt
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "RepTitle",
            parent=styles["Normal"],
            fontName=BOLD_FONT,
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
        )
        subtitle_style = ParagraphStyle(
            "RepSubtitle",
            parent=styles["Normal"],
            fontName=REGULAR_FONT,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
        )
        section_heading = ParagraphStyle(
            "RepSecHeading",
            parent=styles["Normal"],
            fontName=BOLD_FONT,
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=2,
        )
        body_style = ParagraphStyle(
            "RepBody",
            parent=styles["Normal"],
            fontName=REGULAR_FONT,
            fontSize=7.5,
            leading=9.8,
            textColor=colors.HexColor("#334155"),
        )
        bullet_dot_style = ParagraphStyle(
            "RepDot",
            parent=styles["Normal"],
            fontName=BOLD_FONT,
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#2563EB"),
            alignment=1,
        )
        kpi_title_style = ParagraphStyle(
            "KPITitle",
            parent=styles["Normal"],
            fontName=BOLD_FONT,
            fontSize=6.8,
            leading=8,
            textColor=colors.HexColor("#64748B"),
            alignment=1,
        )
        kpi_value_style = ParagraphStyle(
            "KPIVal",
            parent=styles["Normal"],
            fontName=BOLD_FONT,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#1E3A8A"),
            alignment=1,
        )
        kpi_sub_style = ParagraphStyle(
            "KPISub",
            parent=styles["Normal"],
            fontName=REGULAR_FONT,
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#475569"),
            alignment=1,
        )
        rec_box_style = ParagraphStyle(
            "RecText",
            parent=styles["Normal"],
            fontName=REGULAR_FONT,
            fontSize=7.8,
            leading=10.2,
            textColor=colors.HexColor("#065F46"),
        )
        footnote_style = ParagraphStyle(
            "Footnote",
            parent=styles["Normal"],
            fontName=OBLIQUE_FONT,
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#94A3B8"),
        )

        elements = []

        # 1. Header Banner
        header_table_data = [
            [
                Paragraph("<b>WIKIPEDIA MARKET INSIGHTS</b>", ParagraphStyle("H1", fontName=BOLD_FONT, fontSize=8, textColor=colors.HexColor("#2563EB"))),
                Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", ParagraphStyle("HDate", fontName=REGULAR_FONT, fontSize=7.5, alignment=2, textColor=colors.HexColor("#64748B"))),
            ],
            [
                Paragraph(f"Topic Validation Report: <b>{topic}</b>", title_style),
                Paragraph(f"Languages: <b>{', '.join([l.upper() for l in target_langs])}</b> | Period: <b>{period_str}</b>", subtitle_style),
            ],
        ]
        t_header = Table(header_table_data, colWidths=[content_width * 0.7, content_width * 0.3])
        t_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 3))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=5, spaceBefore=1))

        # 2. KPI Scorecards (Clean 3-row Table)
        total_views_str = f"{kpis.get('total_views', 0):,}"
        yoy_str = f"{kpis.get('yoy_growth', 'N/A')}"
        if isinstance(kpis.get("yoy_growth"), (int, float)):
            yoy_str = f"{kpis.get('yoy_growth'):+.1f}%"
        trust_str = f"{kpis.get('trust_score', 0)}/100"
        trust_rating = kpis.get("trust_rating", "MODERATE")
        top_market = kpis.get("top_market", "N/A")

        col_w = content_width / 4.0
        kpi_data = [
            [
                Paragraph("TOTAL DEMAND", kpi_title_style),
                Paragraph("YOY GROWTH", kpi_title_style),
                Paragraph("TRUST SCORE", kpi_title_style),
                Paragraph("TOP PRIORITY", kpi_title_style),
            ],
            [
                Paragraph(total_views_str, kpi_value_style),
                Paragraph(yoy_str, kpi_value_style),
                Paragraph(trust_str, kpi_value_style),
                Paragraph(top_market, kpi_value_style),
            ],
            [
                Paragraph("Human Views", kpi_sub_style),
                Paragraph("12m vs Prior 12m", kpi_sub_style),
                Paragraph(trust_rating, kpi_sub_style),
                Paragraph("Relative Mindshare", kpi_sub_style),
            ],
        ]
        kpi_table = Table(kpi_data, colWidths=[col_w] * 4)
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (0, -1), 0.75, colors.HexColor("#E2E8F0")),
            ("BOX", (1, 0), (1, -1), 0.75, colors.HexColor("#E2E8F0")),
            ("BOX", (2, 0), (2, -1), 0.75, colors.HexColor("#E2E8F0")),
            ("BOX", (3, 0), (3, -1), 0.75, colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 6))

        # 3. Embedded Chart (Strictly preserves exact aspect ratio without squashing)
        if chart_image_path and os.path.exists(chart_image_path):
            try:
                from PIL import Image as PILImage
                with open(chart_image_path, "rb") as img_file:
                    img_bytes = img_file.read()
                with PILImage.open(io.BytesIO(img_bytes)) as pil_img:
                    orig_w, orig_h = pil_img.size
                aspect_ratio = orig_w / orig_h
                img_width = content_width
                img_height = content_width / aspect_ratio

                # Safe vertical cap to prevent any page spillover
                max_allowed_height = 270.0
                if img_height > max_allowed_height:
                    img_height = max_allowed_height
                    img_width = max_allowed_height * aspect_ratio

                chart_img = Image(io.BytesIO(img_bytes), width=img_width, height=img_height)
                chart_img.hAlign = "CENTER"
                elements.append(chart_img)
                elements.append(Spacer(1, 5))
            except Exception as e:
                # Fallback if image load fails
                pass

        # 4. Strategic Insights & Findings
        elements.append(Paragraph("KEY MARKET SIGNALS & FINDINGS", section_heading))
        bullet_rows = []
        for finding in strategic_findings[:4]:
            bullet_rows.append([
                Paragraph("•", bullet_dot_style),
                Paragraph(finding, body_style),
            ])
        if bullet_rows:
            t_bullets = Table(bullet_rows, colWidths=[10, content_width - 10])
            t_bullets.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(t_bullets)
            elements.append(Spacer(1, 4))

        # 5. Founder Recommendation Box
        elements.append(Paragraph("STRATEGIC PRODUCT RECOMMENDATION", section_heading))
        rec_box = Table(
            [[Paragraph(f"<b>Founder Takeaway:</b> {recommendation}", rec_box_style)]],
            colWidths=[content_width],
        )
        rec_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#A7F3D0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(rec_box)
        elements.append(Spacer(1, 4))

        # 6. Data Caveats & Limitations
        elements.append(Paragraph("ASSUMPTIONS & DATA LIMITATIONS", ParagraphStyle("LimH", fontName=BOLD_FONT, fontSize=6.8, textColor=colors.HexColor("#64748B"))))
        limit_text = " • ".join(limitations) if limitations else "Data filtered for human users; bot traffic and incomplete ongoing months excluded."
        elements.append(Paragraph(limit_text, footnote_style))

        # Build Document
        doc.build(elements)
        return pdf_path
