"""Create the fictional demo policies. Requires reportlab."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parent
POLICIES = {
    'employee-leave-policy.pdf': ('Employee Leave Policy', [
        [('Annual leave', 'Full-time employees receive 20 days of paid annual leave each calendar year. Annual leave is prorated for employees who join during the year.'),
         ('Requesting time off', 'Submit annual leave requests in the HR portal at least 10 business days before the first day off. Your manager must approve the request before you book travel.'),
         ('Carryover', 'Employees may carry over up to 5 unused annual leave days into the next calendar year. Carried-over days must be used by March 31.')],
        [('Sick leave', 'Employees receive 8 paid sick days per calendar year. Notify your manager as soon as practical when you cannot work due to illness.'),
         ('Family leave', 'Eligible employees may take up to 12 weeks of unpaid family leave in a rolling 12-month period. Contact People Operations to confirm eligibility and arrange leave.')]
    ]),
    'remote-work-policy.pdf': ('Remote Work Policy', [
        [('Eligibility', 'Employees may work remotely up to 3 days per week with manager approval. Roles that require on-site coverage may have different schedules.'),
         ('Core hours', 'Remote employees must be available for collaboration from 10:00 a.m. to 3:00 p.m. in their team\'s local time zone on working days.'),
         ('Equipment', 'The company provides a laptop and a one-time home-office equipment allowance of up to $500. Submit receipts through the expense system within 30 days of purchase.')],
        [('Security', 'Use the company VPN when accessing internal systems from a public network. Never leave a company device unattended in a public place.'),
         ('Working abroad', 'Employees must obtain written approval from People Operations at least 30 days before working from another country. Approval depends on legal, tax, and security review.')]
    ]),
    'travel-expense-policy.pdf': ('Travel & Expense Policy', [
        [('Booking travel', 'Book business travel through the company travel portal. Flights over $800 require manager approval before booking.'),
         ('Hotels', 'The standard hotel limit is $225 per night before taxes. A manager may approve a higher rate when a conference hotel or local market conditions justify it.'),
         ('Meals', 'The meal reimbursement limit is $65 per person per travel day, including tips. Alcohol is not reimbursable.')],
        [('Submitting expenses', 'Submit expense reports within 30 calendar days after the trip ends. Attach an itemized receipt for every expense over $25.'),
         ('Personal travel', 'Personal travel added to a business trip must be paid by the employee. Reimbursement is limited to the documented cost of the business-only itinerary.')]
    ])
}
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='PolicyTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=23, leading=28, textColor=colors.HexColor('#173a37'), spaceAfter=8))
styles.add(ParagraphStyle(name='Kicker', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=13, textColor=colors.HexColor('#69827c'), spaceAfter=20))
styles.add(ParagraphStyle(name='PolicyHead', parent=styles['Heading2'], fontSize=13, leading=17, textColor=colors.HexColor('#173a37'), spaceBefore=14, spaceAfter=5))
styles.add(ParagraphStyle(name='PolicyBody', parent=styles['BodyText'], fontSize=11, leading=17, textColor=colors.HexColor('#263b38'), spaceAfter=9))
def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#d8e4df'))
    canvas.line(54, 51, 558, 51)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#617a74'))
    canvas.drawString(54, 37, 'NORTHSTAR  /  FICTIONAL SAMPLE POLICY')
    canvas.drawRightString(558, 37, str(doc.page))
for filename, (title, pages) in POLICIES.items():
    story = []
    for index, sections in enumerate(pages):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(title, styles['PolicyTitle']))
        story.append(Paragraph('PEOPLE OPERATIONS  /  SAMPLE DOCUMENT', styles['Kicker']))
        for heading, body in sections:
            story.extend([Paragraph(heading, styles['PolicyHead']), Paragraph(body, styles['PolicyBody'])])
    SimpleDocTemplate(str(ROOT / filename), pagesize=(612, 792), leftMargin=54, rightMargin=54, topMargin=62, bottomMargin=68, title=title).build(story, onFirstPage=footer, onLaterPages=footer)
