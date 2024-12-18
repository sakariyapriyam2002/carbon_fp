import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from io import BytesIO
import matplotlib.pyplot as plt
import os
import datetime  # Import datetime module

app = Flask(__name__)

# Function to calculate carbon footprint
def calculate_footprint(energy_kwh, distance_km, waste_kg):
    energy_emission = 0.233  # Emission factor for electricity
    emission_energy = energy_kwh * energy_emission

    emission_transport = 0.192  # Emission factor for transportation
    emission_transport = distance_km * emission_transport

    emission_waste = 0.1  # Emission factor for waste
    emission_waste = waste_kg * emission_waste

    total_emission = emission_energy + emission_transport + emission_waste

    return emission_energy, emission_transport, emission_waste, total_emission

# Function to generate a chart
def generate_emission_chart(energy, transport, waste):
    categories = ['Energy', 'Transport', 'Waste']
    values = [energy, transport, waste]

    # Create a pie chart
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(
        values, 
        labels=categories, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=['#ff9999', '#66b3ff', '#99ff99']
    )
    ax.set_title('Carbon Emission Distribution')

    # Save the chart as an image
    chart_path = 'emission_chart.png'
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()
    return chart_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            energy_kwh = float(request.form["electricity"])
            distance_km = float(request.form["distance"])
            waste_kg = float(request.form["waste"])

            emission_energy, emission_transport, emission_waste, total_emission = calculate_footprint(energy_kwh, distance_km, waste_kg)

            result = {
                "energy": emission_energy,
                "transport": emission_transport,
                "waste": emission_waste,
                "total": total_emission
            }

            return render_template("result.html", result=result)
        except ValueError:
            return "Invalid input, please enter valid numbers."

    return render_template("index.html")

@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    energy = request.args.get('energy')
    transport = request.args.get('transport')
    waste = request.args.get('waste')
    total = request.args.get('total')

    # Check if parameters exist
    if not all([energy, transport, waste, total]):
        return "Missing parameters for PDF generation", 400
    
    try:
        energy = float(energy)
        transport = float(transport)
        waste = float(waste)
        total = float(total)
    except ValueError:
        return "Invalid parameter values", 400

    # Generate the chart
    chart_path = generate_emission_chart(energy, transport, waste)

    # Get current date
    generated_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current date in desired format

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Add header
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.darkblue)
    c.drawString(200, 770, "Carbon Footprint Report")
    c.line(50, 760, 550, 760)

    # Add sub-header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(50, 730, "Summary of Carbon Emissions")

    # Add a paragraph with emissions data
    c.setFont("Helvetica", 12)
    c.drawString(50, 710, f"Energy Emission (Electricity): {energy:.2f} kg CO2")
    c.drawString(50, 690, f"Transport Emission: {transport:.2f} kg CO2")
    c.drawString(50, 670, f"Waste Emission: {waste:.2f} kg CO2")
    c.drawString(50, 650, f"Total Emission: {total:.2f} kg CO2")

    # Add the generated date
    c.setFont("Helvetica", 10)
    c.drawString(50, 630, f"Generated Date: {generated_date}")

    # Add table
    data = [
        ["Category", "Emissions (kg CO2)"],
        ["Energy", f"{energy:.2f}"],
        ["Transport", f"{transport:.2f}"],
        ["Waste", f"{waste:.2f}"],
        ["Total", f"{total:.2f}"]
    ]
    table = Table(data, colWidths=[200, 150])
    table.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    table.wrapOn(c, 400, 500)  # wrap the table within bounds
    table.drawOn(c, 100, 500)  # position the table on the canvas

    # Add chart image
    if os.path.exists(chart_path):
        c.drawImage(chart_path, 100, 200, width=400, height=250)

    # Footer
    c.setFont("Helvetica", 10)
    c.drawString(50, 50, "Generated by the Carbon Footprint Calculator")

    c.showPage()
    c.save()

    buffer.seek(0)

    # Remove the chart image file
    if os.path.exists(chart_path):
        os.remove(chart_path)

    return send_file(buffer, as_attachment=True, download_name="carbon_footprint_report.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
