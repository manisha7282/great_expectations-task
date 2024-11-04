import pandas as pd
import great_expectations as ge
from great_expectations.data_context import DataContext

import os
from dotenv import load_dotenv
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText


load_dotenv()


suite_name = "customer_suite"


context = DataContext(r"C:\\Users\\ManishaBheemanpally\\OneDrive - Accellor\\Desktop\\Greater_Expectationa\\gx")


existing_suites = context.list_expectation_suite_names()
if suite_name not in existing_suites:
    context.add_or_update_expectation_suite(expectation_suite_name=suite_name)

def validate_customer_data(file_name):
    
    customer_df = pd.read_csv(file_name)

    
    customer_df_ge = ge.from_pandas(customer_df)

    
    
    customer_df_ge.expect_column_values_to_be_in_set('Index', list(range(len(customer_df))))
    customer_df_ge.expect_column_value_lengths_to_be_between('Customer Id', 1, 15)
    customer_df_ge.expect_column_values_to_be_of_type('First Name', 'str')
    customer_df_ge.expect_column_values_to_be_of_type('Last Name', 'str')
    customer_df_ge.expect_column_values_to_be_of_type("Index", "INTEGER")
    customer_df_ge.expect_column_values_to_be_of_type('Subscription Date', 'datetime64[ns]')

    
    results = customer_df_ge.validate()

    
    validation_results = []
    for result in results['results']:
        validation_results.append({
            "Column Name": result['expectation_config']['kwargs'].get('column', 'N/A'),
            "Expectation Type": result['expectation_config']['expectation_type'],
            "Success": result['success'],
            "Observed Value": result.get('result', {}).get('observed_value', None),
            "Unexpected Count": result.get('result', {}).get('unexpected_count', 0) 
        })
    validation_df=pd.DataFrame(validation_results)    
    print(validation_df)
    return validation_results

def generate_pdf(validation_results, file_name="validation_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Customer Data Validation Report", ln=True, align='C')
    pdf.ln(10)  

    for result in validation_results:
        pdf.cell(0, 10, txt=f"Column Name: {result['Column Name']}", ln=True)
        pdf.cell(0, 10, txt=f"Expectation Type: {result['Expectation Type']}", ln=True)
        pdf.cell(0, 10, txt=f"Success: {result['Success']}", ln=True)
        pdf.cell(0, 10, txt=f"Observed Value: {result['Observed Value']}", ln=True)
        pdf.cell(0, 10, txt=f"Unexpected Count: {result['Unexpected Count']}", ln=True)  # Add unexpected count
        pdf.ln(5)  # Add a line break between results
        pdf.cell(0, 10, txt="-" * 40, ln=True)  # Separator line for better readability

    pdf.output(file_name)

def send_email(pdf_file_path):
    
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")  

    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Great Expectations Validation (sales and customers) report'

    
    body = "Please find attached the Great Expectations Validation Summary for sales and customers in PDF format.\n\n"
    msg.attach(MIMEText(body, 'plain'))

    
    try:
        with open(pdf_file_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read(), Name='customer_report.pdf')
            part['Content-Disposition'] = f'attachment; filename="customer_report.pdf"'
            msg.attach(part)
        print("PDF attached successfully.")
    except Exception as e:
        print(f"Error attaching PDF file: {e}")
        return

    
    try:
        with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
            server.starttls()  
            server.login(sender_email, sender_password)  
            server.send_message(msg)  
        print(f"Email sent successfully to recipient.")
    except smtplib.SMTPAuthenticationError:
        print("Failed to authenticate. Check your email and password.")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    
    validation_results = validate_customer_data(r"C:\Users\ManishaBheemanpally\Downloads\customers-100000.csv")
    
    
    pdf_file_name = "validation_report.pdf"
    generate_pdf(validation_results, pdf_file_name)
    
    
    send_email(pdf_file_name)
    print("Validation report sent via email.")




