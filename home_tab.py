import flet as ft
import data_store

URDU_FONT = "Jameel Noori Nastaleeq"

def format_num(val):
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else f"{f:,.2f}"
    except: return "0"

class HomeTab(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        self.padding = ft.padding.only(top=30, left=10, right=10, bottom=20) 
        self.is_built = False 
        self.last_version = 0 
        self.popup_cache = {} 
        
        self.error_text = ft.Text("", color=ft.Colors.RED_700, size=16, weight=ft.FontWeight.BOLD)
        
        self.popup_title = ft.Text("", size=30, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_900, text_align=ft.TextAlign.RIGHT)
        self.popup_list = ft.ListView(spacing=15)
        self.active_dialog = ft.AlertDialog(
            title=self.popup_title, 
            content=ft.Container(content=self.popup_list, width=450, height=400, padding=10), 
            actions=[ft.ElevatedButton("بند کریں (Close)", icon=ft.Icons.CLOSE, color=ft.Colors.RED_900, bgcolor=ft.Colors.RED_50, style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD)), on_click=self.close_popup)], 
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.main_page.overlay.append(self.active_dialog)

        self.header_row = ft.Row([ft.Text("فیکٹری کا ڈیش بورڈ (Factory Dashboard)", size=34, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_900)], alignment=ft.MainAxisAlignment.END)
        
        self.summary_list = ft.Column(spacing=20)
        self.content = ft.ListView(expand=True, spacing=15, controls=[self.header_row, self.error_text, ft.Divider(thickness=2, color=ft.Colors.BLUE_100), self.summary_list])

        self.load_data()
        self.is_built = True

    def display_popup(self, title_text, rows):
        try:
            self.popup_title.value = title_text
            self.popup_list.controls = rows
            self.active_dialog.open = True
            
            if self.active_dialog.page: self.active_dialog.update()
            else: self.main_page.update()
        except Exception as ex: 
            self.error_text.value = f"Popup Error: {str(ex)}"
            try: self.update()
            except: pass

    def close_popup(self, e):
        try:
            self.active_dialog.open = False
            if self.active_dialog.page: self.active_dialog.update()
        except: pass

    def create_kpi_card(self, title, value, icon, bg_color, text_color, on_click=None):
        return ft.Container(content=ft.Column([ft.Row([ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=text_color, font_family=URDU_FONT), ft.Icon(icon, color=text_color, size=36)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text(value, size=40, weight=ft.FontWeight.BOLD, color=text_color, font_family=URDU_FONT)], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=10), bgcolor=bg_color, padding=25, border_radius=15, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.Colors.BLUE_GREY_100, offset=ft.Offset(0, 4)), on_click=on_click, ink=True if on_click else False)

    def create_month_stat(self, title, value, text_color, bg_color, on_click=None):
        return ft.Container(content=ft.Column([ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600, font_family=URDU_FONT), ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=text_color, font_family=URDU_FONT)], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2), padding=20, expand=True, bgcolor=bg_color, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_200), on_click=on_click, ink=True if on_click else False)

    def show_product_breakdown(self, e, title, prod_dict):
        cache_key = f"prod_{title}"
        if cache_key not in self.popup_cache:
            rows = [ft.Container(content=ft.Column([ft.Row([ft.Text(format_num(stats["total"]), size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.PURPLE_800), ft.Text(f" :{p_name}", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLACK)], alignment=ft.MainAxisAlignment.END), ft.Row([ft.Text(f"بڑا ڈرم: {format_num(stats['barha'])}", size=20, font_family=URDU_FONT, color=ft.Colors.GREY_600), ft.Text("|", size=20, color=ft.Colors.GREY_400), ft.Text(f"چھوٹا ڈرم: {format_num(stats['chota'])}", size=20, font_family=URDU_FONT, color=ft.Colors.GREY_600)], alignment=ft.MainAxisAlignment.END), ft.Divider(height=1, color=ft.Colors.GREY_200)], spacing=5)) for p_name, stats in prod_dict.items() if stats["total"] > 0]
            if not rows: rows.append(ft.Text("کوئی ڈیٹا موجود نہیں", size=22, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT))
            self.popup_cache[cache_key] = rows
            
        self.display_popup(title, self.popup_cache[cache_key])

    def show_labour_breakdown(self, e, title, labour_dict, stat_key):
        cache_key = f"labour_{title}_{stat_key}"
        if cache_key not in self.popup_cache:
            rows = [ft.Container(content=ft.Column([ft.Row([ft.Text(f"{stats[stat_key]:,.0f}", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=(ft.Colors.GREEN_700 if stat_key == "earned" else (ft.Colors.BLUE_700 if stat_key == "paid" else ft.Colors.ORANGE_700))), ft.Text(f" :{l_name}", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLACK)], alignment=ft.MainAxisAlignment.END), ft.Divider(height=1, color=ft.Colors.GREY_200)], spacing=5)) for l_name, stats in sorted(labour_dict.items(), key=lambda x: x[1][stat_key], reverse=True) if abs(stats[stat_key]) > 0.1]
            if not rows: rows.append(ft.Text("کوئی ڈیٹا موجود نہیں", size=22, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT))
            self.popup_cache[cache_key] = rows
            
        self.display_popup(title, self.popup_cache[cache_key])

    def load_data(self):
        if self.last_version == data_store.data_version: return
        self.last_version = data_store.data_version
        
        self.popup_cache.clear() 
        
        all_records = data_store.history_payments + data_store.daily_ledger
        new_controls = [] 
        
        if not all_records:
            new_controls.append(ft.Container(content=ft.Column([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=100, color=ft.Colors.GREY_300), ft.Text("ابھی تک کوئی ریکارڈ موجود نہیں ہے۔", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.GREY_500)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=50))
            self.summary_list.controls = new_controls
            if self.is_built: 
                try: self.summary_list.update()
                except: pass
            return

        monthly_data = {}; overall_earned = overall_paid = overall_qty = 0.0; overall_products = {}; overall_labour = {}

        for r in all_records:
            date_str = r.get("date", ""); 
            if len(date_str) < 7: continue
            month_key = date_str[:7]; payee = r.get("payee", "نامعلوم")
            if month_key not in monthly_data: monthly_data[month_key] = {"earned": 0.0, "paid": 0.0, "balance": 0.0, "qty": 0.0, "count": 0, "products": {}, "labour": {}}
            earned, paid, balance = r.get("total_earned", 0.0), r.get("paid_amount", 0.0), r.get("net_balance", 0.0)

            for d in [overall_labour, monthly_data[month_key]["labour"]]:
                if payee not in d: d[payee] = {"earned": 0.0, "paid": 0.0, "balance": 0.0}
                d[payee]["earned"] += earned; d[payee]["paid"] += paid; d[payee]["balance"] += balance

            for item in r.get("items", []):
                try:
                    c, b = float(item.get("c_qty", 0) or 0), float(item.get("b_qty", 0) or 0)
                    prod_name = item.get("prod", "نامعلوم")
                    for d in [overall_products, monthly_data[month_key]["products"]]:
                        if prod_name not in d: d[prod_name] = {"total": 0.0, "chota": 0.0, "barha": 0.0}
                        d[prod_name]["total"] += (c + b); d[prod_name]["chota"] += c; d[prod_name]["barha"] += b
                    monthly_data[month_key]["qty"] += (c + b); overall_qty += (c + b)
                except: pass
            monthly_data[month_key]["earned"] += earned; monthly_data[month_key]["paid"] += paid; monthly_data[month_key]["balance"] += balance; monthly_data[month_key]["count"] += 1
            overall_earned += earned; overall_paid += paid

        overall_balance = sum(d["balance"] for d in overall_labour.values())

        new_controls.append(ft.Text("مکمل فیکٹری خلاصہ (All-Time Summary)", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT))
        new_controls.append(ft.Row([self.create_kpi_card("کل رقم", f"{overall_earned:,.0f}", ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.GREEN_50, ft.Colors.GREEN_900, lambda e: self.show_labour_breakdown(e, "مکمل رقم (تفصیل)", overall_labour, "earned")), self.create_kpi_card("کل مقدار", format_num(overall_qty), ft.Icons.INVENTORY_2_OUTLINED, ft.Colors.PURPLE_50, ft.Colors.PURPLE_900, lambda e: self.show_product_breakdown(e, "مکمل مقدار (تفصیل)", overall_products))], spacing=25))
        new_controls.append(ft.Row([self.create_kpi_card("بقیہ کھاتہ", f"{overall_balance:,.0f}", ft.Icons.ACCOUNT_BALANCE, ft.Colors.ORANGE_50, ft.Colors.ORANGE_900, lambda e: self.show_labour_breakdown(e, "مکمل بقیہ کھاتہ (تفصیل)", overall_labour, "balance")), self.create_kpi_card("ادا شدہ رقم", f"{overall_paid:,.0f}", ft.Icons.PAYMENTS_OUTLINED, ft.Colors.BLUE_50, ft.Colors.BLUE_900, lambda e: self.show_labour_breakdown(e, "مکمل ادا شدہ رقم (تفصیل)", overall_labour, "paid"))], spacing=25))
        new_controls.append(ft.Divider(height=25, color=ft.Colors.TRANSPARENT))
        new_controls.append(ft.Text("ماہانہ تفصیلات (Monthly Breakdown)", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_800, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT))

        month_names = {"01":"جنوری","02":"فروری","03":"مارچ","04":"اپریل","05":"مئی","06":"جون","07":"جولائی","08":"اگست","09":"ستمبر","10":"اکتوبر","11":"نومبر","12":"دسمبر"}
        for m_key in sorted(monthly_data.keys(), reverse=True):
            data = monthly_data[m_key]; p = m_key.split("-"); display = f"{month_names.get(p[1],p[1])} {p[0]}"
            new_controls.append(ft.Container(content=ft.Column([ft.Row([ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE_700, size=32), ft.Text(display, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900, font_family=URDU_FONT)], spacing=10), ft.Container(expand=True), ft.Text(f"اندراج کی تعداد: {data['count']}", size=20, font_family=URDU_FONT, color=ft.Colors.GREY_500)]), ft.Divider(color=ft.Colors.BLUE_100), ft.Row([self.create_month_stat("بقیہ کھاتہ", f"{data['balance']:,.0f}", ft.Colors.ORANGE_700, ft.Colors.ORANGE_50, lambda e, d=data['labour']: self.show_labour_breakdown(e, f"{display} بقیہ کھاتہ", d, "balance")), self.create_month_stat("ادا شدہ رقم", f"{data['paid']:,.0f}", ft.Colors.BLUE_700, ft.Colors.BLUE_50, lambda e, d=data['labour']: self.show_labour_breakdown(e, f"{display} ادا شدہ", d, "paid")), self.create_month_stat("کل رقم", f"{data['earned']:,.0f}", ft.Colors.GREEN_700, ft.Colors.GREEN_50, lambda e, d=data['labour']: self.show_labour_breakdown(e, f"{display} کل رقم", d, "earned")), self.create_month_stat("کل مقدار", format_num(data['qty']), ft.Colors.PURPLE_700, ft.Colors.PURPLE_50, lambda e, d=data['products']: self.show_product_breakdown(e, f"{display} کل مقدار", d))], spacing=15)]), padding=25, bgcolor=ft.Colors.WHITE, border=ft.border.all(1, ft.Colors.BLUE_GREY_100), border_radius=15, shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLUE_GREY_50, offset=ft.Offset(0, 2))))
            
        self.summary_list.controls = new_controls 
        if self.is_built: 
            try: self.summary_list.update() 
            except Exception: pass