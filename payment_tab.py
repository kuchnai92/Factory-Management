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
        self.payee_names = []
        
        self.auto_save_old_dates()
        
        # --- HEADER CONTROLS ---
        self.date_input = ft.TextField(
            label="تاریخ (Date)", width=160, value=str(datetime.date.today()), dense=True,
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            on_submit=self.on_date_enter, prefix_icon=ft.Icons.CALENDAR_TODAY
        )
        self.today_btn = ft.IconButton(icon=ft.Icons.TODAY, tooltip="آج (Today)", icon_color=ft.Colors.BLUE_700, icon_size=30, on_click=self.set_to_today)

        self.save_day_btn = ft.ElevatedButton("دن محفوظ کریں (Save Day)", icon=ft.Icons.SAVE, on_click=self.save_day_data, bgcolor=ft.Colors.GREEN_800, color=ft.Colors.WHITE, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD)))
        
        self.add_entry_btn = ft.ElevatedButton("نیا اندراج (New Entry)", icon=ft.Icons.ADD_CIRCLE, on_click=lambda e: self.open_entry_dialog(None), bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(font_family=URDU_FONT, size=20, weight=ft.FontWeight.BOLD)))

        self.header_summary = ft.Container(expand=True)

        self.header_row = ft.Row([
            ft.Row([self.save_day_btn, self.today_btn, self.date_input], alignment=ft.MainAxisAlignment.START),
            ft.Text("روزانہ کی ادائیگی", size=30, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT, color=ft.Colors.BLUE_900)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.ledger_list = ft.ListView(spacing=15, expand=True, padding=ft.padding.only(top=10, bottom=30)) 

        self.content = ft.Column([
            self.header_row, 
            ft.Divider(color=ft.Colors.TRANSPARENT, height=10),
            ft.Row([self.add_entry_btn, self.header_summary], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=ft.Colors.BLUE_GREY_100, height=20, thickness=2),
            ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.BLUE_GREY_500, size=30),
                ft.Text("عارضی لیجر (Temporary Ledger):", size=24, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_GREY_800)
            ]),
            self.ledger_list
        ], expand=True)

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

        # --- SPEED FIX: Isolated Snackbar avoids whole-page redraws ---
        self.app_snackbar = ft.SnackBar(ft.Text(""), duration=1500)
        self.main_page.overlay.append(self.app_snackbar)

        self.editing_record = None
        self.build_entry_dialog()

        self.refresh_data_lists()
        self.load_visual_ledger()

    # --- DIALOG BUILD & LOGIC (Optimized for Speed) ---
    def build_entry_dialog(self):
        self.dlg_labour_dd = ft.Dropdown(
            label="مزدور کا نام (Name)", width=300, 
            text_size=21, dense=True, 
            text_style=ft.TextStyle(size=21, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT), 
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT)
        )
        
        self.dlg_paid_input = ft.TextField(
            label="ادا کردہ رقم (Paid)", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER, 
            dense=True, text_style=ft.TextStyle(size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700, font_family=URDU_FONT), 
            label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT),
            on_submit=self.dlg_save_entry
        )
        
        self.dlg_items_column = ft.Column(spacing=10)
        self.dlg_grand_total_text = ft.Text("مکمل حساب: 0", weight=ft.FontWeight.BOLD, size=28, color=ft.Colors.GREEN_800, font_family=URDU_FONT)
        self.dlg_quick_pay_btn = ft.IconButton(icon=ft.Icons.ACCOUNT_BALANCE_WALLET, tooltip="پوری رقم ادا کریں (Pay Full)", icon_color=ft.Colors.GREEN_600, on_click=self.dlg_quick_fill_paid)
        self.dlg_add_item_btn = ft.ElevatedButton("مزید آئٹم +", icon=ft.Icons.ADD, on_click=lambda e: self.dlg_add_item_row(), bgcolor=ft.Colors.BLUE_100, color=ft.Colors.BLUE_900, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD)))

        dlg_content_col = ft.Column([
            ft.Row([ft.Row([self.dlg_quick_pay_btn, self.dlg_paid_input]), ft.Row([self.dlg_add_item_btn, self.dlg_labour_dd])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=20, color=ft.Colors.BLUE_GREY_100),
            self.dlg_items_column,
            ft.Divider(height=20, color=ft.Colors.BLUE_GREY_100),
            ft.Row([self.dlg_grand_total_text], alignment=ft.MainAxisAlignment.END)
        ], tight=True, spacing=10)

        self.entry_dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.EDIT_DOCUMENT, color=ft.Colors.BLUE_700), ft.Text("اندراج کریں (Manage Entry)", weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_900)], alignment=ft.MainAxisAlignment.END),
            content=ft.Container(content=dlg_content_col, width=800, padding=10),
            actions=[
                ft.TextButton("منسوخ کریں (Cancel)", on_click=self.close_entry_dialog),
                ft.ElevatedButton("محفوظ کریں (Save)", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=self.dlg_save_entry, style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD)))
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        self.main_page.overlay.append(self.entry_dlg)

    def clear_zero(self, e):
        if e.control.value in ["0", "0.0"]:
            e.control.value = ""
            e.control.update()

    def restore_zero(self, e, calc_func):
        if str(e.control.value).strip() == "":
            e.control.value = "0"
            e.control.update()
        if calc_func: calc_func(e)

    def dlg_update_grand_total(self, update_paid=True):
        total = sum([getattr(row, 'latest_total', 0.0) for row in self.dlg_items_column.controls])
        self.dlg_grand_total_text.value = f"مکمل حساب: {total:,.0f}"
        try: self.dlg_grand_total_text.update()
        except: pass

        if update_paid:
            self.dlg_paid_input.value = clean_qty(total) if total > 0 else "0"
            try: self.dlg_paid_input.update()
            except: pass
        return total

    def dlg_quick_fill_paid(self, e):
        total = sum([getattr(row, 'latest_total', 0.0) for row in self.dlg_items_column.controls])
        self.dlg_paid_input.value = clean_qty(total)
        try: self.dlg_paid_input.update()
        except: pass

    def dlg_remove_item_row(self, row_control):
        if len(self.dlg_items_column.controls) > 1: 
            self.dlg_items_column.controls.remove(row_control)
            self.dlg_update_grand_total(update_paid=True)
            try: self.dlg_items_column.update()
            except: pass

    def dlg_add_item_row(self, initial_prod=None, initial_c="", initial_b=""):
        instant_options = [ft.dropdown.Option(n) for n in self.product_names]

        prod_dd = ft.Dropdown(
            label="آئٹم (Item)", width=220, options=instant_options, dense=True, value=initial_prod, 
            text_size=21, text_style=ft.TextStyle(size=21, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT), 
            label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT)
        )

        chota_input = ft.TextField(label="چھوٹا", width=90, value=initial_c, keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT))
        barha_input = ft.TextField(label="بڑا", width=90, value=initial_b, keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, font_family=URDU_FONT))
        row_total_text = ft.Text("رقم: 0", weight=ft.FontWeight.BOLD, size=22, color=ft.Colors.BLUE_900, font_family=URDU_FONT, width=150, text_align=ft.TextAlign.RIGHT)
        
        row_container = ft.Container()
        del_btn = ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.RED_500, on_click=lambda ev: self.dlg_remove_item_row(row_container))

        def calc_row_total(ev):
            price_chota, price_barha = self.get_product_prices(prod_dd.value)
            try:
                c_qty = float(chota_input.value) if (chota_input.value and str(chota_input.value).strip() != "") else 0.0
                b_qty = float(barha_input.value) if (barha_input.value and str(barha_input.value).strip() != "") else 0.0
                total = (c_qty * price_chota) + (b_qty * price_barha)
                row_container.latest_total = total
                row_total_text.value = f"رقم: {total:,.0f}"
            except ValueError:
                row_total_text.value = "رقم: Error"
                row_container.latest_total = 0.0
            
            try: row_total_text.update()
            except: pass
            self.dlg_update_grand_total(update_paid=True)

        prod_dd.on_change = calc_row_total
        chota_input.on_change = calc_row_total
        barha_input.on_change = calc_row_total
        
        chota_input.on_focus = self.clear_zero
        barha_input.on_focus = self.clear_zero
        chota_input.on_blur = lambda ev: self.restore_zero(ev, calc_row_total)
        barha_input.on_blur = lambda ev: self.restore_zero(ev, calc_row_total)
        
        chota_input.on_submit = self.dlg_save_entry
        barha_input.on_submit = self.dlg_save_entry

        row_container.content = ft.Row([del_btn, row_total_text, barha_input, chota_input, prod_dd], vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END)
        row_container.prod_dd = prod_dd 
        row_container.force_calc = lambda: calc_row_total(None)
        row_container.get_data = lambda: {"prod": prod_dd.value, "c_qty": chota_input.value if chota_input.value else "0", "b_qty": barha_input.value if barha_input.value else "0", "total": getattr(row_container, 'latest_total', 0.0)}

        self.dlg_items_column.controls.append(row_container)
        calc_row_total(None)
        
        if self.entry_dlg.open:
            try: self.dlg_items_column.update()
            except: pass

    # --- SPEED FIX: Targeted dialog close prevents full page redraw ---
    def close_entry_dialog(self, e=None):
        self.entry_dlg.open = False
        try: self.entry_dlg.update()
        except: pass

    def dlg_save_entry(self, e=None):
        if not self.dlg_labour_dd.value: return 
        
        total_earned = self.dlg_update_grand_total(update_paid=False)
        try: paid_amount = float(self.dlg_paid_input.value) if self.dlg_paid_input.value else 0.0
        except: paid_amount = 0.0

        items_data_to_save = [row.get_data() for row in self.dlg_items_column.controls if row.get_data()["prod"]]
        if not items_data_to_save: return 

        if self.editing_record and self.editing_record in data_store.daily_ledger:
            data_store.daily_ledger.remove(self.editing_record)

        selected_date = self.date_input.value
        existing_record = next((r for r in data_store.daily_ledger if r["payee"] == self.dlg_labour_dd.value and r["date"] == selected_date), None)

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
            record = {"id": str(uuid.uuid4()), "date": selected_date, "payee": self.dlg_labour_dd.value, "items": items_data_to_save, "total_earned": total_earned, "paid_amount": paid_amount, "net_balance": total_earned - paid_amount}
            data_store.daily_ledger.append(record)

        data_store.save_data() 
        self.load_visual_ledger()
        
        try: 
            self.ledger_list.update()
            self.header_summary.update()
        except: pass

        if self.editing_record:
            self.close_entry_dialog() 
        else:
            self.dlg_labour_dd.value = None
            self.dlg_paid_input.value = "0"
            self.dlg_items_column.controls.clear()
            self.dlg_add_item_row()
            self.dlg_update_grand_total(update_paid=True)
            
            try: 
                self.dlg_labour_dd.update()
                self.dlg_paid_input.update()
                self.dlg_items_column.update()
            except: pass
            
            # SPEED FIX: Targeted snackbar update instead of whole page
            self.app_snackbar.content = ft.Text("کامیابی سے محفوظ ہو گیا! (Saved!)", size=18, font_family=URDU_FONT)
            self.app_snackbar.bgcolor = ft.Colors.GREEN_700
            self.app_snackbar.open = True
            try: self.app_snackbar.update()
            except: pass

    # --- SPEED FIX: Targeted dialog open prevents full page redraw ---
    def open_entry_dialog(self, record_to_edit=None):
        self.refresh_data_lists()
        self.editing_record = record_to_edit
        self.dlg_labour_dd.options = [ft.dropdown.Option(p) for p in self.payee_names]
        self.dlg_items_column.controls.clear()
        
        if record_to_edit:
            self.dlg_labour_dd.value = record_to_edit["payee"]
            for item in record_to_edit["items"]:
                c_val = item["c_qty"] if item["c_qty"] != "0" else ""
                b_val = item["b_qty"] if item["b_qty"] != "0" else ""
                self.dlg_add_item_row(initial_prod=item["prod"], initial_c=c_val, initial_b=b_val)
            self.dlg_update_grand_total(update_paid=False)
            self.dlg_paid_input.value = clean_qty(record_to_edit["paid_amount"])
        else:
            self.dlg_labour_dd.value = None
            self.dlg_paid_input.value = "0"
            self.dlg_add_item_row()
            self.dlg_update_grand_total(update_paid=True)

        self.entry_dlg.open = True
        try: self.entry_dlg.update()
        except: pass

    # --- MAIN ENGINE METHODS ---
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
        try: 
            self.ledger_list.update()
            self.header_summary.update()
        except: pass

    def set_to_today(self, e):
        self.date_input.value = str(datetime.date.today())
        try: self.date_input.update()
        except: pass
        self.on_date_enter(e)

    def refresh_dropdowns(self, e):
        self.refresh_data_lists()
        options_list = [ft.dropdown.Option(n) for n in self.product_names]
        if hasattr(self, 'dlg_labour_dd'):
            self.dlg_labour_dd.options = [ft.dropdown.Option(p) for p in self.payee_names]
            for row in self.dlg_items_column.controls:
                if hasattr(row, 'prod_dd'):
                    row.prod_dd.options = options_list

    def refresh_data_lists(self):
        self.product_prices = {p["name"]: (p.get("price_chota", 0.0), p.get("price_barha", 0.0)) for p in data_store.products}
        self.product_names = [p["name"] for p in data_store.products]
        self.payee_names = [l["name"] for l in data_store.labourers]

    def get_product_prices(self, prod_name):
        if not hasattr(self, 'product_prices'): return 0.0, 0.0
        return self.product_prices.get(prod_name, (0.0, 0.0))

    # --- SPEED FIX: Targeted confirm dialog updates ---
    def confirm_delete(self, title_text, on_confirm_action):
        self.confirm_dlg.content.value = title_text
        def close_dlg(e):
            self.confirm_dlg.open = False
            try: self.confirm_dlg.update()
            except: pass
        def confirm_action(e):
            self.confirm_dlg.open = False
            try: self.confirm_dlg.update()
            except: pass
            on_confirm_action()

        self.confirm_dlg.actions[0].on_click = close_dlg
        self.confirm_dlg.actions[1].on_click = confirm_action
        self.confirm_dlg.open = True
        try: self.confirm_dlg.update()
        except: pass

    def create_del_handler(self, record):
        return lambda e: self.confirm_delete("کیا آپ واقعی اس اندراج کو ڈیلیٹ کرنا چاہتے ہیں؟", lambda: self.delete_ledger_item(record))

    def delete_ledger_item(self, record):
        if record in data_store.daily_ledger:
            data_store.daily_ledger.remove(record)
            data_store.save_data()
            self.load_visual_ledger()
            try: 
                self.ledger_list.update()
                self.header_summary.update()
            except: pass

    def settle_ledger_payment(self, record):
        record['paid_amount'] = record['total_earned']
        record['net_balance'] = 0.0
        data_store.save_data()
        self.load_visual_ledger()
        try: 
            self.ledger_list.update()
            self.header_summary.update()
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
            self.header_summary.content = ft.Container(
                content=ft.Row(summary_blocks, spacing=15, wrap=True, alignment=ft.MainAxisAlignment.CENTER), 
                padding=ft.padding.symmetric(horizontal=20, vertical=8), 
                bgcolor=ft.Colors.BLUE_50, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=10
            )
            self.header_summary.visible = True
        else:
            self.header_summary.visible = False

    def add_ledger_card_to_ui(self, record):
        product_blocks = []
        for item in record["items"]:
            product_blocks.append(ft.Text(f"{item['prod']} (چھوٹا: {format_num(item['c_qty'])} - بڑا: {format_num(item['b_qty'])})", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, font_family=URDU_FONT))
            
        products_row = ft.Row(product_blocks, spacing=40, wrap=True, alignment=ft.MainAxisAlignment.END, expand=True)

        print_btn = receipt_printer.get_print_button(record)
        del_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_500, tooltip="Delete", on_click=self.create_del_handler(record))
        edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE_500, tooltip="Edit", on_click=lambda e, r=record: self.open_entry_dialog(r))

        row_controls = [
            ft.Text(f"{record['date']}", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.GREY_500, font_family=URDU_FONT),
            print_btn, del_btn, edit_btn
        ]

        if abs(record.get('net_balance', 0.0)) > 0.1:
            pay_btn = ft.ElevatedButton(
                "برابر کریں", icon=ft.Icons.DONE_ALL, color=ft.Colors.WHITE, bgcolor=ft.Colors.ORANGE_600, 
                on_click=lambda e, r=record: self.settle_ledger_payment(r),
                style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD))
            )
            row_controls.append(pay_btn)

        row_controls.extend([
            ft.Container(content=ft.Text(f"بقیہ: {record['net_balance']:,.0f}", weight=ft.FontWeight.BOLD, size=22, color=ft.Colors.BLACK, font_family=URDU_FONT), width=120),
            ft.Container(content=ft.Text(f"ادا شدہ: {record['paid_amount']:,.0f}", weight=ft.FontWeight.BOLD, size=22, color=ft.Colors.RED_700, font_family=URDU_FONT), width=150),
            ft.Container(content=ft.Text(f"کل: {record['total_earned']:,.0f}", weight=ft.FontWeight.BOLD, size=22, color=ft.Colors.GREEN_700, font_family=URDU_FONT), width=120),
            products_row, 
            ft.Text(f"{record['payee']}", weight=ft.FontWeight.BOLD, size=26, color=ft.Colors.BLUE_900, width=180, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT),
        ])

        ledger_card = ft.Container(
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(20), border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=12
        )
        self.ledger_list.controls.append(ledger_card) 

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
        
        success_msg = ft.Container(
            bgcolor=ft.Colors.GREEN_50, border=ft.border.all(1, ft.Colors.GREEN_300), border_radius=8, padding=20,
            content=ft.Row([
                ft.Text(f"تاریخ {selected_date} کا لیجر کامیابی سے محفوظ ہو گیا!", color=ft.Colors.GREEN_800, weight=ft.FontWeight.BOLD, size=22, font_family=URDU_FONT),
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=30)
            ], alignment=ft.MainAxisAlignment.END)
        )
        self.ledger_list.controls.append(success_msg)
        
        try: 
            self.ledger_list.update()
            self.header_summary.update()
        except: pass