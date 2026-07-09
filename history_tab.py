import flet as ft
import data_store
import datetime
import receipt_printer 

URDU_FONT = "Jameel Noori Nastaleeq"

def format_num(val):
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else f"{f:.2f}"
    except:
        return "0"

def safe_parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return datetime.date.min

class HistoryTab(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        
        self.current_view = "dates" 
        self.current_detail_date = None
        
        self.search_date = ft.TextField(
            label="تاریخ تلاش (Search Date)", width=150, value=str(datetime.date.today()), dense=True,
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            on_submit=self.perform_search 
        )
        self.search_today_btn = ft.IconButton(
            icon=ft.Icons.TODAY, tooltip="آج (Today)", icon_color=ft.Colors.BLUE_700, 
            icon_size=30, on_click=self.set_search_today
        )
        self.search_btn = ft.ElevatedButton(
            "تلاش کریں", icon=ft.Icons.SEARCH, on_click=self.perform_search, 
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE,
            style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD))
        )
        self.show_all_btn = ft.ElevatedButton(
            "سب دکھائیں", on_click=self.show_all, 
            bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK,
            style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD))
        )
        
        self.search_row = ft.Row([
            self.show_all_btn, 
            self.search_btn, 
            self.search_today_btn, 
            self.search_date
        ], alignment=ft.MainAxisAlignment.START)

        self.view_container = ft.Container(expand=True)
        
        self.content = ft.Column([
            ft.Row([
                self.search_row,
                ft.Text("محفوظ شدہ ریکارڈ (History)", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(thickness=2),
            self.view_container
        ], expand=True)

    def set_search_today(self, e):
        self.search_date.value = str(datetime.date.today())
        try: self.search_date.update()
        except: pass
        self.perform_search(e)

    def perform_search(self, e):
        self.show_dates_view(filter_date=self.search_date.value)

    def show_all(self, e):
        self.search_date.value = ""
        try: self.search_date.update()
        except: pass
        self.show_dates_view(filter_date=None)

    def load_data(self):
        if getattr(self, 'current_view', 'dates') == "details":
            self.show_detail_view(self.current_detail_date)
        else:
            filter_val = self.search_date.value if self.search_date.value and self.search_date.value.strip() != "" else None
            self.show_dates_view(filter_date=filter_val)

    # --- UPDATED: Calculates remaining balance explicitly ---
    def get_day_summary(self, payments):
        day_total_amount = sum(p.get("total_earned", 0.0) for p in payments)
        day_total_balance = sum(p.get("net_balance", 0.0) for p in payments)
        day_total_qty = 0.0
        product_totals = {}

        for p in payments:
            for item in p.get("items", []):
                try:
                    qty = float(item.get("c_qty", 0)) + float(item.get("b_qty", 0))
                    day_total_qty += qty
                    prod_name = item.get("prod", "نامعلوم")
                    product_totals[prod_name] = product_totals.get(prod_name, 0.0) + qty
                except:
                    pass
        return product_totals, day_total_qty, day_total_amount, day_total_balance

    def show_dates_view(self, filter_date=None):
        self.current_view = "dates" 
        self.search_row.visible = True
        
        grouped_data = {}
        for payment in data_store.history_payments:
            d = payment['date']
            if filter_date and filter_date.strip() != "" and d != filter_date:
                continue
            if d not in grouped_data:
                grouped_data[d] = []
            grouped_data[d].append(payment)

        list_view = ft.ListView(expand=True, spacing=15)

        sorted_dates = sorted(grouped_data.keys(), key=safe_parse_date, reverse=True)

        for date_key in sorted_dates:
            payments = grouped_data[date_key]
            product_totals, day_total_qty, day_total_amount, day_total_balance = self.get_day_summary(payments)
            
            stats_blocks = []
            for prod_name, qty in product_totals.items():
                stats_blocks.append(
                    ft.Text(f"{prod_name}: {format_num(qty)}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800, font_family=URDU_FONT)
                )
            
            stats_blocks.append(ft.Text("|", size=18, color=ft.Colors.GREY_400))
            
            # --- NEW: Shows Warning if Balance Left over ---
            if abs(day_total_balance) > 0.1:
                stats_blocks.append(
                    ft.Text(f"بقایا جات: {day_total_balance:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600, font_family=URDU_FONT)
                )
                stats_blocks.append(ft.Text("|", size=18, color=ft.Colors.GREY_400))

            stats_blocks.extend([
                ft.Text(f"کل مقدار: {format_num(day_total_qty)}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_700, font_family=URDU_FONT),
                ft.Text(f"کل رقم: {day_total_amount:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700, font_family=URDU_FONT),
                ft.Text(f"کل اندراج: {len(payments)}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, font_family=URDU_FONT),
            ])

            stats_row = ft.Row(stats_blocks, spacing=20, wrap=True, alignment=ft.MainAxisAlignment.END)

            date_card = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE_700, size=30),
                        ft.Text(f"تاریخ: {date_key}", weight=ft.FontWeight.BOLD, size=24, color=ft.Colors.BLUE_900, font_family=URDU_FONT),
                    ], spacing=10),
                    
                    ft.Container(expand=True),
                    stats_row, 
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=ft.Colors.BLUE_400)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(2, ft.Colors.BLUE_100),
                border_radius=10,
                ink=True, 
                on_click=lambda e, d=date_key: self.show_detail_view(d)
            )
            list_view.controls.append(date_card)

        self.view_container.content = list_view
        try: self.update()
        except: pass

    # --- NEW: Settle old balances ---
    def settle_history_payment(self, record, date_key):
        record['paid_amount'] = record['total_earned']
        record['net_balance'] = 0.0
        data_store.save_data()
        self.show_detail_view(date_key)
        try: self.update()
        except: pass

    def show_detail_view(self, date_key):
        self.current_view = "details" 
        self.current_detail_date = date_key
        self.search_row.visible = False
        
        list_view = ft.ListView(expand=True, spacing=10)
        
        payments = [p for p in reversed(data_store.history_payments) if p['date'] == date_key]

        product_totals, day_total_qty, day_total_amount, day_total_balance = self.get_day_summary(payments)
        
        summary_blocks = []
        for prod_name, qty in product_totals.items():
            summary_blocks.append(ft.Text(f"{prod_name}: {format_num(qty)}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800, font_family=URDU_FONT))
            
        if abs(day_total_balance) > 0.1:
            summary_blocks.extend([
                ft.Text("|", size=20, color=ft.Colors.GREY_400),
                ft.Text(f"بقایا جات: {day_total_balance:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600, font_family=URDU_FONT)
            ])
            
        summary_blocks.extend([
            ft.Text("|", size=20, color=ft.Colors.GREY_400),
            ft.Text(f"کل مقدار: {format_num(day_total_qty)}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800, font_family=URDU_FONT),
            ft.Text(f"کل رقم: {day_total_amount:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800, font_family=URDU_FONT),
            ft.Text(f"کل اندراج: {len(payments)}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800, font_family=URDU_FONT),
        ])

        summary_print_btn = receipt_printer.get_summary_print_button(
            date_key, payments, day_total_qty, day_total_amount
        )

        summary_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    summary_print_btn,
                    ft.Text("آج کا خلاصہ (Day Summary)", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900, font_family=URDU_FONT),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Divider(height=1, color=ft.Colors.BLUE_200),
                ft.Row(summary_blocks, spacing=25, wrap=True, alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.BLUE_50, 
            border=ft.border.all(2, ft.Colors.BLUE_200),
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )
        
        list_view.controls.append(summary_card)

        for payment in payments:
            product_blocks = []
            for item in payment["items"]:
                product_blocks.append(
                    ft.Text(f"{item['prod']} (چھوٹا: {format_num(item['c_qty'])} - بڑا: {format_num(item['b_qty'])})", 
                            size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT)
                )
            
            products_row = ft.Row(product_blocks, spacing=40, wrap=True, alignment=ft.MainAxisAlignment.END, expand=True)
            
            print_btn = receipt_printer.get_print_button(payment)
            
            row_controls = [print_btn]

            # --- NEW: Settle Button if History Record is Unpaid ---
            if abs(payment.get('net_balance', 0.0)) > 0.1:
                pay_btn = ft.ElevatedButton(
                    "برابر کریں", icon=ft.Icons.DONE_ALL, 
                    color=ft.Colors.WHITE, bgcolor=ft.Colors.ORANGE_600, 
                    on_click=lambda e, r=payment, d=date_key: self.settle_history_payment(r, d),
                    style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=14, weight=ft.FontWeight.BOLD))
                )
                row_controls.append(pay_btn)

            row_controls.extend([
                ft.Text(f"بقیہ: {payment['net_balance']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLACK, font_family=URDU_FONT),
                ft.Text(f"ادا شدہ: {payment['paid_amount']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.RED_700, font_family=URDU_FONT),
                ft.Text(f"اضافی/کٹوتی: {payment.get('extra_amount', 0.0):.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.ORANGE_700, font_family=URDU_FONT),
                ft.Text(f"کل: {payment['total_earned']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_700, font_family=URDU_FONT),
                products_row, 
                ft.Text(f"{payment['payee']}", weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLUE_900, width=150, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT),
            ])
            
            card = ft.Container(
                content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15, border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=8, bgcolor=ft.Colors.WHITE
            )
            list_view.controls.append(card)

        back_btn = ft.ElevatedButton(
            "واپس (Back)", icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.show_dates_view(),
            bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK,
            style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD))
        )
        
        header = ft.Row([
            back_btn,
            ft.Text(f"تفصیلات برائے تاریخ: {date_key}", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900, font_family=URDU_FONT)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.view_container.content = ft.Column([
            header,
            ft.Divider(thickness=2),
            list_view
        ], expand=True)
        
        try: self.update()
        except: pass