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

        # xhtml2pdf handles absolute local paths well
        logo_path = os.path.abspath("logo.png") if os.path.exists("logo.png") else ""
        sign_path = os.path.abspath("indu_sign.png") if os.path.exists("indu_sign.png") else ""

        logo_html = f'<img src="{logo_path}" style="max-height: 100px;">' if logo_path else '<div style="height: 100px; text-align:center;">LOGO</div>'
        sig_html = f'<img src="{sign_path}" style="max-height: 50px;">' if sign_path else '<br><br><br>'

        discount_html = ""
        if discount_percent > 0:
            discount_html = f"""
            <tr>
                <td style="padding: 4px 8px;">Discount ({discount_percent:g}%)</td>
                <td class="text-right" style="padding: 4px 8px;">: - ₹ {discount_amount:,.2f}</td>
            </tr>
            """

        # HTML Template optimized for xhtml2pdf
        html_template = f"""
        <html>
        <head>
        <style>
            @page {{ size: A4; margin: 1.5cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #111; }}
            .invoice-header {{ text-align: center; font-size: 18pt; font-weight: bold; margin-bottom: 15px; }}
            .box {{ border: 1px solid #111; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td, th {{ padding: 6px 8px; vertical-align: top; }}
            .border-bottom {{ border-bottom: 1px solid #111; }}
            .border-right {{ border-right: 1px solid #111; }}
            .border-top {{ border-top: 1px solid #111; }}
            .bg-light {{ background-color: #f4f2f5; font-weight: bold; }}
            .text-right {{ text-align: right; }}
            .text-center {{ text-align: center; }}
            .bold {{ font-weight: bold; }}
        </style>
        </head>
        <body>
            <div class="invoice-header">Tax Invoice</div>
            
            <div class="box">
                <!-- Clinic Header -->
                <table class="border-bottom">
                    <tr>
                        <td style="width: 25%; text-align: center;" class="border-right">{logo_html}</td>
                        <td style="width: 75%; padding-left: 15px; vertical-align: middle;">
                            <span style="font-size: 16pt; font-weight: bold; color: #222;">JesRa Electrolysis</span><br><br>
                            <span style="color: #444;">No.414/69, 9th main, Vijayanagar, Bangalore</span><br><br>
                            Phone: <strong>9964847715</strong> &nbsp;&nbsp;&nbsp;&nbsp; Email: <strong>jesra.electrolysis@gmail.com</strong>
                        </td>
                    </tr>
                </table>

                <!-- Bill To -->
                <table class="border-bottom">
                    <tr>
                        <td class="bg-light border-right" style="width: 50%;">Bill To:</td>
                        <td class="bg-light" style="width: 50%;">Invoice Details:</td>
                    </tr>
                    <tr>
                        <td class="border-right">
                            <span class="bold" style="font-size: 11pt;">{client_name.title()}</span><br><br>
                            Contact No: <span class="bold">{contact_no}</span>
                        </td>
                        <td>
                            No: <span class="bold">{inv_no}</span><br><br>
                            Date: <span class="bold">{date_str}</span>
                        </td>
                    </tr>
                </table>

                <!-- Items -->
                <table class="border-bottom">
                    <tr class="bg-light">
                        <td class="border-right border-bottom text-center" style="width: 5%;">#</td>
                        <td class="border-right border-bottom" style="width: 32%;">Item Name</td>
                        <td class="border-right border-bottom" style="width: 14%;">HSN/ SAC</td>
                        <td class="border-right border-bottom text-right" style="width: 12%;">Quantity</td>
                        <td class="border-right border-bottom text-center" style="width: 9%;">Unit</td>
                        <td class="border-right border-bottom text-right" style="width: 14%;">Price/ Unit (₹)</td>
                        <td class="border-bottom text-right" style="width: 14%;">Amount(₹)</td>
                    </tr>
                    <tr>
                        <td class="border-right text-center">1</td>
                        <td class="border-right">Electrolysis Treatment</td>
                        <td class="border-right"></td>
                        <td class="border-right text-right">{hours_qty:.2f}</td>
                        <td class="border-right text-center">Hur</td>
                        <td class="border-right text-right">₹ {base_rate * 2:,.2f}</td>
                        <td class="text-right">₹ {service_amount:,.2f}</td>
                    </tr>
                    {"<tr><td class='border-right text-center'>2</td><td class='border-right'>Probe</td><td class='border-right'></td><td class='border-right text-right'>1.00</td><td class='border-right text-center'>-</td><td class='border-right text-right'>₹ " + f"{probe_cost:,.2f}</td><td class='text-right'>₹ {probe_cost:,.2f}</td></tr>" if probe_cost > 0 else ""}
                    <tr>
                        <td class="border-right"><br><br><br><br><br><br><br><br></td>
                        <td class="border-right"></td><td class="border-right"></td><td class="border-right"></td><td class="border-right"></td><td class="border-right"></td><td></td>
                    </tr>
                    <tr>
                        <td colspan="3" class="border-top border-right bold">Total</td>
                        <td class="border-top border-right bold text-right">{total_qty:.2f}</td>
                        <td class="border-top border-right"></td>
                        <td class="border-top border-right"></td>
                        <td class="border-top bold text-right">₹ {subtotal:,.2f}</td>
                    </tr>
                </table>

                <!-- Summary -->
                <table class="border-bottom">
                    <tr>
                        <td style="width: 52%;" class="border-right"></td>
                        <td style="width: 48%; padding: 0;">
                            <table>
                                <tr>
                                    <td style="padding: 4px 8px;">Sub Total</td>
                                    <td class="text-right" style="padding: 4px 8px;">: ₹ {subtotal:,.2f}</td>
                                </tr>
                                {discount_html}
                                <tr>
                                    <td class="border-top bold" style="padding: 4px 8px;">Total</td>
                                    <td class="border-top bold text-right" style="padding: 4px 8px;">: ₹ {total_due:,.2f}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

                <!-- Words -->
                <div class="border-bottom" style="padding: 8px;">
                    <span class="bold">Invoice Amount In Words :</span><br>
                    {amount_words}
                </div>

                <!-- Footer -->
                <table>
                    <tr>
                        <td style="width: 52%;" class="border-right">
                            <span class="bold">Description:</span><br>
                            {description}
                        </td>
                        <td style="width: 48%; padding: 0;">
                            <table>
                                <tr>
                                    <td style="padding: 4px 8px;">Received</td>
                                    <td class="text-right" style="padding: 4px 8px;">: ₹ {amount_received:,.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 8px;">Balance</td>
                                    <td class="text-right" style="padding: 4px 8px;">: ₹ {balance:,.2f}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Signatory -->
            <table style="margin-top: 10px;">
                <tr>
                    <td style="width: 60%;"></td>
                    <td style="width: 40%; text-align: right;">
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
                # Generate PDF using pure python (xhtml2pdf) directly into memory
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
