import csv
import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

USER_CSV_PATH = 'data/users.csv'
REPORT_CSV_PATH = 'data/tax_reports.csv'

# Function to add a new user to the CSV file
def add_user_to_csv(username, password, phone_number, email, dob):
    fieldnames = ['username', 'password', 'phone_number', 'email', 'dob']
    with open(USER_CSV_PATH, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow({
            'username': username,
            'password': password,
            'phone_number': phone_number,
            'email': email,
            'dob': dob
            
        })

# Function to check user credentials
def check_user_credentials(username, password):
    with open(USER_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                return row
    return None

# Function to calculate income tax based on Indian tax slabs
def calculate_income_tax(income):
    if income <= 250000:
        return 0
    elif income <= 500000:
        return (income - 250000) * 0.05
    elif income <= 1000000:
        return (income - 500000) * 0.2 + 12500
    else:
        return (income - 1000000) * 0.3 + 12500 + 100000

# Vehicle tax calculation (simplified)
def calculate_vehicle_tax(vehicle_type, engine_capacity, vehicle_age):
    tax = 0
    if vehicle_type.lower() == 'car':
        if engine_capacity <= 1000:
            tax = 1500
        else:
            tax = 2500
    elif vehicle_type.lower() == 'motorbike':
        if engine_capacity <= 150:
            tax = 500
        else:
            tax = 800
    if vehicle_age > 10:
        tax *= 0.9
    return tax

# Property tax calculation
def calculate_property_tax(property_value, property_type="residential"):
    if property_type.lower() == "commercial":
        return property_value * 0.01
    else:
        return property_value * 0.005

# Function to store tax reports in the CSV file
def store_tax_report(username, income_tax, vehicle_tax, property_tax, total_tax, year):
    fieldnames = ['username', 'year', 'income_tax', 'vehicle_tax', 'property_tax', 'total_tax']
    with open(REPORT_CSV_PATH, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow({
            'username': username,
            'year': year,
            'income_tax': income_tax,
            'vehicle_tax': vehicle_tax,
            'property_tax': property_tax,
            'total_tax': total_tax
        })

# Ensure the 'data' folder exists
if not os.path.exists('data'):
    os.makedirs('data')

# If the 'users.csv' doesn't exist, create it with a header
if not os.path.exists(USER_CSV_PATH):
    with open(USER_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'password', 'phone_number', 'email', 'dob'])
        writer.writeheader()

# If the 'tax_reports.csv' doesn't exist, create it with a header
if not os.path.exists(REPORT_CSV_PATH):
    with open(REPORT_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'year', 'income_tax', 'vehicle_tax', 'property_tax', 'total_tax'])
        writer.writeheader()

# Route for the home page (index page)
@app.route('/')
def index():
    return render_template('index.html')

# Route for the register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone_number = request.form['phone_number']
        email = request.form['email']
        dob = request.form['dob']
        
        add_user_to_csv(username, password, phone_number, email, dob)
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = check_user_credentials(username, password)
        
        if user:
            session.clear()  # Clear any existing session data to avoid old data contamination
            session['username'] = user['username']
            session['email'] = user['email']
            session['phone_number'] = user['phone_number']
            session['dob'] = user['dob']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# Route for the dashboard page
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user_data=session)

# Route for the profile page
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('profile.html', user_data=session)

# Route for the edit profile page
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Check if the form was submitted
    if request.method == 'POST':
        # Retrieve and update the user details
        session['username'] = request.form['username']
        session['email'] = request.form['email']
        session['phone_number'] = request.form['phone_number']
        session['dob'] = request.form['dob']
        
        return redirect(url_for('profile'))
    
    # Display the form with existing data
    return render_template('edit_profile.html', user_data=session)

# Route for tax calculation page
@app.route('/tax_calculation', methods=['GET', 'POST'])
def tax_calculation():
    if request.method == 'POST':
        income = float(request.form['income'])
        vehicle_type = request.form['vehicle_type']
        engine_capacity = int(request.form['engine_capacity'])
        vehicle_age = int(request.form['vehicle_age'])
        property_value = float(request.form['property_value'])
        property_type = request.form['property_type']
        year = int(request.form['year'])  # Get the selected tax year from the form

        user_data = session
        user_data['income'] = income
        user_data['vehicle_details'] = {
            'type': vehicle_type,
            'engine_capacity': engine_capacity,
            'age': vehicle_age
        }
        user_data['property_value'] = property_value
        user_data['property_type'] = property_type
        user_data['tax_year'] = year  # Store the tax year in the session

        income_tax = calculate_income_tax(income)
        vehicle_tax = calculate_vehicle_tax(vehicle_type, engine_capacity, vehicle_age)
        property_tax = calculate_property_tax(property_value, property_type)

        total_tax = income_tax + vehicle_tax + property_tax
        user_data['tax_due'] = total_tax

        # Store the tax report in the CSV file
        store_tax_report(user_data['username'], income_tax, vehicle_tax, property_tax, total_tax, year)

        return redirect(url_for('tax_report'))
    
    return render_template('tax_calculation.html')

# Route for the tax report page
@app.route('/tax_report')
def tax_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_data = session
    income_tax = calculate_income_tax(user_data['income'])
    vehicle_tax = calculate_vehicle_tax(user_data['vehicle_details']['type'], user_data['vehicle_details']['engine_capacity'], user_data['vehicle_details']['age'])
    property_tax = calculate_property_tax(user_data['property_value'], user_data['property_type'])
    total_tax = income_tax + vehicle_tax + property_tax

    return render_template('tax_report.html', username=session['username'], income_tax=income_tax, vehicle_tax=vehicle_tax, property_tax=property_tax, total_tax=total_tax)

# Route for generating PDF tax report
@app.route('/download-pdf')
def download_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_data = session
    income_tax = calculate_income_tax(user_data['income'])
    vehicle_tax = calculate_vehicle_tax(user_data['vehicle_details']['type'], user_data['vehicle_details']['engine_capacity'], user_data['vehicle_details']['age'])
    property_tax = calculate_property_tax(user_data['property_value'], user_data['property_type'])
    total_tax = income_tax + vehicle_tax + property_tax

    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name="Title", fontSize=18, alignment=1, textColor=colors.darkblue, fontName="Helvetica-Bold")
    heading_style = ParagraphStyle(name="Heading", fontSize=14, alignment=0, textColor=colors.black, fontName="Helvetica-Bold")
    
    elements = [
        Paragraph("Tax Report for {}".format(user_data['username']), title_style),
        Paragraph("<b>Income Tax:</b> ${:.2f}".format(income_tax), heading_style),
        Paragraph("<b>Vehicle Tax:</b> ${:.2f}".format(vehicle_tax), heading_style),
        Paragraph("<b>Property Tax:</b> ${:.2f}".format(property_tax), heading_style),
        Paragraph("<b>Total Tax Due:</b> ${:.2f}".format(total_tax), heading_style),
    ]

    doc.build(elements)

    response = make_response(pdf_output.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=tax_report.pdf'
    return response
if __name__== '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
