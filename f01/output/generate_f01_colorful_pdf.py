"""
F01 Promotional Margin Leakage - Colorful PDF Report Generator v2.3.0
Generates a premium, visually rich PDF with charts, KPI cards, colored sections.
"""
import io, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF

BRAND_DARK   = (15,  23,  42)
BRAND_BLUE   = (37,  99, 235)
BRAND_CYAN   = (6,  182, 212)
BRAND_GREEN  = (16, 185, 129)
BRAND_AMBER  = (245, 158,  11)
BRAND_RED    = (239,  68,  68)
BRAND_PURPLE = (139,  92, 246)
GRAY_100     = (241, 245, 249)
GRAY_200     = (226, 232, 240)
GRAY_700     = (51,  65,  85)
WHITE        = (255, 255, 255)

_tmp_counter = 0
def _tmp_path():
    global _tmp_counter
    _tmp_counter += 1
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f'_ct_{_tmp_counter}.png')

def fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def _safe(text):
    import re
    text = str(text)
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'(.*?)', r'\1', text)
    text = re.sub(r'\$\True[^$]+\True\True', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    for k,v in {u'\u2014':'-',u'\u2013':'-',u'\u2018':"'",u'\u2019':"'",u'\u201c':'"',u'\u201d':'"',
                u'\u2022':'-',u'\u2026':'...',u'\u2264':'<=',u'\u2265':'>=',u'\u00b1':'+/-',
                u'\u21b3':'->',u'\u00d7':'x',u'\u03a3':'SUM',u'\u2192':'->','-':'-'}.items():
        text = text.replace(k, v)
    text = text.encode('ascii', errors='replace').decode('ascii')
    return text.strip()
