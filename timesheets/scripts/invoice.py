#!/usr/bin/env python3
"""
Invoice Generator — Creates professional PDF invoices from timesheet CSVs.

Usage:
    ./invoice.py --client "Acme" --rate 100 --csvs Acme/*.csv --from-name "Jane Doe" --invoice-num INV-2026-002
    ./invoice.py --client "Acme" --rate 100 --csvs Acme/*.csv --from-name "Jane Doe" --invoice-num INV-2026-002 --date 2026-03-12
    ./invoice.py --client "Globex" --rate 150 --csvs Globex/*.csv --from-name "Jane Doe" --from-email "jane@example.com" --invoice-num INV-2026-007

CSV format expected:
    Date,Hours,Description
    2026-03-02,1.0,Some work description
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from collections import OrderedDict
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle


# ── Colors ──────────────────────────────────────────────────────────────────
DARK        = HexColor('#1a1a2e')
ACCENT      = HexColor('#0f3460')
LIGHT_ACC   = HexColor('#e8edf3')
MEDIUM_GRAY = HexColor('#f7f7f7')
TEXT_DARK   = HexColor('#333333')
TEXT_LIGHT  = HexColor('#666666')
BORDER      = HexColor('#ddd')
WHITE       = HexColor('#ffffff')


def fmt_hours(hours):
    """One decimal for whole and half hours (2.0, 1.5), two for quarter hours (2.25)."""
    return f"{hours:,.2f}" if round(hours * 100) % 10 else f"{hours:,.1f}"


# Keep these formats in sync with archive.py.
def parse_date(date_str):
    """Try multiple date formats and return a datetime object."""
    date_str = date_str.strip().strip('"')
    for fmt in ('%Y-%m-%d', '%b %d %Y', '%b %d, %Y', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def load_entries(csv_paths):
    """Load and parse all CSV timesheet files into a sorted list of entries."""
    all_entries = []
    for path in csv_paths:
        if not os.path.isfile(path):
            print(f"Warning: skipping {path} (not found)", file=sys.stderr)
            continue
        with open(path, 'r') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                date_str = row.get('Date', '').strip()
                hours_str = row.get('Hours', '').strip()
                desc = row.get('Description', '').strip()
                if date_str.upper() in ('TOTAL', '') or hours_str == '':
                    continue
                # A skipped row would silently underbill, so bad rows stop the invoice.
                try:
                    hours = float(hours_str)
                except ValueError:
                    sys.exit(f"Error: {path}: bad hours '{hours_str}' on {date_str}")
                dt = parse_date(date_str)
                if dt is None:
                    sys.exit(f"Error: {path}: could not parse date '{date_str}'")
                all_entries.append({'date': dt, 'hours': hours, 'description': desc})

    all_entries.sort(key=lambda e: e['date'])
    return all_entries


def consolidate_entries(entries):
    """Merge same-day entries into single rows."""
    consolidated = OrderedDict()
    for e in entries:
        key = e['date'].strftime('%Y-%m-%d')
        if key not in consolidated:
            consolidated[key] = {'date': e['date'], 'hours': 0, 'descriptions': []}
        consolidated[key]['hours'] += e['hours']
        consolidated[key]['descriptions'].append(e['description'])

    result = []
    for val in consolidated.values():
        result.append({
            'date': val['date'],
            'hours': val['hours'],
            'description': '; '.join(val['descriptions']),
        })
    return result


def group_by_month(entries):
    """Group entries by month name."""
    monthly = OrderedDict()
    for e in entries:
        key = e['date'].strftime('%B %Y')
        if key not in monthly:
            monthly[key] = []
        monthly[key].append(e)
    return monthly


def build_invoice(
    entries,
    rate,
    client_name,
    from_name,
    from_email,
    invoice_num,
    invoice_date,
    output_path,
):
    """Generate the invoice PDF."""
    monthly = group_by_month(entries)
    total_hours = sum(e['hours'] for e in entries)
    total_amount = total_hours * rate

    # Date range label
    if entries:
        first = entries[0]['date']
        last = entries[-1]['date']
        if first.year == last.year:
            period_label = f"{first.strftime('%b %d')} – {last.strftime('%b %d, %Y')}"
        else:
            period_label = f"{first.strftime('%b %d, %Y')} – {last.strftime('%b %d, %Y')}"
    else:
        period_label = "N/A"

    CONTENT_W = letter[0] - 1.2 * inch

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.5*inch, bottomMargin=0.6*inch,
    )

    story = []

    # ── Styles ──────────────────────────────────────────────────────────────
    title_style     = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=28, textColor=DARK)
    label_style     = ParagraphStyle('L', fontName='Helvetica-Bold', fontSize=8, textColor=TEXT_LIGHT, spaceAfter=2)
    value_style     = ParagraphStyle('V', fontName='Helvetica', fontSize=10, textColor=TEXT_DARK, leading=14)
    bold_value      = ParagraphStyle('BV', fontName='Helvetica-Bold', fontSize=10, textColor=TEXT_DARK, leading=14)
    section_head    = ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=11, textColor=ACCENT, spaceAfter=4, spaceBefore=10)
    small_style     = ParagraphStyle('S', fontName='Helvetica', fontSize=8.5, textColor=TEXT_DARK, leading=12)
    small_bold      = ParagraphStyle('SB', fontName='Helvetica-Bold', fontSize=8.5, textColor=TEXT_DARK, leading=12)
    right_small     = ParagraphStyle('RS', fontName='Helvetica', fontSize=8.5, textColor=TEXT_DARK, alignment=TA_RIGHT, leading=12)
    right_small_b   = ParagraphStyle('RSB', fontName='Helvetica-Bold', fontSize=8.5, textColor=TEXT_DARK, alignment=TA_RIGHT, leading=12)
    month_style     = ParagraphStyle('M', fontName='Helvetica-Bold', fontSize=9, textColor=ACCENT, leading=13)
    date_style      = ParagraphStyle('D', fontName='Helvetica', fontSize=8.5, textColor=TEXT_LIGHT, leading=12)
    th_style        = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.5, textColor=TEXT_LIGHT)
    th_right        = ParagraphStyle('THR', fontName='Helvetica-Bold', fontSize=7.5, textColor=TEXT_LIGHT, alignment=TA_RIGHT)

    # ── Header ──────────────────────────────────────────────────────────────
    header_right_text = f'<b>Invoice #:</b> {escape(invoice_num)}<br/><b>Date:</b> {escape(invoice_date)}'
    header_data = [[
        Paragraph("INVOICE", title_style),
        Paragraph(header_right_text, ParagraphStyle(
            'HR', fontName='Helvetica', fontSize=9, textColor=TEXT_LIGHT, alignment=TA_RIGHT, leading=14)),
    ]]
    ht = Table(header_data, colWidths=[3.5*inch, CONTENT_W - 3.5*inch])
    ht.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(ht)
    story.append(Spacer(1, 20))

    # ── From / To ───────────────────────────────────────────────────────────
    from_text = escape(from_name)
    if from_email:
        from_text += f'<br/>{escape(from_email)}'

    ft_data = [
        [Paragraph("FROM", label_style), Paragraph("BILL TO", label_style)],
        [Paragraph(from_text, value_style), Paragraph(escape(client_name), bold_value)],
    ]
    ft = Table(ft_data, colWidths=[CONTENT_W / 2] * 2)
    ft.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(ft)
    story.append(Spacer(1, 16))

    # ── Summary box ─────────────────────────────────────────────────────────
    c_label = ParagraphStyle('CL', parent=label_style, alignment=TA_CENTER)
    c_bold  = ParagraphStyle('CB', parent=bold_value, alignment=TA_CENTER, fontSize=13)

    summary_data = [
        [Paragraph("Total Hours", c_label), Paragraph("Rate", c_label),
         Paragraph("Period", c_label), Paragraph("Amount Due", c_label)],
        [
            Paragraph(fmt_hours(total_hours), c_bold),
            Paragraph(f"${rate:,.2f}/hr", c_bold),
            Paragraph(period_label, ParagraphStyle('CP', parent=bold_value, alignment=TA_CENTER, fontSize=11)),
            Paragraph(f"${total_amount:,.2f}", ParagraphStyle(
                'CA', fontName='Helvetica-Bold', fontSize=16, textColor=ACCENT, alignment=TA_CENTER)),
        ],
    ]
    # The period label is the longest value, so its column gets the extra width.
    st = Table(summary_data, colWidths=[1.4*inch, 1.6*inch, CONTENT_W - 4.8*inch, 1.8*inch])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_ACC),
        ('ROUNDEDCORNERS', [6,6,6,6]),
        ('TOPPADDING', (0,0), (-1,0), 8), ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('TOPPADDING', (0,1), (-1,1), 2), ('BOTTOMPADDING', (0,1), (-1,1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(st)
    story.append(Spacer(1, 20))

    # ── Detailed line items ─────────────────────────────────────────────────
    story.append(Paragraph("DETAILED TIME LOG", section_head))
    story.append(Spacer(1, 4))

    table_data = [[
        Paragraph("DATE", th_style), Paragraph("DESCRIPTION", th_style),
        Paragraph("HOURS", th_right),
    ]]

    for month_name, month_entries in monthly.items():
        mh = sum(e['hours'] for e in month_entries)
        table_data.append([
            Paragraph(month_name, month_style), '',
            Paragraph(fmt_hours(mh), ParagraphStyle('', parent=right_small_b, textColor=ACCENT)),
        ])
        for e in month_entries:
            table_data.append([
                Paragraph(e['date'].strftime('%b %d'), date_style),
                Paragraph(escape(e['description']), small_style),
                Paragraph(fmt_hours(e['hours']), right_small),
            ])

    # Totals row
    table_data.append([
        Paragraph("<b>TOTAL</b>", ParagraphStyle('', parent=small_bold, fontSize=10)),
        Paragraph(f"${total_amount:,.2f}", ParagraphStyle('', parent=right_small_b, fontSize=10, textColor=ACCENT)),
        Paragraph(fmt_hours(total_hours), ParagraphStyle('', parent=right_small_b, fontSize=10)),
    ])

    col_widths = [0.7*inch, CONTENT_W - 0.7*inch - 0.8*inch, 0.8*inch]
    dt = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('LINEBELOW', (0,0), (-1,0), 1, BORDER),
        ('TOPPADDING', (0,0), (-1,0), 4),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE', (0,-1), (-1,-1), 1, DARK),
        ('TOPPADDING', (0,-1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
    ]

    row_i = 1
    for month_name, month_entries in monthly.items():
        style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), LIGHT_ACC))
        style_cmds.append(('SPAN', (0, row_i), (1, row_i)))
        style_cmds.append(('TOPPADDING', (0, row_i), (-1, row_i), 6))
        style_cmds.append(('BOTTOMPADDING', (0, row_i), (-1, row_i), 5))
        row_i += 1
        for j, _ in enumerate(month_entries):
            bg = WHITE if j % 2 == 0 else MEDIUM_GRAY
            style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), bg))
            row_i += 1

    dt.setStyle(TableStyle(style_cmds))
    story.append(dt)

    doc.build(story)
    return total_hours, total_amount


def main():
    parser = argparse.ArgumentParser(description='Generate a PDF invoice from timesheet CSVs.')
    parser.add_argument('--client', required=True, help='Client/company name for "Bill To"')
    parser.add_argument('--rate', type=float, required=True, help='Hourly rate in dollars')
    parser.add_argument('--csvs', nargs='+', required=True, help='One or more CSV timesheet files (glob-friendly)')
    parser.add_argument('--output', '-o', help='Output PDF path (default: Invoice_<client>_<date>.pdf)')
    parser.add_argument('--invoice-num', required=True, help='Invoice number, e.g. INV-2026-003')
    parser.add_argument('--date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), default=datetime.now(),
                        help='Invoice date as YYYY-MM-DD (default: today)')
    parser.add_argument('--from-name', required=True, help='Your name')
    parser.add_argument('--from-email', help='Your email')
    parser.add_argument('--no-consolidate', action='store_true', help='Keep separate rows for same-day entries')

    args = parser.parse_args()

    client_safe = args.client.replace(' ', '_')
    output_path = args.output or f"Invoice_{client_safe}_{args.date.strftime('%Y%m%d')}.pdf"

    # Load & process
    entries = load_entries(args.csvs)
    if not entries:
        print("Error: no valid timesheet entries found.", file=sys.stderr)
        sys.exit(1)

    if not args.no_consolidate:
        entries = consolidate_entries(entries)

    total_hours, total_amount = build_invoice(
        entries=entries,
        rate=args.rate,
        client_name=args.client,
        from_name=args.from_name,
        from_email=args.from_email,
        invoice_num=args.invoice_num,
        invoice_date=args.date.strftime('%B %d, %Y'),
        output_path=output_path,
    )

    print(f"Invoice generated: {output_path}")
    print(f"  {len(entries)} line items  |  {fmt_hours(total_hours)} hours  |  ${total_amount:,.2f}")


if __name__ == '__main__':
    main()
