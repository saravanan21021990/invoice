import streamlit as st
import pdfkit
import os
import base64
from datetime import datetime


# --- Helper Functions ---
def number_to_words(n):
    if n == 0:
        return "Zero Rupees only"
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
            "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_below_1000(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num] + " "
        elif num < 100:
            return tens[num // 10] + " " + ones[num % 10] + (" " if num % 10 != 0 else "")
        else:
            return ones[num // 100] + " Hundred " + convert_below_1000(num % 100)

    result = ""
    if n >= 100000:
        result += convert_below_1000(n // 100000) + "Lakh "
        n %= 100000
    if n >= 1000:
        result += convert_below_1000(n // 1000) + "Thousand "
        n %= 1000
    if n > 0:
        result += convert_below_1000(n)
    return result.strip() + " Rupees only"


def get_image_base64(filepath):
    """Converts an image to base64 so it can be embedded directly in the HTML."""
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    return None


# --- Web App UI ---
st.set_page_config(page_title="JesRa Billing System", layout="centered")

st.title("JesRa Electrolysis Billing")
st.markdown("Generate and download professional PDF invoices directly to your device.")

# --- Input Form ---
with st.form("invoice_form"):
    st.subheader("1. Clinic & Rate Settings")
    col1, col2 = st.columns(2)
    inv_no = col1.text_input("Invoice Number", value="1")
    base_rate = col2.number_input("Base Rate (per 30 mins ₹)", min_value=1.0, value=800.0, step=50.0)

    st.subheader("2. Client Details")
    client_name = st.text_input("Client Name", placeholder="e.g., Kavya")
    contact_no = st.text_input("Contact Number", placeholder="e.g., 9632036238")

    st.subheader("3. Service Details")
    col3, col4 = st.columns(2)
    duration_minutes = col3.number_input("Duration (minutes)", min_value=0.0, value=30.0, step=5.0)
    probe_cost = col4.number_input("Probe Charge (₹)", min_value=0.0, value=300.0, step=10.0)

    col5, col6 = st.columns(2)
    discount_percent = col5.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
    amount_received = col6.number_input("Amount Received (₹)", min_value=0.0, value=0.0, step=50.0)

    description = st.text_input("Description", value="Chin, beard, mustache trimming")

    submitted = st.form_submit_button("Generate PDF Invoice")

# --- PDF Generation Logic ---
if submitted:
    if not client_name:
        st.error("Please enter a client name.")
    else:
        # Calculations
        rate_per_minute = base_rate / 30.0
        service_amount = rate_per_minute * duration_minutes
        subtotal = service_amount + probe_cost
        discount_amount = subtotal * (discount_percent / 100.0)
        total_due = subtotal - discount_amount
        balance = total_due - amount_received

        hours_qty = duration_minutes / 60.0
        total_qty = hours_qty + (1 if probe_cost > 0 else 0)

        date_str = datetime.now().strftime("%d-%m-%Y")
        amount_words = number_to_words(int(round(total_due)))

        # Process Images
        logo_b64 = get_image_base64("logo.png")
        sign_b64 = get_image_base64("indu_sign.png")

        logo_html = f'<img src="{logo_b64}" style="max-height: 120px; max-width: 100%;">' if logo_b64 else '<div style="height: 120px;">[LOGO]</div>'
        sig_html = f'<img src="{sign_b64}" style="max-height: 50px; max-width: 180px;">' if sign_b64 else '<div style="height: 45px;"></div>'

        discount_html = ""
        if discount_percent > 0:
            discount_html = f"""
            <tr>
                <td>Discount ({discount_percent:g}%)</td>
                <td style="text-align: right;">: - ₹ {discount_amount:,.2f}</td>
            </tr>
            """

        # HTML Template
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 11pt; color: #212529; margin: 0; padding: 0; }}
            .invoice-header {{ text-align: center; font-size: 22pt; font-weight: 700; padding: 15px 0; color: #343a40; }}
            .invoice-card {{ border: 1.5px solid #212529; background-color: #fff; }}
            .border-bottom {{ border-bottom: 1.5px solid #212529; }}
            .border-right {{ border-right: 1.5px solid #212529; }}
            .header-table, .info-table, .item-table, .summary-table {{ width: 100%; border-collapse: collapse; }}
            .header-table td, .info-table td {{ padding: 12px; vertical-align: middle; }}
            .info-table td {{ vertical-align: top; }}
            .clinic-title {{ font-size: 18pt; font-weight: bold; color: #3b3b4f; margin-bottom: 8px; }}
            .info-table th {{ background-color: #f4f2f5; text-align: left; padding: 8px 12px; font-weight: bold; border-bottom: 1.5px solid #212529; }}
            .item-table th {{ border-bottom: 1.5px solid #212529; border-right: 1px solid #212529; padding: 8px; font-weight: bold; font-size: 10pt; background-color: #f8f9fa; text-align: left; }}
            .item-table th:last-child, .item-table td:last-child {{ border-right: none; }}
            .item-table td {{ border-bottom: 1px solid #ddd; border-right: 1px solid #212529; padding: 8px; font-size: 10pt; }}
            .item-table .spacer-row td {{ height: 250px; border-bottom: 1.5px solid #212529; }}
            .item-table .total-row td {{ border-top: 1.5px solid #212529; border-bottom: 1.5px solid #212529; font-weight: bold; background-color: #fdfdfd; }}
            .num {{ text-align: right; }}
            .center {{ text-align: center; }}
            .summary-table td {{ padding: 6px 12px; font-size: 10pt; }}
            .words-box, .desc-box {{ padding: 8px 12px; font-size: 10pt; }}
            .words-box {{ border-bottom: 1.5px solid #212529; }}
            .sign-container {{ padding: 10px 15px 8px 15px; text-align: right; }}
            .sign-title, .sign-footer {{ font-size: 10pt; font-weight: bold; }}
            .sign-title {{ margin-bottom: 6px; }}
        </style>
        </head>
        <body>
        <div class="invoice-header">Tax Invoice</div>
        <div class="invoice-card">
            <table class="header-table border-bottom">
                <tr>
                    <td style="width: 25%; text-align: center; border-right: 1px solid #eee;">{logo_html}</td>
                    <td style="width: 75%;">
                        <div class="clinic-title">JesRa Electrolysis</div>
                        <div style="margin-bottom: 15px; color: #444;">No.414/69, 9th main, Vijayanagar, Bangalore</div>
                        <table style="width: 100%; font-size: 10.5pt; color: #333;">
                            <tr>
                                <td style="padding: 0; text-align: left;">Phone: <strong>9964847715</strong></td>
                                <td style="padding: 0; text-align: right;">Email: <strong>jesra.electrolysis@gmail.com</strong></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            <table class="info-table border-bottom">
                <tr><th class="border-right" style="width: 50%;">Bill To:</th><th style="width: 50%;">Invoice Details:</th></tr>
                <tr>
                    <td class="border-right"><div style="font-weight: bold; margin-bottom: 15px;">{client_name.title()}</div><div>Contact No: <strong>{contact_no}</strong></div></td>
                    <td><div style="margin-bottom: 8px;">No: <strong>{inv_no}</strong></div><div>Date: <strong>{date_str}</strong></div></td>
                </tr>
            </table>
            <table class="item-table">
                <thead>
                    <tr><th style="width: 5%;" class="center">#</th><th style="width: 32%;">Item Name</th><th style="width: 14%;">HSN/ SAC</th><th style="width: 12%;" class="num">Quantity</th><th style="width: 9%;" class="center">Unit</th><th style="width: 14%;" class="num">Price/ Unit (₹)</th><th style="width: 14%;" class="num">Amount(₹)</th></tr>
                </thead>
                <tbody>
                    <tr><td class="center">1</td><td>Electrolysis Treatment</td><td></td><td class="num">{hours_qty:.2f}</td><td class="center">Hur</td><td class="num">₹ {base_rate * 2:,.2f}</td><td class="num">₹ {service_amount:,.2f}</td></tr>
                    {"<tr><td class='center'>2</td><td>Probe</td><td></td><td class='num'>1.00</td><td class='center'>-</td><td class='num'>₹ " + f"{probe_cost:,.2f}</td><td class='num'>₹ {probe_cost:,.2f}</td></tr>" if probe_cost > 0 else ""}
                    <tr class="spacer-row"><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
                    <tr class="total-row"><td colspan="3">Total</td><td class="num">{total_qty:.2f}</td><td></td><td></td><td class="num">₹ {subtotal:,.2f}</td></tr>
                </tbody>
            </table>
            <table style="width: 100%; border-collapse: collapse;" class="border-bottom">
                <tr>
                    <td style="width: 52%; border-right: 1.5px solid #212529;"></td>
                    <td style="width: 48%; padding: 0;">
                        <table class="summary-table">
                            <tr><td>Sub Total</td><td style="text-align: right;">: ₹ {subtotal:,.2f}</td></tr>
                            {discount_html}
                            <tr style="font-weight: bold; border-top: 1px solid #eee;"><td>Total</td><td style="text-align: right;">: ₹ {total_due:,.2f}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
            <div class="words-box"><div style="font-weight: bold; margin-bottom: 4px;">Invoice Amount In Words :</div><div>{amount_words}</div></div>
            <table style="width: 100%; border-collapse: collapse;" class="border-bottom">
                <tr>
                    <td style="width: 52%; border-right: 1.5px solid #212529; vertical-align: top;" class="desc-box"><div style="font-weight: bold; margin-bottom: 4px;">Description:</div><div>{description}</div></td>
                    <td style="width: 48%; padding: 0; vertical-align: top;">
                        <table class="summary-table">
                            <tr><td>Received</td><td style="text-align: right;">: ₹ {amount_received:,.2f}</td></tr>
                            <tr><td>Balance</td><td style="text-align: right;">: ₹ {balance:,.2f}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
            <div class="sign-container"><div class="sign-title">For JesRa Electrolysis:</div><div style="margin: 5px 0;">{sig_html}</div><div class="sign-footer">Authorized Signatory</div></div>
        </div>
        </body>
        </html>
        """

        options = {
            'page-size': 'A4',
            'margin-top': '12mm', 'margin-right': '12mm',
            'margin-bottom': '12mm', 'margin-left': '12mm',
            'encoding': "UTF-8", 'quiet': ''
        }

        # Handle wkhtmltopdf path for local Windows vs Cloud Linux
        config = None
        if os.name == 'nt':
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            if os.path.exists(path_wkhtmltopdf):
                config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        temp_file = "temp_invoice.pdf"
        try:
            with st.spinner("Generating PDF..."):
                if config:
                    pdfkit.from_string(html_template, temp_file, options=options, configuration=config)
                else:
                    pdfkit.from_string(html_template, temp_file, options=options)

            with open(temp_file, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()

            st.success("Invoice generated successfully!")
            st.download_button(
                label="Download PDF Invoice",
                data=pdf_bytes,
                file_name=f"Invoice_{inv_no}_{client_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )

        except Exception as e:
            st.error(
                f"Error generating PDF. If you are running locally on Windows, make sure wkhtmltopdf is installed. Error details: {e}")