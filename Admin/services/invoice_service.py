"""
Invoice PDF generator – used by both admin and user order detail views.
"""

import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


def generate_invoice_pdf(order):
    """
    Build a PDF invoice for `order` and return a BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    brown = colors.HexColor('#6B3E26')
    cream = colors.HexColor('#F7F4ED')
    light = colors.HexColor('#FBF9F4')
    border_color = colors.HexColor('#E7E2D9')

    title_style = ParagraphStyle('brand', fontSize=28, textColor=brown,
                                  fontName='Helvetica-Bold', spaceAfter=2)
    sub_style   = ParagraphStyle('sub',   fontSize=9,  textColor=colors.grey)
    label_style = ParagraphStyle('label', fontSize=9,  fontName='Helvetica-Bold',
                                  textColor=colors.HexColor('#374151'))
    value_style = ParagraphStyle('value', fontSize=9,  textColor=colors.HexColor('#6B7280'))
    section_style = ParagraphStyle('section', fontSize=11, fontName='Helvetica-Bold',
                                    textColor=brown, spaceBefore=12, spaceAfter=6)
    right_style = ParagraphStyle('right', fontSize=9, alignment=TA_RIGHT,
                                  textColor=colors.HexColor('#374151'))

    thin_side  = colors.HexColor('#E7E2D9')

    def cell_border():
        from reportlab.lib.styles import getSampleStyleSheet
        return colors.HexColor('#E7E2D9')

    elements = []

    # ── Brand header ──────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph('VARA', title_style),
            Paragraph(
                f'<b>INVOICE</b><br/>'
                f'<font size=9 color=grey>#{order.id:05d}</font>',
                ParagraphStyle('inv_no', fontSize=18, fontName='Helvetica-Bold',
                                textColor=brown, alignment=TA_RIGHT)
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Paragraph('Fine Art · Paintings · VARA Store', sub_style))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(HRFlowable(width='100%', thickness=1.5, color=brown, spaceAfter=8))

    # ── Invoice meta + Customer ───────────────────────────────────────────────
    address_str = '—'
    if order.address:
        a = order.address
        address_str = f'{a.street_address}, {a.city}, {a.state} – {a.pincode}'

    meta_data = [
        [
            # Left: Invoice info
            Table([
                [Paragraph('Invoice Date', label_style),
                 Paragraph(order.created_at.strftime('%B %d, %Y'), value_style)],
                [Paragraph('Order Status', label_style),
                 Paragraph(order.status, value_style)],
                [Paragraph('Payment', label_style),
                 Paragraph(order.payment_method, value_style)],
                [Paragraph('Pmt Status', label_style),
                 Paragraph(order.payment_status, value_style)],
            ], colWidths=[3*cm, 5.5*cm],
               style=TableStyle([('TOPPADDING', (0,0),(-1,-1), 3),
                                 ('BOTTOMPADDING', (0,0),(-1,-1), 3)])),
            # Right: Customer info
            Table([
                [Paragraph('Bill To', ParagraphStyle('bt', fontSize=10,
                             fontName='Helvetica-Bold', textColor=brown))],
                [Paragraph(f'{order.user.first_name} {order.user.last_name}', label_style)],
                [Paragraph(order.user.email, value_style)],
                [Paragraph(address_str, value_style)],
            ], colWidths=[9.5*cm],
               style=TableStyle([('TOPPADDING', (0,0),(-1,-1), 2),
                                 ('BOTTOMPADDING', (0,0),(-1,-1), 2)])),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[9*cm, 9.5*cm])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0),(-1,-1), 'TOP')]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=border_color, spaceAfter=6))

    # ── Items table ───────────────────────────────────────────────────────────
    elements.append(Paragraph('Order Items', section_style))

    item_headers = ['#', 'Product', 'Variant', 'Qty', 'Unit Price', 'Subtotal']
    rows = [item_headers]
    for i, item in enumerate(order.items.select_related('product', 'variant').all(), 1):
        rows.append([
            str(i),
            item.product.title,
            item.variant.variant_type if item.variant else '—',
            str(item.quantity),
            f'₹{item.price:.2f}',
            f'₹{item.get_subtotal():.2f}',
        ])

    item_table = Table(rows, colWidths=[1*cm, 6.5*cm, 3*cm, 1.5*cm, 3*cm, 3.5*cm],
                       repeatRows=1)
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brown),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 0.4*cm))

    # ── Totals ────────────────────────────────────────────────────────────────
    items_subtotal = sum(item.get_subtotal() for item in order.items.all())

    totals_data = []
    totals_data.append(['Items Subtotal', f'₹{items_subtotal:.2f}'])
    if order.discount_amount:
        totals_data.append(['Coupon Discount', f'– ₹{order.discount_amount:.2f}'])
    if order.delivery_charge:
        totals_data.append(['Delivery Charge', f'₹{order.delivery_charge:.2f}'])
    totals_data.append(['', ''])   # spacer row
    totals_data.append(['TOTAL PAID', f'₹{order.total_amount:.2f}'])

    tot_table = Table(totals_data, colWidths=[14*cm, 4.5*cm])
    tot_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, len(totals_data)-1), (-1, len(totals_data)-1), 1, brown),
        ('FONTNAME', (0, len(totals_data)-1), (-1, len(totals_data)-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, len(totals_data)-1), (-1, len(totals_data)-1), brown),
        ('FONTSIZE', (0, len(totals_data)-1), (-1, len(totals_data)-1), 11),
    ])
    tot_table.setStyle(tot_style)
    elements.append(tot_table)

    elements.append(HRFlowable(width='100%', thickness=0.5, color=border_color, spaceBefore=10, spaceAfter=8))
    elements.append(Paragraph('Thank you for shopping with VARA.',
                               ParagraphStyle('footer', fontSize=9, textColor=colors.grey,
                                               alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer
