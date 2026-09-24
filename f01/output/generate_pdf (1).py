"""
Generate PDF from Formula F01: Promotional Margin Leakage Validation Report.
Uses fpdf2 for pure-Python PDF generation with support for portrait, landscape tables,
code blocks, and clean typography.
"""

import os
import re
import sys
from fpdf import FPDF

class F01ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            page_w = 267 if self.cur_orientation == 'L' else 180
            self.set_x(15)
            self.cell(page_w, 5, 'Formula F01: Promotional Margin Leakage - Technical Audit Report', align='C')
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def title_page(self):
        self.add_page(orientation='P')
        self.ln(45)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(0, 51, 102)
        self.set_x(15)
        self.cell(180, 11, 'Formula F01: Promotional Margin Leakage', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(0, 80, 140)
        self.set_x(15)
        self.cell(180, 9, 'Production Validation & Technical Audit Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(20)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(70, 70, 70)
        info_lines = [
            'System: Zeitster E-Commerce Margin Scoring Engine',
            'Engine Module: formulas.f01_discount_leakage',
            'Version: 2.0.0 (Production Rebuild)',
            'Evaluation Date: September 2026',
            'Cohort Analyzed: 50,000 Shopify Orders | 600 SKUs',
            'Status: 100% Validated (32/32 Tests Passed | Reconciled)'
        ]
        for line in info_lines:
            self.set_x(15)
            self.cell(180, 7, line, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(25)
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(55, self.get_y(), 155, self.get_y())
        self.ln(10)
        self.set_font('Helvetica', 'I', 9.5)
        self.set_text_color(110, 110, 110)
        self.set_x(15)
        self.cell(180, 6, 'STRICT DATA-GRAIN & FINANCIAL INTEGRITY COMPLIANT', align='C')

    def add_heading(self, text, level=1):
        pw = 267 if self.cur_orientation == 'L' else 180
        self.ln(3)
        if level == 1:
            if self.get_y() > 230:
                self.add_page(orientation=self.cur_orientation)
            self.set_font('Helvetica', 'B', 13)
            self.set_text_color(0, 51, 102)
            self.set_x(15)
            self.multi_cell(pw, 7, text)
            self.set_draw_color(0, 51, 102)
            self.set_line_width(0.3)
            self.line(15, self.get_y() + 1, 15 + pw, self.get_y() + 1)
            self.ln(4)
        elif level == 2:
            if self.get_y() > 240:
                self.add_page(orientation=self.cur_orientation)
            self.set_font('Helvetica', 'B', 11)
            self.set_text_color(0, 70, 130)
            self.set_x(15)
            self.multi_cell(pw, 6, text)
            self.ln(2)
        elif level == 3:
            if self.get_y() > 250:
                self.add_page(orientation=self.cur_orientation)
            self.set_font('Helvetica', 'B', 9.5)
            self.set_text_color(50, 50, 50)
            self.set_x(15)
            self.multi_cell(pw, 5, text)
            self.ln(2)

    def add_body_text(self, text):
        pw = 267 if self.cur_orientation == 'L' else 180
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(30, 30, 30)
        self.set_x(15)
        self.multi_cell(pw, 4.5, text)
        self.ln(1.5)

    def add_bullet(self, text):
        pw = 267 if self.cur_orientation == 'L' else 180
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(30, 30, 30)
        self.set_x(18)
        self.cell(4, 4.5, '-')
        self.multi_cell(pw - 7, 4.5, text)
        self.ln(1)

    def add_code_block(self, code_lines):
        pw = 267 if self.cur_orientation == 'L' else 180
        if self.get_y() > 220:
            self.add_page(orientation=self.cur_orientation)
        self.set_font('Courier', '', 7)
        self.set_fill_color(244, 247, 250)
        self.set_text_color(35, 45, 60)
        for line in code_lines:
            self.set_x(15)
            safe_text = clean_md_formatting(line[:140])
            self.cell(pw, 3.8, safe_text, fill=True, ln=1)
        self.ln(3)

    def add_table(self, headers, rows):
        num_cols = len(headers)
        # Use Landscape page if table has more than 6 columns
        is_wide = num_cols > 6
        target_orient = 'L' if is_wide else 'P'

        if self.cur_orientation != target_orient:
            self.add_page(orientation=target_orient)

        available_width = 267 if self.cur_orientation == 'L' else 180

        # Calculate column weights
        col_widths = []
        for i in range(num_cols):
            max_len = len(str(headers[i]))
            for row in rows:
                if i < len(row):
                    max_len = max(max_len, len(str(row[i])))
            col_widths.append(max(max_len, 4))

        total_weight = sum(col_widths)
        col_widths = [(w / total_weight) * available_width for w in col_widths]

        min_w = 6.5 if is_wide else 15.0
        for i in range(num_cols):
            if col_widths[i] < min_w:
                col_widths[i] = min_w
        total_w = sum(col_widths)
        col_widths = [(w / total_w) * available_width for w in col_widths]

        row_height = 4.2 if is_wide else 5.0
        font_size = 5.5 if num_cols > 15 else (6.5 if is_wide else 7.5)

        if self.get_y() > (175 if self.cur_orientation == 'L' else 255):
            self.add_page(orientation=self.cur_orientation)

        # Header
        self.set_font('Helvetica', 'B', font_size)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.set_x(15)
        for i, h in enumerate(headers):
            txt = clean_md_formatting(str(h))
            max_c = int(col_widths[i] / 1.1)
            if len(txt) > max_c:
                txt = txt[:max_c - 1] + '.'
            self.cell(col_widths[i], row_height + 0.5, txt, border=1, fill=True, align='C')
        self.ln()

        # Rows
        self.set_font('Helvetica', '', font_size)
        self.set_text_color(30, 30, 30)

        for row_idx, row in enumerate(rows):
            if self.get_y() > (180 if self.cur_orientation == 'L' else 260):
                self.add_page(orientation=self.cur_orientation)
                # Re-draw header
                self.set_font('Helvetica', 'B', font_size)
                self.set_fill_color(0, 51, 102)
                self.set_text_color(255, 255, 255)
                self.set_x(15)
                for i, h in enumerate(headers):
                    txt = clean_md_formatting(str(h))
                    max_c = int(col_widths[i] / 1.1)
                    if len(txt) > max_c:
                        txt = txt[:max_c - 1] + '.'
                    self.cell(col_widths[i], row_height + 0.5, txt, border=1, fill=True, align='C')
                self.ln()
                self.set_font('Helvetica', '', font_size)
                self.set_text_color(30, 30, 30)

            if row_idx % 2 == 0:
                self.set_fill_color(243, 247, 252)
            else:
                self.set_fill_color(255, 255, 255)

            self.set_x(15)
            for i in range(num_cols):
                txt = clean_md_formatting(str(row[i])) if i < len(row) else ''
                max_c = int(col_widths[i] / 1.05)
                if len(txt) > max_c:
                    txt = txt[:max_c - 1] + '.'
                align_mode = 'C' if (i == 0 or 'Rank' in headers[0]) else 'L'
                self.cell(col_widths[i], row_height, txt, border=1, fill=True, align=align_mode)
            self.ln()

        self.ln(3)

def clean_md_formatting(text):
    """Remove markdown formatting characters and normalize to safe ASCII."""
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    # LaTeX cleanup
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\mathbf\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\left\(', '(', text)
    text = re.sub(r'\\right\)', ')', text)
    text = re.sub(r'\\times', 'x', text)
    text = re.sub(r'\\le', '<=', text)
    text = re.sub(r'\\ge', '>=', text)
    text = re.sub(r'\\sum', 'sum', text)
    text = re.sub(r'\\max', 'max', text)
    text = text.replace('$$', '')
    text = text.replace('$', '')
    text = text.replace('\u2014', '-')
    text = text.replace('\u2013', '-')
    text = text.replace('\u2018', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u2022', '-')
    text = text.replace('\u2026', '...')
    text = text.replace('\u2714', '[Y]')
    text = text.replace('\u2716', '[N]')
    text = text.replace('\u2705', '[YES]')
    text = text.replace('\u274c', '[NO]')
    text = text.replace('\u2610', '[ ]')
    text = text.replace('\u2264', '<=')
    text = text.replace('\u2265', '>=')
    text = text.replace('\u00b1', '+/-')
    text = text.replace('\u21b3', '->')
    text = text.replace('—', '-')
    text = text.replace('–', '-')
    # Strict ASCII conversion to prevent FPDFUnicodeEncodingException
    text = text.encode('ascii', errors='replace').decode('ascii')
    return text

def parse_and_generate(md_path, pdf_path):
    print(f"Reading markdown from: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pdf = F01ReportPDF()
    pdf.title_page()
    pdf.add_page(orientation='P')

    lines = content.split('\n')
    i = 0
    in_table = False
    in_code_block = False
    table_headers = []
    table_rows = []
    code_lines = []
    skip_header = True

    while i < len(lines):
        line = lines[i]

        # Skip initial title block until first ## heading
        if skip_header:
            if line.startswith('## '):
                skip_header = False
            else:
                i += 1
                continue

        # Code block handling (```)
        if line.strip().startswith('```'):
            if in_code_block:
                pdf.add_code_block(code_lines)
                code_lines = []
                in_code_block = False
            else:
                if in_table:
                    pdf.add_table(table_headers, table_rows)
                    in_table = False
                    table_headers, table_rows = [], []
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Flush table if we've left table context
        if in_table and line.strip() and not line.strip().startswith('|'):
            pdf.add_table(table_headers, table_rows)
            in_table = False
            table_headers = []
            table_rows = []

        # Headings
        if line.startswith('## '):
            if in_table:
                pdf.add_table(table_headers, table_rows)
                in_table = False
                table_headers, table_rows = [], []
            text = clean_md_formatting(line[3:].strip())
            pdf.add_heading(text, level=1)
            i += 1
            continue

        if line.startswith('### '):
            if in_table:
                pdf.add_table(table_headers, table_rows)
                in_table = False
                table_headers, table_rows = [], []
            text = clean_md_formatting(line[4:].strip())
            pdf.add_heading(text, level=2)
            i += 1
            continue

        if line.startswith('#### '):
            if in_table:
                pdf.add_table(table_headers, table_rows)
                in_table = False
                table_headers, table_rows = [], []
            text = clean_md_formatting(line[5:].strip())
            pdf.add_heading(text, level=3)
            i += 1
            continue

        # Horizontal rule
        if line.strip() == '---':
            i += 1
            continue

        # Table rows and headers
        if line.strip().startswith('|') and '|' in line[1:]:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]

            # Check if next line is separator (---|---|---)
            if i + 1 < len(lines) and re.match(r'^[\s|:\-]+$', lines[i + 1]):
                if in_table:
                    pdf.add_table(table_headers, table_rows)
                    table_rows = []
                table_headers = cells
                in_table = True
                i += 2
                continue
            elif in_table:
                table_rows.append(cells)
                i += 1
                continue

        # Bullet points
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            text = clean_md_formatting(line.strip()[2:])
            pdf.add_bullet(text)
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', line.strip()):
            num_match = re.match(r'^(\d+\.)\s*(.*)', line.strip())
            if num_match:
                prefix, rest = num_match.groups()
                text = f"{prefix} {clean_md_formatting(rest)}"
                pdf.add_body_text(text)
            i += 1
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Regular body text
        text = clean_md_formatting(line.strip())
        if text:
            pdf.add_body_text(text)
        i += 1

    # Flush remaining table if any
    if in_table:
        pdf.add_table(table_headers, table_rows)

    if in_code_block and code_lines:
        pdf.add_code_block(code_lines)

    try:
        pdf.output(pdf_path)
        print(f"PDF generated successfully: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    except PermissionError:
        fallback_path = pdf_path.replace(".pdf", "_v2.pdf")
        pdf.output(fallback_path)
        print(f"Original file was locked by an active viewer. Saved successfully to: {fallback_path}")
        print(f"File size: {os.path.getsize(fallback_path) / 1024:.1f} KB")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(script_dir, 'F01_TESTING_DATA_RESULTS.md')
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(script_dir, 'F01_TESTING_DATA_RESULTS.pdf')
    parse_and_generate(md_file, pdf_file)
