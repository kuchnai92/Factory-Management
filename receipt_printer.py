import os
import webbrowser
import flet as ft

def print_receipt(record):
    """
    Generates a highly professional HTML receipt for 80x210mm Thermal Printers.
    """
    payee = record.get("payee", "نامعلوم")
    date = record.get("date", "نامعلوم")
    total_earned = record.get("total_earned", 0.0)
    paid_amount = record.get("paid_amount", 0.0)
    net_balance = record.get("net_balance", 0.0)
    items = record.get("items", [])

    rows_html = ""
    for item in items:
        prod = item.get("prod", "")
        b_qty = item.get("b_qty", "0")
        c_qty = item.get("c_qty", "0")
        total = item.get("total", 0.0)
        
        rows_html += f"""
        <tr>
            <td class="col-item">{prod}</td>
            <td class="col-qty">{b_qty}</td>
            <td class="col-qty">{c_qty}</td>
            <td class="col-price">{total:,.0f}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>رسید (Receipt)</title>
    <style>
        @font-face {{
            font-family: 'Jameel Noori Nastaleeq';
        }}
        @page {{ size: 80mm 210mm; margin: 0; }}
        body {{
            font-family: 'Jameel Noori Nastaleeq', Arial, sans-serif;
            width: 72mm; margin: 0 auto; padding: 5mm 2mm;
            box-sizing: border-box; color: #000; line-height: 1.4;
        }}
        .header {{ text-align: center; margin-bottom: 12px; }}
        .header h2 {{ margin: 0; font-size: 26px; font-weight: bold; border-bottom: 2px solid #000; display: inline-block; padding-bottom: 2px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; color: #444; border-bottom: 1px dashed #000; padding-bottom: 8px; display: inline-block; }}
        
        .info-row {{ display: flex; justify-content: space-between; font-size: 15px; margin-top: 10px; margin-bottom: 5px; }}
        .info-label {{ font-weight: normal; color: #333; }}
        .info-value {{ font-weight: bold; font-size: 16px; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 12px; table-layout: fixed; }}
        th {{ border-bottom: 2px solid #000; padding: 4px 0; font-size: 15px; font-weight: bold; }}
        td {{ padding: 4px 0; font-size: 15px; border-bottom: 1px dotted #888; font-weight: bold; }}
        
        .col-item {{ text-align: right; width: 45%; overflow: hidden; }}
        .col-qty {{ text-align: center; width: 15%; }}
        .col-price {{ text-align: left; width: 25%; }}
        
        .totals-container {{ margin-top: 15px; padding-top: 5px; border-top: 2px solid #000; }}
        .total-row {{ display: flex; justify-content: space-between; font-size: 16px; margin-bottom: 5px; font-weight: bold; }}
        .net-balance {{ border-top: 1px solid #000; border-bottom: 2px solid #000; padding: 6px 0; margin-top: 5px; font-size: 18px; }}
        
        .signatures {{ display: flex; justify-content: space-between; margin-top: 40px; }}
        .sig-box {{ width: 45%; text-align: center; border-top: 1px dashed #000; padding-top: 5px; font-size: 14px; font-weight: bold; color: #333; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #555; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>فیکٹری رسید</h2>
        <p>روزانہ ادائیگی کا ریکارڈ</p>
    </div>
    <div class="info-row">
        <div><span class="info-label">تاریخ:</span> <span class="info-value">{date}</span></div>
        <div><span class="info-label">مزدور:</span> <span class="info-value">{payee}</span></div>
    </div>
    <table>
        <thead>
            <tr>
                <th class="col-item">آئٹم</th>
                <th class="col-qty">بڑا</th>
                <th class="col-qty">چھوٹا</th>
                <th class="col-price">رقم</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    <div class="totals-container">
        <div class="total-row"><span>کل کمائی:</span> <span>{total_earned:,.0f}</span></div>
        <div class="total-row"><span>ادا شدہ رقم:</span> <span>{paid_amount:,.0f}</span></div>
        <div class="total-row net-balance"><span>بقیہ کھاتہ:</span> <span>{net_balance:,.0f}</span></div>
    </div>
    <div class="signatures">
        <div class="sig-box">دستخط مزدور</div>
        <div class="sig-box">دستخط مینیجر</div>
    </div>
    <div class="footer">سافٹ ویئر کے ذریعے تیار کردہ کمپیوٹرائزڈ رسید</div>
    <script>window.onload = function() {{ window.print(); }}</script>
</body>
</html>
"""
    file_path = os.path.abspath("receipt.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    webbrowser.open(f"file://{file_path}")

def get_print_button(record):
    return ft.IconButton(
        icon=ft.Icons.PRINT, icon_color=ft.Colors.TEAL_700, 
        tooltip="رسید پرنٹ کریں (Print Receipt)", 
        on_click=lambda e: print_receipt(record)
    )


# --- PREMIUM Z-REPORT LOGIC (WITH PERFECT WORKING WIDTHS) ---
def print_day_summary(date_key, payments, day_total_qty, day_total_amount):
    """
    Generates a highly structured, clean End of Day (Z-Report) for 80x210mm printers.
    """
    total_entries = len(payments)
    total_paid_day = sum(p.get("paid_amount", 0.0) for p in payments)
    
    worker_rows_html = ""
    for p in payments:
        payee = p.get("payee", "نامعلوم")
        earned = p.get("total_earned", 0.0)
        paid = p.get("paid_amount", 0.0)
        worker_rows_html += f"""
        <tr>
            <td class="t-right w-worker">{payee}</td>
            <td class="t-center w-earned">{earned:,.0f}</td>
            <td class="t-left w-paid">{paid:,.0f}</td>
        </tr>
        """

    prod_stats = {}
    for p in payments:
        for item in p.get("items", []):
            name = item.get("prod", "")
            try: c_qty = float(item.get("c_qty", 0) or 0)
            except: c_qty = 0
            try: b_qty = float(item.get("b_qty", 0) or 0)
            except: b_qty = 0
            
            if name not in prod_stats:
                prod_stats[name] = {"c": 0, "b": 0, "t": 0}
            prod_stats[name]["c"] += c_qty
            prod_stats[name]["b"] += b_qty
            prod_stats[name]["t"] += (c_qty + b_qty)

    prod_rows_html = ""
    for name, stats in prod_stats.items():
        prod_rows_html += f"""
        <tr>
            <td class="t-right w-item">{name}</td>
            <td class="t-center w-bqty">{stats['b']:,.0f}</td>
            <td class="t-center w-cqty">{stats['c']:,.0f}</td>
            <td class="t-left w-tqty">{stats['t']:,.0f}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>روزانہ خلاصہ (Daily Summary)</title>
    <style>
        @font-face {{ font-family: 'Jameel Noori Nastaleeq'; }}
        @page {{ size: 80mm 210mm; margin: 0; }} 
        body {{
            font-family: 'Jameel Noori Nastaleeq', Arial, sans-serif;
            width: 72mm; /* Exactly matches the 72mm printable area */
            margin: 0 auto; 
            padding: 5mm 0; /* Exact padding from the perfectly working layout */
            box-sizing: border-box; 
            color: #000; 
            line-height: 1.3;
        }}
        .receipt-wrapper {{ width: 100%; box-sizing: border-box; }} 
        
        .header {{ text-align: center; margin-bottom: 15px; }}
        .header h2 {{ margin: 0; font-size: 24px; font-weight: bold; border-bottom: 2px solid #000; display: inline-block; padding-bottom: 2px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; color: #444; font-weight: bold; }}
        
        .info-box {{ border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 5px 6px; margin-bottom: 10px; }}
        .info-row {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 3px; }}
        .info-label {{ font-weight: normal; color: #333; }}
        .info-value {{ font-weight: bold; font-size: 14px; }}
        
        .section-title {{
            font-size: 14px; font-weight: bold; text-align: center;
            border-top: 1px dashed #000; border-bottom: 1px dashed #000;
            padding: 4px 0; margin-top: 15px; margin-bottom: 5px;
        }}
        
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; table-layout: fixed; }}
        th {{ border-bottom: 2px solid #000; padding: 4px 2px; font-size: 13px; font-weight: bold; }}
        td {{ padding: 4px 2px; font-size: 13px; border-bottom: 1px dotted #888; font-weight: bold; }}
        
        .t-right {{ text-align: right; }}
        .t-left {{ text-align: left; }}
        .t-center {{ text-align: center; }}
        
        /* STRICT COLUMN WIDTHS FROM PERFECT LAYOUT */
        .w-worker {{ width: 38%; overflow: hidden; }} 
        .w-earned {{ width: 31%; }} 
        .w-paid {{ width: 31%; }}
        
        .w-item {{ width: 34%; overflow: hidden; }} 
        .w-bqty {{ width: 22%; }} 
        .w-cqty {{ width: 22%; }} 
        .w-tqty {{ width: 22%; }}
        
        .totals-container {{ margin-top: 15px; padding-top: 5px; border-top: 2px solid #000; }}
        .total-row {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px; font-weight: bold; }}
        .net-balance {{ border-top: 1px solid #000; border-bottom: 2px solid #000; padding-top: 4px; padding-bottom: 4px; margin-top: 4px; font-size: 17px; }}
        
        .end-mark {{ text-align: center; margin-top: 20px; font-size: 14px; font-weight: bold; letter-spacing: 2px; }}
        .footer {{ text-align: center; margin-top: 10px; font-size: 12px; color: #555; }}
    </style>
</head>
<body>
    <div class="receipt-wrapper">
        <div class="header">
            <h2>فیکٹری خلاصہ</h2>
            <p>مکمل روزانہ کی رپورٹ</p>
        </div>
        
        <div class="info-box">
            <div class="info-row">
                <div><span class="info-label">تاریخ:</span> <span class="info-value">{date_key}</span></div>
                <div><span class="info-label">کل اندراج:</span> <span class="info-value">{total_entries}</span></div>
            </div>
        </div>
        
        <div class="section-title">مزدوروں کی تفصیل (Worker Details)</div>
        <table>
            <thead>
                <tr>
                    <th class="t-right w-worker">نام</th>
                    <th class="t-center w-earned">کمائی</th>
                    <th class="t-left w-paid">ادا شدہ</th>
                </tr>
            </thead>
            <tbody>
                {worker_rows_html}
            </tbody>
        </table>

        <div class="section-title">پروڈکٹ کی تفصیل (Item Details)</div>
        <table>
            <thead>
                <tr>
                    <th class="t-right w-item">آئٹم</th>
                    <th class="t-center w-bqty">بڑا</th>
                    <th class="t-center w-cqty">چھوٹا</th>
                    <th class="t-left w-tqty">کل</th>
                </tr>
            </thead>
            <tbody>
                {prod_rows_html}
            </tbody>
        </table>

        <div class="totals-container">
            <div class="total-row">
                <span>کل مقدار (Total Qty):</span>
                <span>{day_total_qty:,.0f}</span>
            </div>
            <div class="total-row">
                <span>کل ادا شدہ (Total Paid):</span>
                <span>{total_paid_day:,.0f}</span>
            </div>
            <div class="total-row net-balance">
                <span>کل رقم (Grand Total):</span>
                <span>{day_total_amount:,.0f}</span>
            </div>
        </div>
        
        <div class="end-mark">*** END OF REPORT ***</div>
        <div class="footer">سافٹ ویئر کے ذریعے تیار کردہ کمپیوٹرائزڈ رپورٹ</div>
    </div>
    <script>window.onload = function() {{ window.print(); }}</script>
</body>
</html>
"""
    file_path = os.path.abspath("summary_receipt.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    webbrowser.open(f"file://{file_path}")

def get_summary_print_button(date_key, payments, day_total_qty, day_total_amount):
    return ft.IconButton(
        icon=ft.Icons.PRINT, 
        icon_color=ft.Colors.BLUE_900, 
        tooltip="دن کا مکمل خلاصہ پرنٹ کریں (Print Full Day Summary)", 
        on_click=lambda e: print_day_summary(date_key, payments, day_total_qty, day_total_amount)
    )