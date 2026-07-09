import flet as ft
import data_store

URDU_FONT = "Jameel Noori Nastaleeq"

class ProductTab(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        
        self.last_version = 0

        self.p_name = ft.TextField(label="پروڈکٹ کا نام (Name)", width=250, text_style=ft.TextStyle(font_family=URDU_FONT, size=22, weight=ft.FontWeight.BOLD), label_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD), on_submit=self.add_product)
        self.p_c_price = ft.TextField(label="چھوٹا ڈرم ریٹ", width=160, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(font_family=URDU_FONT, size=22, weight=ft.FontWeight.BOLD), label_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD), on_submit=self.add_product)
        self.p_b_price = ft.TextField(label="بڑا ڈرم ریٹ", width=160, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(font_family=URDU_FONT, size=22, weight=ft.FontWeight.BOLD), label_style=ft.TextStyle(font_family=URDU_FONT, size=18, weight=ft.FontWeight.BOLD), on_submit=self.add_product)

        add_btn = ft.ElevatedButton("محفوظ کریں", icon=ft.Icons.SAVE, on_click=self.add_product, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, style=ft.ButtonStyle(padding=15, text_style=ft.TextStyle(font_family=URDU_FONT, size=20, weight=ft.FontWeight.BOLD)))

        self.product_list = ft.Column(spacing=15)

        self.content = ft.Column([
            ft.Text("پروڈکٹ کا انتظام (Manage Products)", size=30, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT, font_family=URDU_FONT, color=ft.Colors.BLUE_900),
            ft.Row([add_btn, ft.Row([self.p_b_price, self.p_c_price, self.p_name], alignment=ft.MainAxisAlignment.END)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(thickness=2),
            self.product_list
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

    def add_product(self, e):
        if not self.p_name.value: return
        c_price = float(self.p_c_price.value) if self.p_c_price.value else 0.0
        b_price = float(self.p_b_price.value) if self.p_b_price.value else 0.0

        existing = next((p for p in data_store.products if p['name'] == self.p_name.value), None)
        if existing:
            existing['price_chota'] = c_price
            existing['price_barha'] = b_price
        else:
            data_store.products.append({"name": self.p_name.value, "price_chota": c_price, "price_barha": b_price})

        data_store.save_data()
        self.p_name.value = ""
        self.p_c_price.value = ""
        self.p_b_price.value = ""
        self.load_visual_list()
        self.main_page.update()

    def delete_product(self, prod):
        if prod in data_store.products:
            data_store.products.remove(prod)
            data_store.save_data()
            self.load_visual_list()
            self.main_page.update()

    def edit_product(self, prod):
        self.p_name.value = prod['name']
        self.p_c_price.value = str(prod['price_chota'])
        self.p_b_price.value = str(prod['price_barha'])
        self.main_page.update()

    def create_del_handler(self, prod):
        return lambda e: self.confirm_delete(f"کیا آپ واقعی {prod['name']} کو ڈیلیٹ کرنا چاہتے ہیں؟", lambda: self.delete_product(prod))

    def load_visual_list(self):
        if getattr(self, 'last_version', 0) == data_store.data_version: return
        self.last_version = data_store.data_version
        
        self.product_list.controls.clear()
        for p in data_store.products:
            del_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, tooltip="Delete", on_click=self.create_del_handler(p))
            edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE, tooltip="Edit", on_click=lambda e, prod=p: self.edit_product(prod))

            row = ft.Row([
                del_btn, edit_btn, ft.Container(expand=True),
                ft.Text(f"بڑا ڈرم: {p['price_barha']}", size=22, font_family=URDU_FONT, weight=ft.FontWeight.BOLD),
                ft.Text("|", size=22, color=ft.Colors.GREY_400),
                ft.Text(f"چھوٹا ڈرم: {p['price_chota']}", size=22, font_family=URDU_FONT, weight=ft.FontWeight.BOLD),
                ft.Text(f"پروڈکٹ: {p['name']}", size=26, color=ft.Colors.BLUE_900, font_family=URDU_FONT, weight=ft.FontWeight.BOLD)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

            self.product_list.controls.append(ft.Container(content=row, padding=20, border=ft.border.all(1, ft.Colors.BLUE_GREY_200), border_radius=8, bgcolor=ft.Colors.WHITE))
        if self.main_page: self.main_page.update()