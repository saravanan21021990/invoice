import streamlit as st
import os
from datetime import datetime
from xhtml2pdf import pisa
import io

# --- Helper Functions ---
def number_to_words(n):
    if n == 0:
        return "Zero Rupees only"
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
            "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    def convert_below_1000(num):
        if num == 0: return ""
        elif num < 20: return ones[num] + " "
        elif num < 100: return tens[num // 10] + " " + ones[num % 10] + (" " if num % 10 != 0 else "")
        else: return ones[num // 100] + " Hundred " + convert_below_1000(num % 100)
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

        # Absolute paths for local files
        logo_path = os.path.abspath("logo.png") if os.path.exists("logo.png") else ""
        sign_path = os.path.abspath("indu_sign.png") if os.path.exists("indu_sign.png") else ""

        logo_html = f'<img src="{logo_path}" style="max-height: 90px;">' if logo_path else '<div style="height: 90px; text-align:center;">LOGO</div>'
        sig_html = f'<img src="{sign_path}" style="max-height: 50px;">' if sign_path else '<br><br><br>'

        # Handle Discount display
        disc_label = f"Discount ({discount_percent:g}%)<br><br>" if discount_percent > 0 else ""
        disc_val = f": - ₹ {discount_amount:,.2f}<br><br>" if discount_percent > 0 else ""

        # Handle Probe Row
        probe_row = ""
        if probe_cost > 0:
            probe_row = f"""
            <tr>
                <td style="border-right: 1px solid #111;" class="text-center">2</td>
                <td style="border-right: 1px solid #111;">Probe</td>
                <td style="border-right: 1px solid #111;"></td>
                <td style="border-right: 1px solid #111;" class="text-right">1.00</td>
                <td style="border-right: 1px solid #111;" class="text-center">-</td>
                <td style="border-right: 1px solid #111;" class="text-right">₹ {probe_cost:,.2f}</td>
                <td class="text-right">₹ {probe_cost:,.2f}</td>
            </tr>
            """

        # Ultra-basic HTML table layout to bypass xhtml2pdf crashing
        html_template = f"""
        <html>
        <head>
        <style>
            @page {{ size: A4; margin: 1.5cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; color: #111; }}
            .text-center {{ text-align: center; }}
            .text-right {{ text-align: right; }}
            .bold {{ font-weight: bold; }}
        </style>
        </head>
        <body>
            <div class="text-center bold" style="font-size: 18pt; margin-bottom: 15px;">Tax Invoice</div>
            
            <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #111;">
                <!-- Header -->
                <tr>
                    <td width="25%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; text-align: center; padding: 10px;">
                        {logo_html}
                    </td>
                    <td width="75%" style="border-bottom: 1px solid #111; padding: 10px; padding-left: 20px;">
                        <span style="font-size: 15pt; font-weight: bold; color: #222;">JesRa Electrolysis</span><br><br>
                        <span style="color: #444;">No.414/69, 9th main, Vijayanagar, Bangalore</span><br><br>
                        Phone: <strong>9964847715</strong> &nbsp;&nbsp;&nbsp;&nbsp; Email: <strong>jesra.electrolysis@gmail.com</strong>
                    </td>
                </tr>
                
                <!-- Bill To & Details -->
                <tr>
                    <td width="50%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; background-color: #f4f2f5; padding: 8px;" class="bold">Bill To:</td>
                    <td width="50%" style="border-bottom: 1px solid #111; background-color: #f4f2f5; padding: 8px;" class="bold">Invoice Details:</td>
                </tr>
                <tr>
                    <td width="50%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; padding: 8px;">
                        <span class="bold" style="font-size: 12pt;">{client_name.title()}</span><br><br>
                        Contact No: <span class="bold">{contact_no}</span>
                    </td>
                    <td width="50%" style="border-bottom: 1px solid #111; padding: 8px;">
                        No: <span class="bold">{inv_no}</span><br><br>
                        Date: <span class="bold">{date_str}</span>
                    </td>
                </tr>
            </table>
            
            <!-- Items Table -->
            <table width="100%" cellpadding="6" cellspacing="0" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111;">
                <tr style="background-color: #f4f2f5;">
                    <th width="8%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-center">#</th>
                    <th width="32%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; text-align: left;">Item Name</th>
                    <th width="12%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; text-align: left;">HSN/ SAC</th>
                    <th width="10%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-right">Qty</th>
                    <th width="10%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-center">Unit</th>
                    <th width="14%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-right">Price (₹)</th>
                    <th width="14%" style="border-bottom: 1px solid #111;" class="text-right">Amount(₹)</th>
                </tr>
                <tr>
                    <td style="border-right: 1px solid #111;" class="text-center">1</td>
                    <td style="border-right: 1px solid #111;">Electrolysis</td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;" class="text-right">{hours_qty:.2f}</td>
                    <td style="border-right: 1px solid #111;" class="text-center">Hur</td>
                    <td style="border-right: 1px solid #111;" class="text-right">₹ {base_rate * 2:,.2f}</td>
                    <td class="text-right">₹ {service_amount:,.2f}</td>
                </tr>
                {probe_row}
                <tr>
                    <td style="border-right: 1px solid #111;"><br><br><br><br><br></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td></td>
                </tr>
                <tr>
                    <td colspan="3" style="border-right: 1px solid #111; border-top: 1px solid #111;" class="bold text-right">Total</td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;" class="bold text-right">{total_qty:.2f}</td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;"></td>
                    <td style="border-top: 1px solid #111;" class="bold text-right">₹ {subtotal:,.2f}</td>
                </tr>
            </table>
            
            <!-- Summary & Footer -->
            <table width="100%" cellpadding="8" cellspacing="0" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111;">
                <tr>
                    <td width="60%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;">
                    </td>
                    <td width="20%" style="border-bottom: 1px solid #111;">
                        Sub Total<br><br>
                        {disc_label}
                        <span class="bold">Total</span>
                    </td>
                    <td width="20%" style="border-bottom: 1px solid #111;" class="text-right">
                        : ₹ {subtotal:,.2f}<br><br>
                        {disc_val}
                        <span class="bold">: ₹ {total_due:,.2f}</span>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" style="border-bottom: 1px solid #111; padding: 10px;">
                        <span class="bold">Invoice Amount In Words :</span><br><br>
                        {amount_words}
                    </td>
                </tr>
                <tr>
                    <td width="60%" style="border-right: 1px solid #111; padding: 10px;">
                        <span class="bold">Description:</span><br><br>
                        {description}
                    </td>
                    <td width="20%" style="padding: 10px;">
                        Received<br><br>
                        Balance
                    </td>
                    <td width="20%" style="padding: 10px;" class="text-right">
                        : ₹ {amount_received:,.2f}<br><br>
                        : ₹ {balance:,.2f}
                    </td>
                </tr>
            </table>
            
            <!-- Signatory -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                <tr>
                    <td width="60%"></td>
                    <td width="40%" class="text-right">
                        <span class="bold">For JesRa Electrolysis:</span><br>
                        {sig_html}<br>
                        <span class="bold">Authorized Signatory</span>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        try:
            with st.spinner("Generating PDF..."):
                pdf_buffer = io.BytesIO()
                pisa_status = pisa.CreatePDF(html_template, dest=pdf_buffer)
                
                if pisa_status.err:
                    st.error("An error occurred during PDF rendering.")
                else:
                    pdf_bytes = pdf_buffer.getvalue()
                    st.success("Invoice generated successfully!")
                    st.download_button(
                        label="Download PDF Invoice",
                        data=pdf_bytes,
                        file_name=f"Invoice_{inv_no}_{client_name.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
