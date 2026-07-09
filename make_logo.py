import flet as ft
import os

def main(page: ft.Page):
    # --- 1. SET THE APPLICATION WINDOW PROPERTIES ---
    page.title = "Factory Management System - Amin & Sons"
    
    # This line sets the icon for the actual window and taskbar
    page.window_icon = os.path.join("assets", "logo.png")
    
    # Optional: Set a good initial window size and theme
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # We'll use this color for our header later
    header_color = ft.Colors.BLUE_900

    # --- 2. CREATE THE DISPLAY LOGO FOR THE UI ---
    # This control displays the logo *inside* your application's dashboard.
    self_app_logo_display = ft.Container(
        content=ft.Image(
            src="logo.png",         # Flet will look for this in the specified assets directory
            width=250,              # Controlled size for the UI
            height=250,
            fit=ft.ImageFit.CONTAIN,
            tooltip="Amin & Sons Factory Management"
        ),
        padding=10,
        alignment=ft.alignment.center
    )

    # --- 3. BASIC DASHBOARD LAYOUT TO SHOWCASE LOGO ---
    # We will build a header and a body to show how the logo is integrated.
    
    header = ft.Row([
        # Text only in the header, since the large logo is directly below
        ft.Text("فیکٹری کا ڈیش بورڈ", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
        ft.Container(expand=True),
        # Example user icon on the right
        ft.IconButton(icon=ft.icons.PERSON_PIN_CIRCLE_OUTLINED, icon_color=ft.colors.WHITE),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    header_container = ft.Container(
        content=header,
        bgcolor=header_color, # Using the predefined color variable
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.3, "black")),
    )
    
    # Main body area of the dashboard
    body = ft.Column([
        ft.Text("خوش آمدید، امین اینڈ سنز!", size=32, weight=ft.FontWeight.BOLD),
        ft.Text("آپ کا ڈیجیٹل فیکٹری مینجمنٹ حل یہاں ہے۔", size=18, color=ft.colors.GREY_700),
        ft.Container(height=30),  # Spacer
        self_app_logo_display,   # <-- Our logo is prominently displayed here
        ft.Container(height=20),  # Spacer
        ft.Text("شروع کرنے کے لیے نیچے دیے گئے کسی بھی ٹیب کو منتخب کریں۔", size=16),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    # Place the header and body in the page
    page.add(
        header_container,
        ft.Container(content=body, padding=ft.padding.symmetric(horizontal=30, vertical=20), expand=True)
    )

if __name__ == "__main__":
    # Specify the assets directory path relative to this script
    assets_path = os.path.join(os.path.dirname(__file__), "assets")
    
    # CRITICAL FIX: Run the application and specify the assets_dir
    # This tells Flet where to look for your logo.png file.
    ft.app(target=main, assets_dir=assets_path)