import flet as ft
import data_store
import uuid
import datetime
import receipt_printer

URDU_FONT = "Jameel Noori Nastaleeq"

def clean_qty(val_str):
    try:
        if not val_str or str(val_str).strip() == "": return "0"
        f = float(val_str)
        return str(int(f)) if f.is_integer() else str(f)
    except: 
        return "0"

def format_num(val):
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else f"{f:.2f}"
    except:
        return "0"

class PaymentTab(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        
        self.product_prices = {}
        self.product_names = []
        
        self.auto_save_old_dates()
        
        self.date_input = ft.TextField(
            label="تاریخ (Date)", width=150, value=str(datetime.date.today()), dense=True,
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            on_submit=self.on_date_enter 
        )
        self.today_btn = ft.IconButton(icon=ft.Icons.TODAY, tooltip="آج (Today)", icon_color=ft.Colors.BLUE_700, icon_size=30, on_click=self.set_to_today)

        self.save_day_btn = ft.ElevatedButton("محفوظ کریں (Save)", icon=ft.Icons.SAVE, on_click=self.save_day_data, bgcolor=ft.Colors.BLACK87, color=ft.Colors.WHITE, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD)))

        self.header_summary = ft.Container(expand=True)

        self.header_row = ft.Row([
            ft.Row([self.save_day_btn, self.today_btn, self.date_input], alignment=ft.MainAxisAlignment.START),
            self.header_summary, 
            ft.Text("روزانہ کی ادائیگی", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.labour_dd = ft.Dropdown(label="مزدور کا نام (Name)", width=300, text_size=21, text_style=ft.TextStyle(size=21, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT), label_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), on_focus=self.refresh_dropdowns_event)

        self.paid_input = ft.TextField(label="ادا کردہ رقم (Paid)", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700, font_family=URDU_FONT), label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), on_submit=self.make_ledger, on_focus=self.clear_zero, on_blur=lambda e: self.restore_zero(e, None))
        
        self.add_item_btn = ft.ElevatedButton("مزید آئٹم +", icon=ft.Icons.ADD, on_click=self.add_new_row_event, bgcolor=ft.Colors.BLUE_100, color=ft.Colors.BLUE_900, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD)))

        self.top_row = ft.Row([self.paid_input, ft.Row([self.add_item_btn, self.labour_dd])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.items_column = ft.Column(spacing=10)
        self.grand_total_text = ft.Text("مکمل حساب: 0.00", weight=ft.FontWeight.BOLD, size=24, color=ft.Colors.GREEN_800, font_family=URDU_FONT)
        
        self.make_ledger_btn = ft.ElevatedButton("لیجر میں محفوظ کریں", icon=ft.Icons.ADD_CARD, on_click=self.make_ledger, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD)))
        
        self.ledger_list = ft.Column(spacing=10) 

        self.content = ft.Column([
            self.header_row, ft.Divider(color=ft.Colors.BLUE_GREY_200, thickness=2), self.top_row,
            ft.Divider(height=1, color=ft.Colors.GREY_300), self.items_column, ft.Divider(height=1, color=ft.Colors.GREY_300),
            ft.Row([self.make_ledger_btn, self.grand_total_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=ft.Colors.BLUE_GREY_200, thickness=2), ft.Text("عارضی لیجر (Temporary Ledger):", size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            self.ledger_list
        ], scroll=ft.ScrollMode.AUTO)

        self.confirm_dlg = ft.AlertDialog(
            title=ft.Text("تصدیق کریں (Confirm)", weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.RED_700, text_align=ft.TextAlign.RIGHT),
            content=ft.Text("", size=18, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT),
            actions=[
                ft.TextButton("نہیں (No)"),
                ft.ElevatedButton("ہاں، ڈیلیٹ کریں (Yes, Delete)", bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.main_page.overlay.append(self.confirm_dlg)

        self.refresh_dropdowns(None)
        self.reset_form()
        self.load_visual_ledger()

    def confirm_delete(self, title_text, on_confirm_action):
        self.confirm_dlg.content.value = title_text
        
        def close_dlg(e):
            self.confirm_dlg.open = False
            self.main_page.update()

        def confirm_action(e):
            self.confirm_dlg.open = False
            self.main_page.update()
            on_confirm_action()

        self.confirm_dlg.actions[0].on_click = close_dlg
        self.confirm_dlg.actions[1].on_click = confirm_action
        
        self.confirm_dlg.open = True
        self.main_page.update()

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
                except: pass
        return product_totals, day_total_qty, day_total_amount, day_total_balance

    def auto_save_old_dates(self):
        today_str = str(datetime.date.today())
        old_records = [r for r in data_store.daily_ledger if r["date"] != today_str]
        if not old_records: return
        for daily_record in old_records:
            existing_history = next((r for r in data_store.history_payments if r["payee"] == daily_record["payee"] and r["date"] == daily_record["date"]), None)
            if existing_history:
                for new_item in daily_record["items"]:
                    matching = next((i for i in existing_history["items"] if i["prod"] == new_item["prod"]), None)
                    if matching:
                        matching["c_qty"] = clean_qty(float(matching["c_qty"]) + float(new_item["c_qty"]))
                        matching["b_qty"] = clean_qty(float(matching["b_qty"]) + float(new_item["b_qty"]))
                        matching["total"] += new_item["total"]
                    else:
                        existing_history["items"].append(new_item)
                existing_history["total_earned"] += daily_record["total_earned"]
                existing_history["paid_amount"] += daily_record["paid_amount"]
                existing_history["net_balance"] += daily_record["net_balance"]
            else:
                data_store.history_payments.append(daily_record)
            data_store.daily_ledger.remove(daily_record)
        data_store.save_data()

    def on_date_enter(self, e):
        selected_date = self.date_input.value
        records_to_move = [r for r in data_store.history_payments if r["date"] == selected_date]
        if records_to_move:
            for r in records_to_move:
                data_store.history_payments.remove(r)
                data_store.daily_ledger.append(r)
            data_store.save_data()
        self.load_visual_ledger()
        try: self.update()
        except: pass

    def set_to_today(self, e):
        self.date_input.value = str(datetime.date.today())
        self.on_date_enter(e)

    def clear_zero(self, e):
        if e.control.value in ["0", "0.0"]:
            e.control.value = ""
            try: e.control.update()
            except: pass

    def restore_zero(self, e, calc_func):
        if str(e.control.value).strip() == "":
            e.control.value = "0"
            try: e.control.update()
            except: pass
            if calc_func: calc_func(e)

    def refresh_dropdowns_event(self, e):
        self.refresh_dropdowns(e)

    def refresh_dropdowns(self, e):
        self.product_prices = {p["name"]: (p.get("price_chota", 0.0), p.get("price_barha", 0.0)) for p in data_store.products}
        self.product_names = [p["name"] for p in data_store.products]

        payees = [l["name"] for l in data_store.labourers]
        self.labour_dd.options = [ft.dropdown.Option(p) for p in payees]
        
        options_list = [ft.dropdown.Option(n) for n in self.product_names]
        
        for row_container in self.items_column.controls:
            if row_container.content and len(row_container.content.controls) > 4:
                prod_dd = row_container.content.controls[4] 
                if isinstance(prod_dd, ft.Dropdown): 
                    prod_dd.options = options_list
                    try: prod_dd.update()
                    except: pass
                    
        if e:
            try: self.update()
            except: pass

    def get_product_prices(self, prod_name):
        if not hasattr(self, 'product_prices'): return 0.0, 0.0
        return self.product_prices.get(prod_name, (0.0, 0.0))

    def reset_form(self):
        self.labour_dd.value = None
        self.paid_input.value = "0"
        self.items_column.controls.clear()
        self.add_item_row()
        self.update_grand_total(update_paid=True)

    def add_new_row_event(self, e):
        self.add_item_row()
        try: self.items_column.update()
        except: pass

    def remove_item_row(self, row_control):
        if len(self.items_column.controls) > 1: 
            self.items_column.controls.remove(row_control)
            self.update_grand_total(update_paid=True)
            try: self.items_column.update()
            except: pass

    def add_item_row(self, initial_prod=None, initial_c="", initial_b=""):
        instant_options = [ft.dropdown.Option(n) for n in getattr(self, 'product_names', [])]

        prod_dd = ft.Dropdown(
            label="آئٹم", width=250, options=instant_options, dense=True, value=initial_prod, 
            text_size=21, text_style=ft.TextStyle(size=21, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT), 
            label_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT)
        )

        chota_input = ft.TextField(label="چھوٹا ڈرم", width=120, value=initial_c, keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT))
        barha_input = ft.TextField(label="بڑا ڈرم", width=120, value=initial_b, keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT))
        row_total_text = ft.Text("رقم: 0.00", weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLUE_900, font_family=URDU_FONT)
        
        row_container = ft.Container()
        del_btn = ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.RED_500, on_click=lambda e: self.remove_item_row(row_container))

        def calc_row_total(e):
            price_chota, price_barha = self.get_product_prices(prod_dd.value)
            try:
                c_qty = float(chota_input.value) if (chota_input.value and str(chota_input.value).strip() != "") else 0.0
                b_qty = float(barha_input.value) if (barha_input.value and str(barha_input.value).strip() != "") else 0.0
                total = (c_qty * price_chota) + (b_qty * price_barha)
                row_total_text.value = f"رقم: {total:.2f}"
            except ValueError:
                row_total_text.value = "رقم: Error"
            
            if e is not None:
                try: row_total_text.update()
                except: pass
                self.update_grand_total(update_paid=True)

        prod_dd.on_change = calc_row_total
        chota_input.on_change = calc_row_total
        barha_input.on_change = calc_row_total
        
        chota_input.on_blur = calc_row_total
        chota_input.on_submit = self.make_ledger 
        barha_input.on_blur = calc_row_total
        barha_input.on_submit = self.make_ledger 

        row_container.content = ft.Row([del_btn, row_total_text, barha_input, chota_input, prod_dd], vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END)
        row_container.get_data = lambda: {"prod": prod_dd.value, "c_qty": chota_input.value if chota_input.value else "0", "b_qty": barha_input.value if barha_input.value else "0", "total": float(str(row_total_text.value).replace("رقم: ", "").replace("Error", "0").replace(",", ""))}

        self.items_column.controls.append(row_container)
        calc_row_total(None) 

    def update_grand_total(self, update_paid=True):
        total = sum([row.get_data()["total"] for row in self.items_column.controls])
        self.grand_total_text.value = f"مکمل حساب: {total:.2f}"
        
        try: self.grand_total_text.update()
        except: pass

        if update_paid:
            if total > 0: self.paid_input.value = clean_qty(total)
            else: self.paid_input.value = "0"
            try: self.paid_input.update()
            except: pass
            
        return total

    def delete_ledger_item(self, record):
        if record in data_store.daily_ledger:
            data_store.daily_ledger.remove(record)
            data_store.save_data()
            self.load_visual_ledger()
            try: self.update()
            except: pass

    def edit_ledger_item(self, record):
        self.labour_dd.value = record["payee"]
        self.date_input.value = record["date"] 
        self.items_column.controls.clear()
        for item in record["items"]:
            c_val = item["c_qty"] if item["c_qty"] != "0" else ""
            b_val = item["b_qty"] if item["b_qty"] != "0" else ""
            self.add_item_row(initial_prod=item["prod"], initial_c=c_val, initial_b=b_val)
        self.update_grand_total(update_paid=False)
        self.paid_input.value = clean_qty(record["paid_amount"])
        self.delete_ledger_item(record)

    def create_del_handler(self, record):
        return lambda e: self.confirm_delete("کیا آپ واقعی اس اندراج کو ڈیلیٹ کرنا چاہتے ہیں؟", lambda: self.delete_ledger_item(record))

    # --- NEW: Action to quickly settle differences ---
    def settle_ledger_payment(self, record):
        record['paid_amount'] = record['total_earned']
        record['net_balance'] = 0.0
        data_store.save_data()
        self.load_visual_ledger()
        try: self.update()
        except: pass

    def load_visual_ledger(self):
        self.ledger_list.controls.clear()
        selected_date = self.date_input.value
        current_day_records = []
        for record in reversed(data_store.daily_ledger):
            if record["date"] == selected_date: 
                current_day_records.append(record)
                self.add_ledger_card_to_ui(record)
                
        if current_day_records:
            product_totals, day_total_qty, day_total_amount, day_total_balance = self.get_day_summary(current_day_records)
            summary_blocks = []
            for prod_name, qty in product_totals.items():
                summary_blocks.append(ft.Text(f"{prod_name}: {format_num(qty)}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800, font_family=URDU_FONT))
            
            if abs(day_total_balance) > 0.1:
                summary_blocks.extend([
                    ft.Text("|", size=18, color=ft.Colors.GREY_400),
                    ft.Text(f"بقایا جات: {day_total_balance:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600, font_family=URDU_FONT),
                ])

            summary_blocks.extend([
                ft.Text("|", size=18, color=ft.Colors.GREY_400),
                ft.Text(f"مقدار: {format_num(day_total_qty)}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800, font_family=URDU_FONT),
                ft.Text(f"رقم: {day_total_amount:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800, font_family=URDU_FONT),
            ])
            self.header_summary.content = ft.Container(content=ft.Row(summary_blocks, spacing=15, wrap=True, alignment=ft.MainAxisAlignment.CENTER), padding=ft.padding.symmetric(horizontal=20, vertical=5), bgcolor=ft.Colors.BLUE_50, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=20)
            self.header_summary.visible = True
        else:
            self.header_summary.visible = False

    def add_ledger_card_to_ui(self, record):
        product_blocks = []
        for item in record["items"]:
            product_blocks.append(ft.Text(f"{item['prod']} (چھوٹا: {format_num(item['c_qty'])} - بڑا: {format_num(item['b_qty'])})", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT))
            
        products_row = ft.Row(product_blocks, spacing=40, wrap=True, alignment=ft.MainAxisAlignment.END, expand=True)

        print_btn = receipt_printer.get_print_button(record)
        del_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, tooltip="Delete", on_click=self.create_del_handler(record))
        edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE, tooltip="Edit", on_click=lambda e, r=record: self.edit_ledger_item(r))

        row_controls = [
            ft.Text(f"{record['date']}", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.GREY_700, font_family=URDU_FONT),
            print_btn, del_btn, edit_btn
        ]

        # --- NEW: Show button ONLY if there's a balance left ---
        if abs(record.get('net_balance', 0.0)) > 0.1:
            pay_btn = ft.ElevatedButton(
                "برابر کریں", icon=ft.Icons.DONE_ALL, 
                color=ft.Colors.WHITE, bgcolor=ft.Colors.ORANGE_600, 
                on_click=lambda e, r=record: self.settle_ledger_payment(r),
                style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=14, weight=ft.FontWeight.BOLD))
            )
            row_controls.append(pay_btn)

        row_controls.extend([
            ft.Text(f"بقیہ: {record['net_balance']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLACK, font_family=URDU_FONT),
            ft.Text(f"ادا شدہ: {record['paid_amount']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.RED_700, font_family=URDU_FONT),
            ft.Text(f"کل: {record['total_earned']:.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.GREEN_700, font_family=URDU_FONT),
            products_row, 
            ft.Text(f"مزدور: {record['payee']}", weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLUE_900, width=150, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT),
        ])

        ledger_card = ft.Container(
            content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=5, bgcolor=ft.Colors.WHITE
        )
        self.ledger_list.controls.append(ledger_card) 

    def make_ledger(self, e):
        if not self.labour_dd.value: return 
        total_earned = self.update_grand_total(update_paid=False)
        try: paid_amount = float(self.paid_input.value) if self.paid_input.value else 0.0
        except: paid_amount = 0.0

        items_data_to_save = [row.get_data() for row in self.items_column.controls if row.get_data()["prod"]]
        if not items_data_to_save: return 

        selected_date = self.date_input.value
        existing_record = next((r for r in data_store.daily_ledger if r["payee"] == self.labour_dd.value and r["date"] == selected_date), None)

        if existing_record:
            for new_item in items_data_to_save:
                matching = next((i for i in existing_record["items"] if i["prod"] == new_item["prod"]), None)
                if matching:
                    matching["c_qty"] = clean_qty(float(matching["c_qty"]) + float(new_item["c_qty"]))
                    matching["b_qty"] = clean_qty(float(matching["b_qty"]) + float(new_item["b_qty"]))
                    matching["total"] += new_item["total"]
                else: existing_record["items"].append(new_item)
            
            existing_record["total_earned"] += total_earned
            existing_record["paid_amount"] += paid_amount
            existing_record["net_balance"] = existing_record["total_earned"] - existing_record["paid_amount"]
        else:
            record = {"id": str(uuid.uuid4()), "date": selected_date, "payee": self.labour_dd.value, "items": items_data_to_save, "total_earned": total_earned, "paid_amount": paid_amount, "net_balance": total_earned - paid_amount}
            data_store.daily_ledger.append(record)

        data_store.save_data() 
        self.load_visual_ledger()
        self.reset_form()
        try: self.update()
        except: pass

    def save_day_data(self, e):
        selected_date = self.date_input.value
        records_to_save = [r for r in data_store.daily_ledger if r["date"] == selected_date]
        for daily_record in records_to_save:
            existing_history = next((r for r in data_store.history_payments if r["payee"] == daily_record["payee"] and r["date"] == daily_record["date"]), None)
            if existing_history:
                for new_item in daily_record["items"]:
                    matching = next((i for i in existing_history["items"] if i["prod"] == new_item["prod"]), None)
                    if matching:
                        matching["c_qty"] = clean_qty(float(matching["c_qty"]) + float(new_item["c_qty"]))
                        matching["b_qty"] = clean_qty(float(matching["b_qty"]) + float(new_item["b_qty"]))
                        matching["total"] += new_item["total"]
                    else: existing_history["items"].append(new_item)
                existing_history["total_earned"] += daily_record["total_earned"]
                existing_history["paid_amount"] += daily_record["paid_amount"]
                existing_history["net_balance"] += daily_record["net_balance"]
            else: data_store.history_payments.append(daily_record)
            data_store.daily_ledger.remove(daily_record)

        data_store.save_data() 
        self.ledger_list.controls.clear()
        self.header_summary.visible = False
        self.ledger_list.controls.append(ft.Text(f"تاریخ {selected_date} کا لیجر محفوظ ہو گیا!", color=ft.Colors.GREEN_600, weight=ft.FontWeight.BOLD, size=20, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT))
        try: self.update()
        except: pass