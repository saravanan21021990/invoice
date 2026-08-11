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

# Auto-increment logic using a local file
INV_FILE = "invoice_no.txt"
def get_next_invoice_no():
    if os.path.exists(INV_FILE):
        with open(INV_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 1
    return 1

def increment_invoice_no():
    current = get_next_invoice_no()
    with open(INV_FILE, "w") as f:
        f.write(str(current + 1))

# --- Web App UI ---
st.set_page_config(page_title="JesRa Billing System", layout="centered")

st.title("JesRa Electrolysis Billing")
st.markdown("Generate and download professional PDF invoices directly to your device.")

# --- Input Form ---
with st.form("invoice_form"):
    st.subheader("1. Clinic Settings")
    inv_no = st.text_input("Invoice Number", value=str(get_next_invoice_no()))
    
    st.subheader("2. Client Details")
    client_name = st.text_input("Client Name", placeholder="e.g., Kavya")
    contact_no = st.text_input("Contact Number", placeholder="e.g., 9632036238")

    st.subheader("3. Service & Rate Details")
    col_h, col_m, col_p = st.columns([1, 1, 1.5])
    dur_hours = col_h.number_input("Hours", min_value=0, value=0, step=1)
    dur_mins = col_m.number_input("Minutes", min_value=0, max_value=59, value=0, step=5)
    probe_cost = col_p.number_input("Probe Charge (Rs.)", min_value=0.0, value=0.0, step=10.0)
    
    col5, col6 = st.columns(2)
    standard_rate_30m = col5.number_input("Standard Base Price (per 30 mins Rs.)", min_value=0.0, value=0.0, step=50.0)
    discount_per_30m = col6.number_input("Discount (per 30 mins Rs.)", min_value=0.0, value=0.0, step=50.0)
    
    col7, col8 = st.columns(2)
    amount_received = col7.number_input("Amount Received (Rs.)", min_value=0.0, value=0.0, step=50.0)
    item_name = col8.text_input("Item Name / Description", value="", placeholder="e.g., Fine hair")

    submitted = st.form_submit_button("Generate PDF Invoice")

# --- PDF Generation Logic ---
if submitted:
    if not client_name:
        st.error("Please enter a client name.")
    else:
        # --- Calculations ---
        # Convert total duration into fractional hours
        total_duration_minutes = (dur_hours * 60) + dur_mins
        hours_qty = total_duration_minutes / 60.0
        
        total_qty = hours_qty + (1 if probe_cost > 0 else 0)
        
        # Calculate Hourly Rates based on the 30-min inputs
        hourly_standard = standard_rate_30m * 2
        hourly_discount = discount_per_30m * 2
        
        # Totals for the Primary Service
        item1_standard_total = hourly_standard * hours_qty
        item1_discount_amount = hourly_discount * hours_qty
        item1_discounted_total = item1_standard_total - item1_discount_amount
        
        # Percentage Calculation
        item1_discount_percent = (item1_discount_amount / item1_standard_total * 100) if item1_standard_total > 0 else 0
        
        # Probe Totals (No discount applied to probe)
        probe_discount_amount = 0.0
        probe_total = probe_cost
        
        # Overall Totals
        total_discount_amount = item1_discount_amount + probe_discount_amount
        subtotal = item1_discounted_total + probe_total
        
        total_due = subtotal
        balance = total_due - amount_received
        
        date_str = datetime.now().strftime("%d-%m-%Y")
        amount_words = number_to_words(int(round(total_due)))

        # Absolute paths for local files
        logo_path = os.path.abspath("logo.png") if os.path.exists("logo.png") else ""
        sign_path = os.path.abspath("indu_sign.png") if os.path.exists("indu_sign.png") else ""

        logo_html = f'<img src="{logo_path}" style="max-height: 80px;">' if logo_path else '<div style="height: 80px; text-align:left;">LOGO</div>'
        sig_html = f'<img src="{sign_path}" style="max-height: 45px;">' if sign_path else '<br><br>'

        # Handle Probe Row
        probe_row = ""
        if probe_cost > 0:
            probe_row = f"""
            <tr>
                <td style="border-right: 1px solid #111;" class="text-center">2</td>
                <td style="border-right: 1px solid #111;">Probe F2</td>
                <td style="border-right: 1px solid #111;"></td>
                <td style="border-right: 1px solid #111;" class="text-right">1</td>
                <td style="border-right: 1px solid #111;" class="text-center">-</td>
                <td style="border-right: 1px solid #111;" class="text-right">Rs. {probe_cost:,.2f}</td>
                <td style="border-right: 1px solid #111;" class="text-center">-</td>
                <td class="text-right">Rs. {probe_cost:,.2f}</td>
            </tr>
            """

        display_item_name = item_name if item_name.strip() else "Electrolysis"

        # HTML table layout
        html_template = f"""
        <html>
        <head>
        <style>
            @page {{ size: A4; margin: 1.0cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #111; }}
            .text-center {{ text-align: center; }}
            .text-right {{ text-align: right; }}
            .text-left {{ text-align: left; }}
            .bold {{ font-weight: bold; }}
        </style>
        </head>
        <body>
            <div class="text-center bold" style="font-size: 16pt; margin-bottom: 10px;">Tax Invoice</div>
            
            <!-- Header (Explicit Borders on TDs to remove middle line and fix alignment) -->
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="25%" style="border-top: 1px solid #111; border-left: 1px solid #111; border-bottom: 1px solid #111; text-align: left; vertical-align: middle; padding: 10px;">
                        {logo_html}
                    </td>
                    <td width="75%" style="border-top: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111; padding: 10px; vertical-align: middle;">
                        <span style="font-size: 16pt; font-weight: bold; color: #222;">JesRa Electrolysis</span><br>
                        <span style="color: #222;">No.414/69, 9th main, Vijayanagar, Bangalore</span><br><br>
                        Phone: <strong>9964847715</strong> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <strong>jesra.electrolysis@gmail.com</strong>
                    </td>
                </tr>
            </table>
            
            <!-- Bill To & Details -->
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="50%" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111; background-color: #f4f2f5; padding: 5px;" class="bold">Bill To:</td>
                    <td width="50%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; background-color: #f4f2f5; padding: 5px;" class="bold">Invoice Details:</td>
                </tr>
                <tr>
                    <td width="50%" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111; padding: 5px;">
                        <span class="bold" style="font-size: 11pt;">{client_name.title()}</span><br><br>
                        Contact No: <span class="bold">{contact_no}</span>
                    </td>
                    <td width="50%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; padding: 5px;">
                        No: <span class="bold">{inv_no}</span><br><br>
                        Date: <span class="bold">{date_str}</span>
                    </td>
                </tr>
            </table>
            
            <!-- Items Table -->
            <table width="100%" cellpadding="4" cellspacing="0" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111;">
                <tr style="background-color: #f4f2f5;">
                    <th width="5%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-center">#</th>
                    <th width="25%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; text-align: left;">Item Name</th>
                    <th width="10%" style="border-right: 1px solid #111; border-bottom: 1px solid #111; text-align: left;">HSN/ SAC</th>
                    <th width="10%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-right">Quantity</th>
                    <th width="8%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-center">Unit</th>
                    <th width="14%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-right">Price/ Unit (Rs.)</th>
                    <th width="14%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;" class="text-right">Discount (Rs.)</th>
                    <th width="14%" style="border-bottom: 1px solid #111;" class="text-right">Amount(Rs.)</th>
                </tr>
                <tr>
                    <td style="border-right: 1px solid #111;" class="text-center">1</td>
                    <td style="border-right: 1px solid #111;">{display_item_name}</td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;" class="text-right">{hours_qty:g}</td>
                    <td style="border-right: 1px solid #111;" class="text-center">Hur</td>
                    <td style="border-right: 1px solid #111;" class="text-right">Rs. {hourly_standard:,.2f}</td>
                    <td style="border-right: 1px solid #111;" class="text-right">Rs. {item1_discount_amount:,.2f}<br>({item1_discount_percent:.1f}%)</td>
                    <td class="text-right">Rs. {item1_discounted_total:,.2f}</td>
                </tr>
                {probe_row}
                <tr>
                    <td style="border-right: 1px solid #111;"><br><br><br></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111;"></td>
                    <td></td>
                </tr>
                <tr>
                    <td colspan="3" style="border-right: 1px solid #111; border-top: 1px solid #111;" class="bold text-right">Total</td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;" class="bold text-right">{total_qty:g}</td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;"></td>
                    <td style="border-right: 1px solid #111; border-top: 1px solid #111;" class="bold text-right">Rs. {total_discount_amount:,.2f}</td>
                    <td style="border-top: 1px solid #111;" class="bold text-right">Rs. {subtotal:,.2f}</td>
                </tr>
            </table>
            
            <!-- Summary & Footer -->
            <table width="100%" cellpadding="5" cellspacing="0" style="border-left: 1px solid #111; border-right: 1px solid #111; border-bottom: 1px solid #111;">
                <tr>
                    <td width="60%" style="border-right: 1px solid #111; border-bottom: 1px solid #111;">
                    </td>
                    <td width="20%" style="border-bottom: 1px solid #111;">
                        Sub Total<br><br>
                        <span class="bold">Total</span>
                    </td>
                    <td width="20%" style="border-bottom: 1px solid #111;" class="text-right">
                        : Rs. {subtotal:,.2f}<br><br>
                        <span class="bold">: Rs. {total_due:,.2f}</span>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" style="border-bottom: 1px solid #111; padding: 6px;">
                        <span class="bold">Invoice Amount In Words :</span><br><br>
                        {amount_words}
                    </td>
                </tr>
                <tr>
                    <td width="60%" style="border-right: 1px solid #111; padding: 6px;">
                    </td>
                    <td width="20%" style="padding: 6px;">
                        Received<br><br>
                        Balance<br><br>
                        <span class="bold">You Saved</span>
                    </td>
                    <td width="20%" style="padding: 6px;" class="text-right">
                        : Rs. {amount_received:,.2f}<br><br>
                        : Rs. {balance:,.2f}<br><br>
                        <span class="bold">: Rs. {total_discount_amount:,.2f}</span>
                    </td>
                </tr>
            </table>
            
            <!-- Signatory -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px;">
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
                    
                    increment_invoice_no()
                    
                    st.success("Invoice generated successfully!")
                    st.info("Invoice number has been automatically incremented for the next bill.")
                    
                    st.download_button(
                        label="Download PDF Invoice",
                        data=pdf_bytes,
                        file_name=f"Invoice_{inv_no}_{client_name.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
