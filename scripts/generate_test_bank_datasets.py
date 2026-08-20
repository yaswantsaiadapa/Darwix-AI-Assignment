"""
Script: Generate Standalone Multi-Format Test Datasets for SBI and HDFC Banks
Creates PDF, CSV, HTML, and TXT files for Question 2 evaluation.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_BANKS_DIR = PROJECT_ROOT / "test_data_banks"
HDFC_DIR = TEST_BANKS_DIR / "hdfc"
SBI_DIR = TEST_BANKS_DIR / "sbi"

HDFC_DIR.mkdir(parents=True, exist_ok=True)
SBI_DIR.mkdir(parents=True, exist_ok=True)


def build_hdfc_pdf():
    pdf_path = HDFC_DIR / "hdfc_business_growth_loans.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#002B49'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#004C87'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        spaceAfter=6
    )

    story = [
        Paragraph("HDFC BANK COMMERCIAL & MSME LENDING POLICY MANUAL", title_style),
        Paragraph("<b>Document Reference:</b> HDFC/COMM/POL/2026-V2 | <b>Division:</b> Wholesale & Commercial Banking", body_style),
        Spacer(1, 8),
        Paragraph("1. HDFC Unsecured Business Growth Loan", h2_style),
        Paragraph("HDFC Bank provides collateral-free Business Growth Loans designed for Micro, Small and Medium Enterprises (MSMEs), sole proprietors, partnerships, LLPs, and private limited companies seeking rapid liquidity for capacity expansion, inventory stocking, and business operations.", body_style),
        Paragraph("<b>Loan Quantum:</b> Minimum ₹50,000 up to a maximum of ₹50,00,000 (₹50 Lakhs).<br/>"
                  "<b>Interest Rate:</b> Competitive rack rate from 11.90% to 21.35% per annum based on borrower risk grade and CIBIL score.<br/>"
                  "<b>Repayment Tenure:</b> Flexible tenure ranging from 12 months to 48 months in structured monthly EMIs.<br/>"
                  "<b>Collateral Requirement:</b> Nil. Strictly zero physical asset collateral or third-party guarantee required.", body_style),
        Spacer(1, 8),
        Paragraph("2. Mandatory Borrower Eligibility Criteria", h2_style),
        Paragraph("To qualify for an HDFC Unsecured Business Growth Loan, the applicant enterprise must satisfy:<br/>"
                  "• <b>Business Vintage:</b> Minimum 3 continuous years in the current line of business with 5 years total business experience.<br/>"
                  "• <b>Annual Turnover:</b> Minimum annual gross revenue of ₹40,00,000 (₹40 Lakhs) as per audited financial returns / GST filings.<br/>"
                  "• <b>Profitability:</b> Minimum 2 years of positive profit after tax (PAT).<br/>"
                  "• <b>Bureau Benchmark:</b> CIBIL Commercial / TransUnion score of 700 and above with clean repayment track record.", body_style),
        Spacer(1, 8),
        Paragraph("3. Credit Guarantee Fund Trust for Micro & Small Enterprises (CGTMSE)", h2_style),
        Paragraph("Under the Government of India / SIDBI CGTMSE scheme, HDFC Bank extends collateral-free credit facilities up to <b>₹5.00 Crore (₹500 Lakhs)</b>.<br/>"
                  "• <b>Guarantee Coverage:</b> 75% to 85% credit guarantee backed by the Government of India.<br/>"
                  "• <b>Primary Security:</b> Zero tangible asset mortgage; hypothecation of current assets created out of bank finance.<br/>"
                  "• <b>Requirement:</b> Valid Udyam MSME Registration Certificate is mandatory at the time of loan login.", body_style),
        Spacer(1, 8),
        Paragraph("4. Ineligible Activities & Prohibitions", h2_style),
        Paragraph("HDFC Bank strictly prohibits commercial lending for:<br/>"
                  "• Speculative trading in cryptocurrencies (Bitcoin, Ethereum), digital asset derivatives, or intraday equities.<br/>"
                  "• Gambling, lottery ticket distribution, casino activities, or unregulated chit funds.<br/>"
                  "• Personal retail consumer consumption, luxury holidays, or residential land hoarding.", body_style),
    ]

    doc.build(story)
    print(f"[Generated] {pdf_path}")


def build_hdfc_csv():
    csv_path = HDFC_DIR / "hdfc_loan_against_property_slabs.csv"
    content = """Product_Code,Property_Type,Min_Loan_INR,Max_Loan_INR,Interest_Rate_Range,Max_LTV_Percent,Max_Tenure_Years,Eligible_Borrowers
HDFC-LAP-COM,Commercial Office / Retail Complex,1000000,500000000,9.00% - 11.75% p.a.,65%,15,MSME / Corporates / LLPs
HDFC-LAP-IND,Industrial Shed / Factory Land,2500000,350000000,9.50% - 12.50% p.a.,60%,12,Manufacturing Enterprises
HDFC-LAP-RES,Residential Property (Self-Occupied),1000000,250000000,8.75% - 11.25% p.a.,75%,15,Proprietors & Directors
HDFC-WC-CC,Hypothecation of Stock & Receivables,500000,250000000,Repo + 2.25% to 3.75%,75%,1 (Annual Renewal),Wholesale & Retail Traders
HDFC-CGTMSE-TL,Term Loan (Government Guarantee),100000,50000000,9.25% - 12.50% p.a.,Nil (Collateral-Free),7,Udyam Registered MSMEs
"""
    csv_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {csv_path}")


def build_hdfc_html():
    html_path = HDFC_DIR / "hdfc_msme_portal_export.html"
    content = """<!DOCTYPE html>
<html>
<head><title>HDFC Bank MSME Working Capital & Term Financing Portal</title></head>
<body>
    <!-- BREADCRUMB: Home > Commercial Banking > MSME Products > Working Capital -->
    <header class="site-header">
        <nav class="navbar"><a href="/home">HDFC Home</a> | <a href="/loans">MSME Loans</a> | <a href="/rates">Rate Matrix</a></nav>
        <div class="ad-banner">BANNER AD: Pre-approved Business Credit Lines up to ₹50 Lakhs! Apply in 10 minutes.</div>
    </header>

    <main>
        <h1>HDFC Bank Working Capital & Cash Credit Solutions</h1>
        <p>HDFC Bank offers comprehensive working capital financing facilities to help growing enterprises manage cash flows, purchase raw materials, and finance inventory holding cycles.</p>

        <h2>1. Cash Credit (CC) and Overdraft (OD) Facilities</h2>
        <p>Designed for manufacturing, trading, and service enterprises requiring continuous liquidity. Interest is computed on daily debit balance and billed monthly.</p>

        <h2>2. Key Terms & Security Norms</h2>
        <table border="1" cellpadding="6">
            <tr><th>Facility Type</th><th>Facility Limit</th><th>Benchmark Rate</th><th>Primary Security</th></tr>
            <tr><td>Cash Credit (CC)</td><td>₹5 Lakhs to ₹25 Crore</td><td>EBLR + 1.85% to 3.25%</td><td>Hypothecation of inventory and book debts (up to 90 days)</td></tr>
            <tr><td>Overdraft (OD) against Property</td><td>₹10 Lakhs to ₹15 Crore</td><td>EBLR + 1.50% to 2.75%</td><td>Mortgage of commercial or residential premises</td></tr>
            <tr><td>Letter of Credit (Inland / Import)</td><td>As per drawing power</td><td>Standard Commission</td><td>Underlying imported/procured goods</td></tr>
        </table>
    </main>

    <footer class="site-footer">
        <p>FOOTER NOISE: Copyright 2026 HDFC Bank Ltd. CIN: L65920MH1994PLC080618. ISO 27001 Certified.</p>
    </footer>
</body>
</html>"""
    html_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {html_path}")


def build_hdfc_txt():
    txt_path = HDFC_DIR / "hdfc_eligibility_and_faq.txt"
    content = """# HDFC Bank MSME Lending FAQ & Application Verification SOP
**Document ID**: HDFC-MSME-FAQ-2026

## 1. Frequently Answered Questions (Commercial Lending Desk)
Q: What is the maximum loan amount under HDFC Unsecured Business Growth Loan?
A: HDFC Bank sanctions up to ₹50 Lakhs under the unsecured business growth loan without physical collateral.

Q: Can a newly incorporated startup (less than 1 year old) qualify for an unsecured business loan?
A: No. HDFC policy mandates a minimum operational business vintage of 3 continuous years and minimum ₹40 Lakhs turnover. Startups can apply under CGTMSE collateral-free facilities if sponsored under recognized incubation or Mudra scheme.

Q: Are loans provided for speculative cryptocurrency investments?
A: No. HDFC commercial underwriting guidelines strictly prohibit credit extension for cryptocurrency trading, bitcoin mining, or speculative real estate hoarding.

## 2. Sample Commercial Loan Application (Intake Verification Record)
Applicant Profile:
- Business Legal Name: Falcon Translogistics Private Limited
- Key Director / Applicant: Vikramaditya Singh Rathore
- Applicant Aadhaar: 4321 8765 9876
- Business PAN: FALCON1234F
- Contact Mobile: +91-9823456789
- Business Email: vikram@falcontlogistics.in
- Disbursement Current A/c: 50200012345678
- Requested Facility: ₹35,00,000 (Thirty Five Lakhs)
- Annual Turnover: ₹1,40,00,000 (One Crore Forty Lakhs)
- Years in Operation: 4 Years
"""
    txt_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {txt_path}")


def build_sbi_pdf():
    pdf_path = SBI_DIR / "sbi_msme_commercial_policy.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#005599'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        spaceAfter=6
    )

    story = [
        Paragraph("STATE BANK OF INDIA - MSME COMMERCIAL CREDIT POLICY", title_style),
        Paragraph("<b>Manual ID:</b> SBI/SME/CREDIT/2026-V1 | <b>Issuer:</b> Small & Medium Enterprises Business Unit", body_style),
        Spacer(1, 8),
        Paragraph("1. SBI SME Smart Score & Simplified Small Business Loan", h2_style),
        Paragraph("State Bank of India offers customized credit facilities for Micro, Small and Medium Enterprises for acquiring plant & machinery, constructing factory sheds, and maintaining working capital reserves.", body_style),
        Paragraph("<b>Sanction Limits:</b> ₹10 Lakhs to ₹500 Lakhs (₹5 Crore) under SME Smart Score and CGTMSE schemes.<br/>"
                  "<b>Interest Rate Structure:</b> Linked to SBI External Benchmark Lending Rate (EBLR) + Spread (9.15% to 13.80% p.a.).<br/>"
                  "<b>Repayment Tenure:</b> Term Loans up to 7 years (84 months) with moratorium up to 6 months. Cash Credit lines reviewed annually.<br/>"
                  "<b>Collateral Norms:</b> Collateral-free up to ₹500 Lakhs under CGTMSE credit guarantee coverage.", body_style),
        Spacer(1, 8),
        Paragraph("2. Pradhan Mantri MUDRA Yojana (PMMY) at SBI", h2_style),
        Paragraph("SBI actively finances micro-enterprises under three MUDRA tiers:<br/>"
                  "• <b>Shishu:</b> Loans up to ₹50,000 at 8.65% to 9.75% p.a. (Zero processing fee, Nil margin).<br/>"
                  "• <b>Kishore:</b> Loans from ₹50,001 to ₹5,00,000 at 9.15% to 11.25% p.a. (Margin: 10% to 15%).<br/>"
                  "• <b>Tarun:</b> Loans from ₹5,00,001 to ₹10,00,000 at 9.65% to 12.00% p.a. (Margin: 15%).", body_style),
        Spacer(1, 8),
        Paragraph("3. Borrower Qualification Benchmarks", h2_style),
        Paragraph("• Minimum 2 years of successful business operations with positive net worth.<br/>"
                  "• Minimum annual business turnover of ₹25,00,000 (₹25 Lakhs) for SME Credit lines.<br/>"
                  "• CIBIL score of 675 and above for promoters/guarantors with no past default history.<br/>"
                  "• Udyam Registration and GSTIN compliance mandatory.", body_style),
        Spacer(1, 8),
        Paragraph("4. Statutory Prohibitions & Exclusions", h2_style),
        Paragraph("SBI commercial MSME credit cannot be sanctioned for:<br/>"
                  "• Speculative trading in virtual digital assets, cryptocurrencies, or betting platforms.<br/>"
                  "• Real estate speculation and unapproved personal consumer borrowing.", body_style),
    ]

    doc.build(story)
    print(f"[Generated] {pdf_path}")


def build_sbi_csv():
    csv_path = SBI_DIR / "sbi_sme_interest_rates.csv"
    content = """Product_Code,Product_Name,Min_Amount_INR,Max_Amount_INR,Benchmark_Rate,Spread_Over_EBLR,Final_RoI_Range,Processing_Fee
SBI-SME-001,SME Smart Score Term Loan,1000000,50000000,EBLR (8.65%),0.50% - 2.85%,9.15% - 11.50% p.a.,0.50% of loan amount
SBI-SME-002,Simplified Small Business Loan,1000000,25000000,EBLR (8.65%),1.25% - 3.50%,9.90% - 12.15% p.a.,0.75% of loan amount
SBI-MUDRA-S,MUDRA Shishu Facility,10000,50000,EBLR (8.65%),0.00% - 1.10%,8.65% - 9.75% p.a.,Nil (Waived)
SBI-MUDRA-K,MUDRA Kishore Facility,50001,500000,EBLR (8.65%),0.50% - 2.60%,9.15% - 11.25% p.a.,0.50% of loan amount
SBI-MUDRA-T,MUDRA Tarun Facility,500001,1000000,EBLR (8.65%),1.00% - 3.35%,9.65% - 12.00% p.a.,0.50% of loan amount
SBI-SME-LAP,SME Loan Against Commercial Property,2500000,200000000,EBLR (8.65%),0.35% - 2.20%,9.00% - 10.85% p.a.,0.35% (Max ₹1 Lakh)
"""
    csv_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {csv_path}")


def build_sbi_html():
    html_path = SBI_DIR / "sbi_mudra_portal_export.html"
    content = """<!DOCTYPE html>
<html>
<head><title>State Bank of India - MSME Pradhan Mantri MUDRA Portal</title></head>
<body>
    <!-- BREADCRUMB: Home > SME Banking > Government Schemes > PMMY MUDRA -->
    <header class="site-header">
        <nav class="navbar"><a href="/sbi-home">SBI Home</a> | <a href="/sme">SME Products</a> | <a href="/apply">Apply Online</a></nav>
        <div class="cookie-banner">SBI Cookie Policy: We use cookies to enhance banking navigation. <button>Accept</button></div>
    </header>

    <main>
        <h1>Pradhan Mantri MUDRA Yojana (PMMY) at State Bank of India</h1>
        <p>State Bank of India delivers institutional micro-finance to non-corporate, non-farm small and micro enterprises engaged in manufacturing, trading, and services.</p>

        <h2>1. Three-Tier MUDRA Scheme Architecture</h2>
        <table border="1" cellpadding="6">
            <tr><th>Mudra Category</th><th>Loan Ceiling</th><th>Primary Target Beneficiaries</th><th>Margin Requirement</th></tr>
            <tr><td>Shishu</td><td>Up to ₹50,000</td><td>Micro-enterprises, vegetable vendors, artisans</td><td>Nil</td></tr>
            <tr><td>Kishore</td><td>₹50,001 to ₹5,00,000</td><td>Small shops, fabrication units, service firms</td><td>10% to 15%</td></tr>
            <tr><td>Tarun</td><td>₹5,00,001 to ₹10,00,000</td><td>Established MSMEs scaling production</td><td>15%</td></tr>
        </table>

        <h2>2. Collateral Security Norms</h2>
        <p>In accordance with RBI / Government of India directives, <b>NO COLLATERAL SECURITY</b> or third-party guarantee is required for MUDRA loans up to ₹10 Lakhs. Facilities are covered under the Credit Guarantee Fund for Micro Units (CGFMU).</p>
    </main>

    <footer class="site-footer">
        <p>FOOTER NOISE: State Bank of India. The Banker to Every Indian. Corporate Centre, State Bank Bhavan, Nariman Point, Mumbai 400021.</p>
    </footer>
</body>
</html>"""
    html_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {html_path}")


def build_sbi_txt():
    txt_path = SBI_DIR / "sbi_borrower_kyc_and_faq.txt"
    content = """# State Bank of India MSME Underwriting FAQ & Borrower KYC Checklist
**Document ID**: SBI-SME-CHECKLIST-2026

## 1. Frequently Answered Questions (SBI SME Desk)
Q: What is the maximum loan under SBI SME Smart Score?
A: Up to ₹500 Lakhs (₹5 Crore) for eligible MSMEs.

Q: What is the collateral security norm for loans up to ₹5 Crore?
A: Loans up to ₹5 Crore can be sanctioned without physical collateral under the CGTMSE Credit Guarantee Scheme.

Q: What are the minimum requirements for an SBI Business Loan?
A: Minimum 2 years in business, minimum ₹25 Lakhs turnover, and promoter CIBIL score of 675+.

## 2. Sample SBI Loan Applicant Intake Record (KYC Audit Copy)
Borrower Information:
- Enterprise Name: Swastik Metal Fabrication Works
- Proprietor / Borrower: Suresh Chandra Aggarwal
- Proprietor Aadhaar No: 9876 5432 1098
- Enterprise PAN: SWAST1234F
- Contact Mobile: +91-9811223344
- Business Email: suresh@swastikmetals.in
- SBI Current Account: 30123456789
- Requested Loan Quantum: ₹20,00,000 (Twenty Lakhs under SBI SME Smart Score)
- Annual Turnover: ₹95,00,000 (Ninety Five Lakhs)
- Operational Vintage: 3 Years 8 Months
"""
    txt_path.write_text(content.strip(), encoding="utf-8")
    print(f"[Generated] {txt_path}")


if __name__ == "__main__":
    print("[Generating Standalone Datasets for SBI and HDFC]...")
    build_hdfc_pdf()
    build_hdfc_csv()
    build_hdfc_html()
    build_hdfc_txt()

    build_sbi_pdf()
    build_sbi_csv()
    build_sbi_html()
    build_sbi_txt()
    print("[Complete] Standalone test datasets generated in test_data_banks/.")
