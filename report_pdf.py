import os
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak

GREEN=colors.HexColor('#183d35')
LIME=colors.HexColor('#e0f2ae')
MUTED=colors.HexColor('#718079')

def _text(value):
    return escape(value or '').replace('\n','<br/>')

def build_report_pdf(report,upload_folder):
    from io import BytesIO
    output=BytesIO();styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Brand',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=22,textColor=GREEN,spaceAfter=2))
    styles.add(ParagraphStyle(name='Tag',parent=styles['Normal'],fontSize=8,leading=11,textColor=MUTED,spaceAfter=18))
    styles.add(ParagraphStyle(name='Section',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=12,textColor=GREEN,spaceBefore=14,spaceAfter=7))
    styles.add(ParagraphStyle(name='BodySafe',parent=styles['BodyText'],fontSize=9.5,leading=14,textColor=colors.HexColor('#253c34')))
    styles.add(ParagraphStyle(name='PhotoCaption',parent=styles['Normal'],fontSize=8,leading=10,textColor=MUTED,alignment=TA_CENTER))
    doc=SimpleDocTemplate(output,pagesize=letter,rightMargin=.65*inch,leftMargin=.65*inch,topMargin=.55*inch,bottomMargin=.55*inch,title=report.title,author='Quimby Construction')
    story=[Paragraph('QUIMBY CONSTRUCTION',styles['Brand']),Paragraph('MASONRY &amp; CHIMNEY SERVICE · PROFESSIONAL JOB REPORT',styles['Tag'])]
    meta=[[Paragraph('<b>Report</b>',styles['BodySafe']),Paragraph(_text(report.title),styles['BodySafe'])],[Paragraph('<b>Customer</b>',styles['BodySafe']),Paragraph(_text(report.job.customer.name),styles['BodySafe'])],[Paragraph('<b>Property</b>',styles['BodySafe']),Paragraph(_text(report.job.customer.address or 'Not provided'),styles['BodySafe'])],[Paragraph('<b>Service / Job</b>',styles['BodySafe']),Paragraph(f'{_text(report.job.service)} · Job #{report.job.id}',styles['BodySafe'])],[Paragraph('<b>Report date</b>',styles['BodySafe']),Paragraph(_text(report.report_date),styles['BodySafe'])],[Paragraph('<b>Status</b>',styles['BodySafe']),Paragraph(_text(report.status),styles['BodySafe'])]]
    table=Table(meta,colWidths=[1.25*inch,5.2*inch]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),LIME),('TEXTCOLOR',(0,0),(0,-1),GREEN),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#dfe7df')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.extend([table,Spacer(1,10)])
    for title,value in [('Services performed',report.services_performed),('Inspection findings',report.findings),('Recommendations',report.recommendations)]:story.extend([Paragraph(title,styles['Section']),Paragraph(_text(value) or '—',styles['BodySafe'])])
    valid=[]
    for selected in report.report_photos:
        path=os.path.join(upload_folder,selected.photo.filename)
        if os.path.isfile(path):valid.append((selected,path))
    if valid:
        story.extend([PageBreak(),Paragraph('Job photographs',styles['Section'])]);cells=[]
        for selected,path in valid:
            try:
                image=Image(path,width=3.0*inch,height=2.15*inch,kind='proportional')
                caption=selected.caption or f'{selected.photo.category} · {selected.photo.original_name}'
                cells.append([image,Paragraph(_text(caption),styles['PhotoCaption'])])
            except Exception:continue
        for i in range(0,len(cells),2):
            row=[]
            for cell in cells[i:i+2]:row.append(Table([[cell[0]],[cell[1]]],colWidths=[3.15*inch]))
            if len(row)==1:row.append('')
            photos=Table([row],colWidths=[3.25*inch,3.25*inch]);photos.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.35,colors.HexColor('#dfe7df')),('INNERGRID',(0,0),(-1,-1),.35,colors.HexColor('#dfe7df')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([photos,Spacer(1,10)])
    story.extend([Spacer(1,18),Paragraph('Prepared by Quimby Construction',styles['Section']),Paragraph('This report documents observed conditions and completed work as of the report date. Contact Quimby Construction with questions about these findings or recommendations.',styles['BodySafe'])])
    doc.build(story,onFirstPage=_footer,onLaterPages=_footer);return output.getvalue()

def _footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#dfe7df'));canvas.line(.65*inch,.42*inch,7.85*inch,.42*inch);canvas.setFont('Helvetica',7);canvas.setFillColor(MUTED);canvas.drawString(.65*inch,.25*inch,'Quimby Construction · Job report');canvas.drawRightString(7.85*inch,.25*inch,f'Page {doc.page}');canvas.restoreState()
