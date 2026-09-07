import io
import os
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_district_pdf(df, target_district="All Odisha"):
    """
    Generates a formal executive hydrogeological PDF dossier for a selected district or state.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=0
    )
    
    heading2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    
    table_text_style = ParagraphStyle(
        "TableText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []
    
    # Filter dataset
    if target_district != "All Odisha" and "District" in df.columns:
        sub_df = df[df["District"] == target_district].copy()
    else:
        sub_df = df.copy()
        
    tot_wells = len(sub_df)
    danger_wells = (sub_df["Status"] == "Danger").sum() if "Status" in sub_df.columns else 0
    fe_exceed = (sub_df["Fe"] > 1.0).sum() if "Fe" in sub_df.columns else 0
    no3_exceed = (sub_df["NO3"] > 45.0).sum() if "NO3" in sub_df.columns else 0
    f_exceed = (sub_df["F"] > 1.5).sum() if "F" in sub_df.columns else 0
    
    # Header Section
    story.append(Paragraph(f"STATE GROUNDWATER HYDROGEOLOGICAL DOSSIER", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>{target_district.upper()}</b> Groundwater Assessment & Potability Dossier", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Groundwater Resources, BIS IS 10500:2012 Compliance & Jal Jeevan Mission Engineering Guidance", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=14))
    
    # 1. Executive Summary Table
    story.append(Paragraph("1. Executive Summary & Quality Index Overview", heading2_style))
    story.append(Paragraph(
        f"This hydrogeological dossier evaluates <b>{tot_wells:,} groundwater monitoring stations</b> across {target_district}. "
        f"A total of <b>{danger_wells} monitoring stations ({danger_wells/tot_wells*100:.1f}%)</b> currently exceed permissible Indian Drinking Water Standards (BIS IS 10500:2012).",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    kpi_data = [
        [Paragraph("<b>Metric Parameter</b>", table_header_style), Paragraph("<b>Count / Value</b>", table_header_style), Paragraph("<b>Status Assessment</b>", table_header_style)],
        [Paragraph("Total Monitored Wells", table_text_style), Paragraph(f"<b>{tot_wells}</b>", table_text_style), Paragraph("Active Surveillance Network", table_text_style)],
        [Paragraph("Critical Danger Wells", table_text_style), Paragraph(f"<font color='#dc2626'><b>{danger_wells} ({danger_wells/tot_wells*100:.1f}%)</b></font>", table_text_style), Paragraph("Immediate Intervention Required", table_text_style)],
        [Paragraph("Iron Contamination (Fe > 1.0 mg/L)", table_text_style), Paragraph(f"<b>{fe_exceed} wells</b>", table_text_style), Paragraph("High Turbidity / Anaerobic Alluvium", table_text_style)],
        [Paragraph("Nitrate Contamination (NO3 > 45 mg/L)", table_text_style), Paragraph(f"<b>{no3_exceed} wells</b>", table_text_style), Paragraph("Non-Point Agricultural / Septic Leaching", table_text_style)],
        [Paragraph("Fluoride Contamination (F > 1.5 mg/L)", table_text_style), Paragraph(f"<b>{f_exceed} wells</b>", table_text_style), Paragraph("Geogenic Granitic / Crystalline Bedrock", table_text_style)]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[200, 140, 190])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))
    
    # 2. Critical Action Stations Table
    story.append(Paragraph("2. Critical Action Stations (Immediate Water Purification Priority)", heading2_style))
    danger_df = sub_df[sub_df["Status"] == "Danger"].head(10)
    
    if not danger_df.empty:
        action_data = [
            [
                Paragraph("<b>Station No</b>", table_header_style),
                Paragraph("<b>Location / Block</b>", table_header_style),
                Paragraph("<b>Basin / Aquifer</b>", table_header_style),
                Paragraph("<b>Fe (mg/L)</b>", table_header_style),
                Paragraph("<b>NO3 (mg/L)</b>", table_header_style),
                Paragraph("<b>F (mg/L)</b>", table_header_style)
            ]
        ]
        
        for _, row in danger_df.iterrows():
            action_data.append([
                Paragraph(str(row.get("Station_No", "N/A")), table_text_style),
                Paragraph(f"{row.get('Location', '')} ({row.get('Block', '')})", table_text_style),
                Paragraph(f"{row.get('River_Basin', 'N/A')}<br/><i>{row.get('Aquifer_System', 'N/A')}</i>", table_text_style),
                Paragraph(f"<font color='#dc2626'><b>{row.get('Fe', 0):.2f}</b></font>" if row.get('Fe', 0) > 1.0 else f"{row.get('Fe', 0):.2f}", table_text_style),
                Paragraph(f"<font color='#dc2626'><b>{row.get('NO3', 0):.1f}</b></font>" if row.get('NO3', 0) > 45.0 else f"{row.get('NO3', 0):.1f}", table_text_style),
                Paragraph(f"<font color='#dc2626'><b>{row.get('F', 0):.2f}</b></font>" if row.get('F', 0) > 1.5 else f"{row.get('F', 0):.2f}", table_text_style)
            ])
            
        action_table = Table(action_data, colWidths=[80, 160, 140, 50, 50, 50])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(action_table)
    else:
        story.append(Paragraph("✅ No critical chemical exceedance stations detected in this selection.", body_style))
        
    story.append(Spacer(1, 14))
    
    # 3. Engineering & Treatment Guidance
    story.append(Paragraph("3. Jal Jeevan Mission (JJM) Engineering Action Guidance", heading2_style))
    recommendations = [
        "<b>Iron Removal Plants (IRPs):</b> Deploy multi-media oxidation-filtration IRP units at high-iron tubewells prior to distribution in rural supply networks.",
        "<b>Nitrate Leaching Safeguards:</b> Implement 30-meter sanitary protection perimeters around drinking water borewells to prevent contamination from pit latrines and paddy fertilizers.",
        "<b>Pipe Material Selection:</b> For scale-forming alkaline groundwater, specify cement-lined ductile iron or HDPE piping to resist calcium carbonate encrustation.",
        "<b>Managed Aquifer Recharge (MAR):</b> Construct check dams and percolation pits in upstream crystalline zones to dilute bedrock mineral concentrations."
    ]
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", body_style))
        story.append(Spacer(1, 3))
        
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
