import flet as ft
import data_store
import uuid
import datetime

URDU_FONT = "Jameel Noori Nastaleeq"

class LabourTab(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        self.active_dialog = None
        self.current_labour = None
        
        # --- NEW: Memory tracker for the screen ---
        self.last_version = 0 

        self.error_text = ft.Text("", color=ft.Colors.RED_700, size=16, weight=ft.FontWeight.BOLD)

        self.l_id = ft.TextField(label="آئی ڈی (ID)", width=150, value=self.get_next_id(), read_only=True, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_900), label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT))
        self.l_name = ft.TextField(label="مزدور کا نام (Name)", width=250, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), label_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, font_family=URDU_FONT), on_submit=self.add_labour)
        
        add_btn = ft.ElevatedButton(
            "مزدور شامل کریں / محفوظ کریں", 
            on_click=self.add_labour, 
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, 
            style=ft.ButtonStyle(text_style=ft.TextStyle(font_family=URDU_FONT, size=16, weight=ft.FontWeight.BOLD))
        )

        self.labour_list = ft.Column(spacing=10)

        self.content = ft.Column([
            ft.Row([
                self.error_text,
                ft.Text("مزدوروں کا انتظام (Manage Labour)", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Row([
                add_btn,
                ft.Row([self.l_name, self.l_id], alignment=ft.MainAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(thickness=2),
            self.labour_list
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
        
        self.load_visual_list()

    def refresh_dropdowns(self):
        pass

    def get_next_id(self):
        return str(len(data_store.labourers) + 1)

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

    def add_labour(self, e):
        if not self.l_name.value: 
            return
            
        existing = next((l for l in data_store.labourers if l.get('id') == self.l_id.value), None)
        if existing:
            existing['name'] = self.l_name.value
        else:
            data_store.labourers.append({"id": self.l_id.value, "name": self.l_name.value, "transactions": []})
            
        data_store.save_data()
        self.l_name.value = ""
        self.l_id.value = self.get_next_id()
        self.load_visual_list()
        self.main_page.update()

    def edit_labour(self, lab):
        self.l_id.value = lab.get('id', '')
        self.l_name.value = lab['name']
        self.main_page.update()

    def delete_labour(self, lab):
        data_store.labourers.remove(lab)
        for i, l in enumerate(data_store.labourers):
            l['id'] = str(i + 1)
        data_store.save_data()
        self.l_id.value = self.get_next_id()
        self.load_visual_list()
        self.main_page.update()

    def create_del_labour_handler(self, lab):
        return lambda e: self.confirm_delete(f"کیا آپ واقعی {lab['name']} کا سارا ریکارڈ ڈیلیٹ کرنا چاہتے ہیں؟", lambda: self.delete_labour(lab))

    def create_del_trans_handler(self, t_id):
        return lambda e: self.confirm_delete("کیا آپ واقعی یہ لین دین ڈیلیٹ کرنا چاہتے ہیں؟", lambda: self.del_transaction(t_id))

    def load_visual_list(self):
        # --- 🔥 NEW: Smart Caching! If data didn't change, instantly skip rebuilding! ---
        if getattr(self, 'last_version', 0) == data_store.data_version:
            return 
        self.last_version = data_store.data_version
        
        self.labour_list.controls.clear()
        
        fast_stats = {l['name']: {'earned': 0, 'paid': 0, 'balance': 0} for l in data_store.labourers}
        
        for r in data_store.history_payments + data_store.daily_ledger:
            payee = r.get("payee")
            if payee in fast_stats: 
                fast_stats[payee]['earned'] += r.get("total_earned", 0)
                fast_stats[payee]['paid'] += r.get("paid_amount", 0)
                fast_stats[payee]['balance'] += r.get("net_balance", 0)

        for i, l in enumerate(data_store.labourers):
            stats = fast_stats.get(l['name'], {'earned': 0, 'paid': 0, 'balance': 0})
            prod_earned = stats['earned']
            prod_paid = stats['paid']
            prod_balance = stats['balance']
            
            transactions = l.get("transactions", [])
            total_in = sum(t['amount'] for t in transactions if t['type'] == 'IN')
            total_out = sum(t['amount'] for t in transactions if t['type'] == 'OUT')
            manual_balance = total_in - total_out
            
            khata_btn = ft.ElevatedButton(
                f"ذاتی لین دین ({manual_balance:,.0f})", 
                icon=ft.Icons.ACCOUNT_BALANCE_WALLET, 
                bgcolor=ft.Colors.PURPLE_50, color=ft.Colors.PURPLE_900,
                on_click=lambda e, lab=l: self.open_khata(lab)
            )
            
            edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE, tooltip="Edit", on_click=lambda e, lab=l: self.edit_labour(lab))
            del_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, tooltip="Delete", on_click=self.create_del_labour_handler(l))
            
            row = ft.Row([
                del_btn, 
                edit_btn, 
                ft.Container(content=khata_btn, width=220), 
                ft.Container(content=ft.Text(f"فیکٹری بقایا: {prod_balance:,.0f}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.ORANGE_800, font_family=URDU_FONT), width=200),
                ft.Container(expand=True), 
                ft.Container(content=ft.Text(f"نام: {l['name']}", weight=ft.FontWeight.BOLD, size=20, color=ft.Colors.BLUE_900, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT), width=200),
                ft.Container(content=ft.Text(f"آئی ڈی: {l.get('id', str(i+1))}", weight=ft.FontWeight.BOLD, size=18, font_family=URDU_FONT, text_align=ft.TextAlign.RIGHT), width=80),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            self.labour_list.controls.append(ft.Container(content=row, padding=10, border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=5, bgcolor=ft.Colors.WHITE))
        if self.main_page: self.main_page.update()

    def open_khata(self, labour):
        self.current_labour = labour
        self.error_text.value = "" 
        
        self.t_amount = ft.TextField(label="رقم (Amount)", width=150, keyboard_type=ft.KeyboardType.NUMBER, dense=True, text_style=ft.TextStyle(font_family=URDU_FONT, size=20, weight=ft.FontWeight.BOLD))
        self.t_reason = ft.TextField(label="تفصیل (Reason)", expand=True, dense=True, text_style=ft.TextStyle(font_family=URDU_FONT, size=18))
        
        self.btn_in = ft.ElevatedButton("رقم جمع کی (Deposit)", icon=ft.Icons.ADD_CIRCLE, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, on_click=lambda e: self.add_transaction("IN"))
        self.btn_out = ft.ElevatedButton("ایڈوانس دیا (Advance)", icon=ft.Icons.REMOVE_CIRCLE, bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, on_click=lambda e: self.add_transaction("OUT"))
        
        self.t_list = ft.ListView(height=220, spacing=10) 
        self.t_total = ft.Text("ذاتی بیلنس: 0", size=24, weight=ft.FontWeight.BOLD, font_family=URDU_FONT)
        
        content_container = ft.Container(
            content=ft.Column([
                ft.Row([self.t_reason, self.t_amount], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([self.btn_out, self.btn_in], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ft.Colors.GREY_300),
                ft.Row([self.t_total], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(color=ft.Colors.GREY_300),
                self.t_list
            ]),
            width=600, padding=10
        )
        
        try:
            if self.active_dialog and self.active_dialog in self.main_page.overlay:
                self.main_page.overlay.remove(self.active_dialog)

            self.active_dialog = ft.AlertDialog(
                title=ft.Text(f"{labour['name']} کا ذاتی لین دین", size=26, weight=ft.FontWeight.BOLD, font_family=URDU_FONT, color=ft.Colors.BLUE_900, text_align=ft.TextAlign.RIGHT),
                content=content_container,
                actions=[ft.ElevatedButton("بند کریں (Close)", icon=ft.Icons.CLOSE, color=ft.Colors.RED_900, bgcolor=ft.Colors.RED_50, on_click=self.close_khata)],
                actions_alignment=ft.MainAxisAlignment.END
            )

            self.refresh_khata_list() 
            self.main_page.overlay.append(self.active_dialog)
            self.active_dialog.open = True
            self.main_page.update()
            
        except Exception as e:
            self.error_text.value = f"Error: {str(e)}"
            self.main_page.update()

    def close_khata(self, e):
        try:
            if self.active_dialog:
                self.active_dialog.open = False
                self.main_page.update()
                
                # Because we changed manual khata, force a UI rebuild next time
                self.last_version = 0 
                self.load_visual_list()
        except: pass

    def add_transaction(self, t_type):
        if not self.t_amount.value: return
        try: amt = float(self.t_amount.value)
        except: return
        
        reason = self.t_reason.value if self.t_reason.value else "نامعلوم"
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        if 'transactions' not in self.current_labour:
            self.current_labour['transactions'] = []
            
        self.current_labour['transactions'].append({
            "id": str(uuid.uuid4()), "date": date_str, "amount": amt, "type": t_type, "reason": reason
        })
        data_store.save_data() 
        self.t_amount.value = ""
        self.t_reason.value = ""
        self.refresh_khata_list()
        self.main_page.update()

    def del_transaction(self, t_id):
        if 'transactions' in self.current_labour:
            self.current_labour['transactions'] = [t for t in self.current_labour['transactions'] if t.get('id') != t_id]
            data_store.save_data()
            self.refresh_khata_list()
            self.main_page.update()

    def refresh_khata_list(self):
        self.t_list.controls.clear()
        transactions = self.current_labour.get('transactions', [])
        
        manual_in = sum(t['amount'] for t in transactions if t['type'] == 'IN')
        manual_out = sum(t['amount'] for t in transactions if t['type'] == 'OUT')
        manual_balance = manual_in - manual_out
        
        self.t_total.value = f"ذاتی بیلنس (Personal Balance): {manual_balance:,.0f}"
        self.t_total.color = ft.Colors.GREEN_700 if manual_balance >= 0 else ft.Colors.RED_700
        
        for t in reversed(transactions):
            is_in = (t['type'] == 'IN')
            color = ft.Colors.GREEN_700 if is_in else ft.Colors.RED_700
            sign = "+" if is_in else "-"
            bg_color = ft.Colors.GREEN_50 if is_in else ft.Colors.RED_50
            icon = ft.Icons.ARROW_DOWNWARD if is_in else ft.Icons.ARROW_UPWARD
            
            del_btn = ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=20, on_click=self.create_del_trans_handler(t['id']))
            
            row = ft.Container(
                content=ft.Row([
                    del_btn, ft.Text(t['date'], size=13, color=ft.Colors.GREY_600, font_family=URDU_FONT),
                    ft.Container(expand=True), ft.Text(t['reason'], size=18, font_family=URDU_FONT, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                    ft.Row([ft.Text(f"{sign}{t['amount']:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=color, font_family=URDU_FONT), ft.Icon(icon, color=color, size=20)], spacing=5)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10, border_radius=5, bgcolor=bg_color, border=ft.border.all(1, color), margin=ft.margin.only(bottom=5)
            )
            self.t_list.controls.append(row)