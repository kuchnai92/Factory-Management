import flet as ft
from home_tab import HomeTab
from product_tab import ProductTab
from labour_tab import LabourTab
from payment_tab import PaymentTab
from history_tab import HistoryTab

def main(page: ft.Page):
    page.title = "Factory Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    URDU_FONT = "Jameel Noori Nastaleeq"

    page.theme = ft.Theme(
        font_family=URDU_FONT,
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(size=21, color=ft.Colors.BLACK, font_family=URDU_FONT),   
            body_medium=ft.TextStyle(size=18, color=ft.Colors.BLACK, font_family=URDU_FONT),  
            body_small=ft.TextStyle(size=16, color=ft.Colors.BLACK, font_family=URDU_FONT),   
            title_large=ft.TextStyle(size=26, color=ft.Colors.BLACK, font_family=URDU_FONT),  
            title_medium=ft.TextStyle(size=22, color=ft.Colors.BLACK, font_family=URDU_FONT), 
            title_small=ft.TextStyle(size=20, color=ft.Colors.BLACK, font_family=URDU_FONT),
            
            # --- THE FIX: This controls the text size inside all Dropdown Menus globally ---
            label_large=ft.TextStyle(size=19, color=ft.Colors.BLACK, font_family=URDU_FONT, weight=ft.FontWeight.BOLD),
            label_medium=ft.TextStyle(size=19, color=ft.Colors.BLACK, font_family=URDU_FONT, weight=ft.FontWeight.BOLD),
        )
    )

    home_view = HomeTab(page)
    product_view = ProductTab(page)
    labour_view = LabourTab(page)
    payment_view = PaymentTab(page)
    history_view = HistoryTab(page)

    def on_tab_change(e):
        idx = e.control.selected_index
        if idx == 0: home_view.load_data()  
        elif idx == 1: product_view.load_visual_list()
        elif idx == 2: labour_view.load_visual_list(); labour_view.refresh_dropdowns()
        elif idx == 3: payment_view.refresh_dropdowns(None)
        elif idx == 4: history_view.load_data()

    t = ft.Tabs(
        selected_index=0,
        length=5, 
        expand=True,
        on_change=on_tab_change,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label=ft.Text("Home Dashboard", size=16, weight=ft.FontWeight.BOLD)),
                        ft.Tab(label=ft.Text("Products", size=16, weight=ft.FontWeight.BOLD)),
                        ft.Tab(label=ft.Text("Labour & Khata", size=16, weight=ft.FontWeight.BOLD)),
                        ft.Tab(label=ft.Text("Daily Payments", size=16, weight=ft.FontWeight.BOLD)),
                        ft.Tab(label=ft.Text("Settings & History", size=16, weight=ft.FontWeight.BOLD)),
                    ]
                ),
                ft.TabBarView(expand=True, controls=[home_view, product_view, labour_view, payment_view, history_view])
            ]
        )
    )
    page.add(t)

if __name__ == "__main__":
    ft.run(main)