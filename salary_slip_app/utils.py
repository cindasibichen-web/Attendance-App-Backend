import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.conf import settings
from num2words import num2words


def generate_salary_pdf(employee_data):
    """
    Generate a well-formatted salary slip PDF (similar to the provided sample).
    """
    directory = os.path.join(settings.MEDIA_ROOT, 'salary_pdfs')
    os.makedirs(directory, exist_ok=True)

    emp_no = str(employee_data.get('Emp. No', ''))
    emp_name = str(employee_data.get('Name', ''))
    net_pay = float(employee_data.get('Net Pay', 0))
    file_name = f"salary_slip_{emp_no}.pdf"
    file_path = os.path.join(directory, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # Outer light blue border
    c.setStrokeColor(colors.HexColor("#030303"))
    c.setLineWidth(1)
    c.rect(25, 25, width - 50, height - 50)

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 60, "Salary Slip")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 90, "Ziya Academy")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawCentredString(width / 2, height - 105, "123, Example Street, City, State - 600001")
    c.setFillColor(colors.black)

    # Employee Info
    y = height - 140
    line_gap = 16
    c.setFont("Helvetica", 10)

    emp_details = [
        ("Employee Name", employee_data.get("Name")),
        ("Employee ID", emp_no),
        ("Designation", employee_data.get("Designation")),
        ("Department", employee_data.get("Department")),
        ("Bank Name", employee_data.get("Bank Name")),
        ("Bank A/C No", employee_data.get("Bank A/C No")),
        ("IFSC Code", employee_data.get("IFSC Code")),
    ]

    for label, value in emp_details:
        c.drawString(60, y, f"{label}: ")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(160, y, str(value or "-"))
        c.setFont("Helvetica", 10)
        y -= line_gap

    y -= 10
    c.line(50, y, width - 50, y)
    y -= 25

    # Earnings & Deductions Titles
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120, y, "Earnings")
    c.drawString(width / 2 + 80, y, "Deductions")
    y -= 20

    c.setFont("Helvetica", 10)
    earnings = [
        ("Basic Salary", employee_data.get("Basic Salary")),
        ("Total Work", employee_data.get("Total Work")),
        ("Paid Days", employee_data.get("Paid Day Earnings")),
    ]
    deductions = [
        ("Total Deductions", employee_data.get("Total Deductions")),
    ]

    # Draw earnings and deductions side by side
    for i in range(max(len(earnings), len(deductions))):
        if i < len(earnings):
            c.drawString(80, y, f"{earnings[i][0]}")
            c.drawRightString(width / 2 - 40, y, f"Rs/- {earnings[i][1]}")
        if i < len(deductions):
            c.drawString(width / 2 + 60, y, f"{deductions[i][0]}")
            c.drawRightString(width - 80, y, f"Rs/- {deductions[i][1]}")
        y -= line_gap

    y -= 10
    c.line(50, y, width - 50, y)
    y -= 25

    # Amount in Words
    amount_words = num2words(net_pay, to="cardinal", lang="en").title() + " Only"
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"Amount in Words: {amount_words}")
    y -= 40

    c.line(50, y, width - 50, y)
    y -= 25

    # Signatures and Net Pay
    c.setFont("Helvetica", 10)
    c.drawString(60, y, "Employer Signature")
    c.drawCentredString(width / 2, y, f"Net Pay: Rs/- {net_pay:,.2f}")
    c.drawRightString(width - 60, y, "Employee Signature")

    c.showPage()
    c.save()

    return f"salary_pdfs/{file_name}"
