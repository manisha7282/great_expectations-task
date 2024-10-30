import pandas as pd
from sqlalchemy import create_engine
import great_expectations as ge
from great_expectations.data_context import DataContext
from great_expectations.core.batch import RuntimeBatchRequest
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

load_dotenv()  

connection_string = "mssql+pyodbc://my_sql_server"
engine = create_engine(connection_string)


def validate_sales_data():
    try:
        sales_df = pd.read_sql('SELECT * FROM greatexpectations.dbo.Sales', engine)
        print("Sales data loaded successfully!")
    except Exception as e:
        print(f"Error loading sales data: {e}")
        return []

    context = DataContext()
    suite_name = "sales_expectation_suite"

    try:
        existing_suites = context.list_expectation_suite_names()
        if suite_name not in existing_suites:
            context.create_expectation_suite(suite_name, overwrite_existing=True)

        sales_batch_request = RuntimeBatchRequest(
            datasource_name="my_sqlalchemy_datasource",
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name="sales",
            runtime_parameters={"query": "SELECT * FROM greatexpectations.dbo.Sales"},
            batch_identifiers={"default_identifier_name": "default_identifier"}
        )

        sales_validator = context.get_validator(batch_request=sales_batch_request, expectation_suite_name=suite_name)

        
        sales_validator.expect_column_values_to_be_between("Total_Revenue", min_value=0)
        sales_validator.expect_column_values_to_not_be_null("Total_Cost")
        sales_validator.expect_column_values_to_be_between("Unit_Price", min_value=0, max_value=10000)
        sales_validator.expect_column_values_to_not_be_null("Units_Sold")
        sales_validator.expect_column_value_lengths_to_equal("Order_ID", 9)
        sales_validator.expect_column_values_to_be_in_set("Order_Priority", ["H", "L", "C", "M"])
        sales_validator.expect_column_values_to_be_in_set("Sales_Channel", ["offline", "online"])
        sales_validator.expect_column_values_to_be_of_type("Country", "VARCHAR")
        sales_validator.expect_column_values_to_be_of_type("Region", "VARCHAR")

        context.save_expectation_suite(sales_validator.expectation_suite)

        context.build_data_docs()

        sales_results = sales_validator.validate()
        #print(sales_results)
    except Exception as e:
        print(f"Error validating sales data: {e}")
        return []

    validation_results = []
    for result in sales_results['results']:
        validation_results.append({
            "Column Name": result['expectation_config']['kwargs']['column'],
            "Expectation Type": result['expectation_config']['expectation_type'],
            "Success": result['success'],
            "Observed Value": result.get('result', {}).get('observed_value', None),
        })
     
    # validation_df = pd.DataFrame(validation_results)
    
    
    # print(validation_df)  
    return validation_results
    


def validate_customer_data():
    try:
        df = pd.read_sql('SELECT * FROM [greatexpectations].[dbo].[customers]', engine)
        print("Customer data loaded successfully!")
    except Exception as e:
        print(f"Error loading customer data: {e}")
        return []

    context = DataContext()
    suite_name = "customer_expectation_suite"

    try:
        existing_suites = context.list_expectation_suite_names()
        if suite_name not in existing_suites:
            context.create_expectation_suite(suite_name, overwrite_existing=True)

        batch_request = RuntimeBatchRequest(
            datasource_name="my_sqlalchemy_datasource",
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name="customers",
            runtime_parameters={"query": "SELECT * FROM greatexpectations.dbo.customers"},
            batch_identifiers={"default_identifier_name": "default_identifier"}
        )

        validator = context.get_validator(batch_request=batch_request, expectation_suite_name=suite_name)

        
        validator.expect_column_values_to_not_be_null("Customer_Id")
        validator.expect_column_value_lengths_to_be_between("Customer_Id", min_value=1, max_value=15)
        validator.expect_column_values_to_be_of_type("Customer_Id", "VARCHAR")
        validator.expect_column_values_to_be_of_type("Index", "INTEGER")
        validator.expect_column_values_to_be_of_type("First_Name", "VARCHAR")
        validator.expect_column_values_to_be_of_type("Last_Name", "VARCHAR")
        validator.expect_column_values_to_be_of_type("Subscription_Date", "DATE")

        context.save_expectation_suite(validator.expectation_suite)

        context.build_data_docs()

        results = validator.validate()
    except Exception as e:
        print(f"Error validating customer data: {e}")
        return []

    validation_results = []
    for result in results['results']:
        validation_results.append({
            "Column Name": result['expectation_config']['kwargs']['column'],
            "Expectation Type": result['expectation_config']['expectation_type'],
            "Success": result['success'],
            "Observed Value": result.get('result', {}).get('observed_value', None),
        })
    validate_df=pd.DataFrame(validation_results)  
    print(validate_df)  
    return validation_results



def generate_pdf_report(sales_results, customer_results):
    pdf_report_path = r"C:\Users\ManishaBheemanpally\OneDrive - Accellor\Desktop\Greater_Expectationa\gx\combined_report.pdf"
    
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Validation Report", 0, 1, 'C')

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Sales Validation Results", 0, 1, 'L')
    pdf.set_font("Arial", 'B', 12)
    headers = ["Column Name", "Expectation Type", "Success", "Observed Value"]
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 10, headers[0], 1, 0, 'C', 1)
    pdf.cell(80, 10, headers[1], 1, 0, 'C', 1)
    pdf.cell(30, 10, headers[2], 1, 0, 'C', 1)
    pdf.cell(40, 10, headers[3], 1, 1, 'C', 1)

    pdf.set_font("Arial", '', 12)
    for result in sales_results:
        pdf.cell(50, 10, str(result['Column Name']), 1)
        pdf.cell(80, 10, str(result['Expectation Type']), 1)
        pdf.cell(30, 10, str(result['Success']), 1)
        pdf.cell(40, 10, str(result['Observed Value']), 1)
        pdf.ln()

    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Customer Validation Results", 0, 1, 'L')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, headers[0], 1, 0, 'C', 1)
    pdf.cell(80, 10, headers[1], 1, 0, 'C', 1)
    pdf.cell(30, 10, headers[2], 1, 0, 'C', 1)
    pdf.cell(40, 10, headers[3], 1, 1, 'C', 1)

    for result in customer_results:
        pdf.cell(50, 10, str(result['Column Name']), 1)
        pdf.cell(80, 10, str(result['Expectation Type']), 1)
        pdf.cell(30, 10, str(result['Success']), 1)
        pdf.cell(40, 10, str(result['Observed Value']), 1)
        pdf.ln()

    try:
        pdf.output(pdf_report_path)
        print(f"Combined validation report saved as PDF: {pdf_report_path}")
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None

    return pdf_report_path


def send_email(pdf_file_path):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")  

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Great Expectations Validation (sales and customers) report'

    body = "Please find attached the Great Expectations Validation Summary for sales and customer in PDF format.\n\n"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(pdf_file_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read(), Name='combined_report.pdf')
            part['Content-Disposition'] = f'attachment; filename="combined_report.pdf"'
            msg.attach(part)
    except Exception as e:
        print(f"Error attaching PDF file: {e}")
        return

    try:
        with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient_email}.")
    except Exception as e:
        print(f"Error sending email: {e}")





sales_results = validate_sales_data()
customer_results = validate_customer_data()

if sales_results or customer_results:  
    pdf_file_path = generate_pdf_report(sales_results, customer_results)
    if pdf_file_path:
        send_email(pdf_file_path)  






