import os
import time
import re
import flet as ft
from datetime import datetime
from scout_engine import ScoutEngine
from tray_manager import TrayManager
import winreg
import sys

def main(page: ft.Page):
    page.title = "Scout - Active Defense"
    page.theme_mode = "light"  # Professional/Corporate look
    # Using older Flet 0.23 style syntax for compatibility natively
    page.window.width = 1000
    page.window.height = 800
    page.padding = 0
    page.bgcolor = ft.colors.BLUE_GREY_50
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap"}
    page.theme = ft.Theme(font_family="Inter")
    
    engine = ScoutEngine()
    
    # Colors
    PRIMARY = ft.colors.BLUE_GREY_800
    SECONDARY = ft.colors.BLUE_GREY_500
    ACCENT = ft.colors.BLUE_800
    SURFACE = ft.colors.WHITE
    ERROR = ft.colors.RED_700
    SUCCESS = ft.colors.GREEN_700

    # Pages Map
    pages_container = ft.Container(expand=True, padding=30)
    
    def change_route(e):
        index = nav_rail.selected_index
        pages_container.content = views[index]
        page.update()

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.DASHBOARD_OUTLINED, selected_icon=ft.icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.icons.SECURITY_OUTLINED, selected_icon=ft.icons.SECURITY, label="Targets"),
            ft.NavigationRailDestination(icon=ft.icons.HISTORY_OUTLINED, selected_icon=ft.icons.HISTORY, label="Audit Log"),
            ft.NavigationRailDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="Settings"),
        ],
        on_change=change_route,
        bgcolor=ft.colors.WHITE,
    )
    
    # --- VIEWS ---
    
    # 1. Dashboard
    
    dashboard_view = ft.Column(expand=True)
    
    def render_dashboard():
        total_targets = len(engine.tracked_targets)
        history_len = len(engine.history_log)
        
        card1 = ft.Card(content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Active Targets", size=14, color=SECONDARY),
            ft.Text(f"{total_targets}", size=36, weight="bold", color=PRIMARY)
        ])), elevation=2)
        
        card2 = ft.Card(content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Lifetime Events", size=14, color=SECONDARY),
            ft.Text(f"{history_len}", size=36, weight="bold", color=PRIMARY)
        ])), elevation=2)

        def show_help(e):
            dlg = ft.AlertDialog(
                title=ft.Text("How Scout Works"),
                content=ft.Text("Scout is a native Active Defense Daemon.\n\n- STRICT target folders completely lock down all files inside them, blocking ransomware and unapproved edits at the OS Level.\n- MONITORING targets silently watch for changes and capture process forensics instantly.\n\nFiles opened via 'Checkout' temporarily lower defenses to allow authorized edits."),
                actions=[ft.TextButton("Dismiss", on_click=lambda e: close_dlg(dlg))]
            )
            def close_dlg(d):
                d.open = False
                page.update()
            page.dialog = dlg
            dlg.open = True
            page.update()

        dashboard_view.controls = [
            ft.Row([
                ft.Text("Scout Overview", size=28, weight="bold", color=PRIMARY),
                ft.IconButton(ft.icons.HELP_OUTLINE, tooltip="Help Guide", on_click=show_help, icon_color=ACCENT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([card1, card2], spacing=20),
            ft.Container(height=30),
            ft.Text("System Engine Status", size=18, weight="bold", color=PRIMARY),
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE if engine.is_running else ft.icons.CANCEL, color=SUCCESS if engine.is_running else ERROR), 
                ft.Text("Scout Kernel Defense Engine Active" if engine.is_running else "Kernel Engine Offline")
            ]),
            ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE if bool(engine.vault) else ft.icons.CANCEL, color=SUCCESS), 
                ft.Text("Sentinel Self-Healing Vault Active")
            ]),
            ft.Row([
                ft.Icon(ft.icons.NOTIFICATIONS_ACTIVE if engine.toaster else ft.icons.NOTIFICATIONS_OFF, color=SUCCESS if engine.toaster else ERROR), 
                ft.Text("Native OS Subsystems Linked" if engine.toaster else "Native OS Subsystems Unlinked")
            ])
        ]
    
    # 2. Targets View
    targets_view = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    
    # Navigation StateTracker for Recursive File Explorer
    browser_history = []

    def update_child_mode(path, mode, is_folder):
        if mode == "INHERIT":
            engine.remove_target(path)
        else:
            engine.add_target(path, is_folder=is_folder, mode=mode)
        render_targets()
        page.update()

    # Reverting AnimatedSwitcher to a static container for stability on this Flet version
    target_list_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    def navigate_explorer(path):
        browser_history.append(path)
        render_targets()
        page.update()

    def navigate_back(e):
        if browser_history:
            browser_history.pop()
        render_targets()
        page.update()

    def vet_baseline(path):
        if engine.vet_target(path):
            page.snack_bar = ft.SnackBar(ft.Text(f"Target Vetted & Baselined: {os.path.basename(path)}"), bgcolor=ft.colors.GREEN_700)
            page.snack_bar.open = True
            page.update()

    def create_explorer_node(current_path, is_explicit_root=False):
        is_folder = os.path.isdir(current_path)
        l_mode = engine._resolve_target_mode(current_path)
        is_explicit = current_path in engine.tracked_targets
        
        if is_explicit_root:
            val = engine.tracked_targets.get(current_path, {}).get("mode", l_mode)
            dropdown_opts = [ft.dropdown.Option("STRICT"), ft.dropdown.Option("MONITORING")]
        else:
            val = l_mode if is_explicit else "INHERIT"
            dropdown_opts = [ft.dropdown.Option("INHERIT"), ft.dropdown.Option("STRICT"), ft.dropdown.Option("MONITORING")]

        # Improved Dropdown UI Contrast without text clipping
        drop = ft.Dropdown(
            value=val,
            options=dropdown_opts,
            width=160,
            text_size=12,
            content_padding=ft.padding.only(left=10, right=10),
            color=PRIMARY, 
            bgcolor=ft.colors.WHITE, 
            border_color=ft.colors.BLUE_GREY_200,
            focused_border_color=ACCENT,
            border_radius=8,
            on_change=lambda e, p=current_path, f=is_folder: update_child_mode(p, e.control.value, f)
        )

        is_checked_out = engine._is_path_authorized(current_path)
        is_locked = (val == "STRICT") and not is_checked_out
        status = "LOCKED (Zero Trust)" if is_locked else ("WATCHING" if val == "MONITORING" else "UNLOCKED (Authorized)")
        s_color = ERROR if is_locked else (ACCENT if "WATCHING" in status else ft.colors.AMBER_800)

        checkout_btn = ft.Container()
        # Enable Checkout for BOTH files and folders if in STRICT mode
        if val == "STRICT":
            if is_locked:
                checkout_btn = ft.ElevatedButton("Checkout", height=35, on_click=lambda e, p=current_path: toggle_checkout(p, True))
            else:
                checkout_btn = ft.ElevatedButton("Check-In", height=35, bgcolor=ERROR, color=ft.colors.WHITE, on_click=lambda e, p=current_path: toggle_checkout(p, False))

        icon = ft.icons.FOLDER if is_folder else ft.icons.INSERT_DRIVE_FILE
        
        def on_node_click(e):
            if is_folder:
                navigate_explorer(current_path)
        
        vet_btn = ft.Container()
        if not is_folder:
            vet_btn = ft.IconButton(
                ft.icons.VERIFIED, 
                icon_color=ft.colors.GREEN_600, 
                tooltip="Vet Current State (Reset Baseline)",
                on_click=lambda e, p=current_path: vet_baseline(p)
            )

        header_row = ft.Row([
            ft.Icon(icon, color=PRIMARY, size=30),
            ft.Container(content=ft.Column([
                ft.Text(os.path.basename(current_path) or current_path, weight="bold", size=14, color=PRIMARY),
                ft.Text(status, color=s_color, size=11, weight="bold")
            ]), on_click=on_node_click, expand=True, padding=5, tooltip="Click to open folder" if is_folder else ""),
            vet_btn,
            checkout_btn,
            drop,
        ])
        
        if is_explicit_root:
            header_row.controls.append(ft.IconButton(ft.icons.DELETE, icon_color=ERROR, tooltip="Untrack Root", on_click=lambda e, p=current_path: remove_target(p)))

        # Using standard Container on_click instead of raw gesture detectors for fluid SPA navigation
        return ft.Card(content=ft.Container(content=header_row, padding=10), elevation=2 if is_explicit_root else 1)

    def render_targets():
        target_list = ft.Column(spacing=10)
        current_dir = browser_history[-1] if browser_history else None

        if current_dir:
            breadcrumbs = ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color=PRIMARY, on_click=navigate_back),
                ft.Text(current_dir, size=16, weight="bold", color=PRIMARY, expand=True)
            ])
            target_list.controls.append(breadcrumbs)
            target_list.controls.append(ft.Divider())

            try:
                for item in os.listdir(current_dir):
                    child_path = os.path.join(current_dir, item)
                    target_list.controls.append(create_explorer_node(child_path, is_explicit_root=False))
            except Exception:
                target_list.controls.append(ft.Text("Access Denied or Directory Empty.", italic=True, color=ERROR))

        else:
            # We are at Root
            if not engine.tracked_targets:
                target_list.controls.append(ft.Text("No files or folders are currently secured.", italic=True, color=SECONDARY))
            
            roots = []
            for path in engine.tracked_targets.keys():
                is_child = False
                for parent_path, info in engine.tracked_targets.items():
                    if info["type"] == "folder" and path != parent_path and path.startswith(parent_path):
                        is_child = True
                        break
                if not is_child:
                    roots.append(path)
                    
            for root in roots:
                target_list.controls.append(create_explorer_node(root, is_explicit_root=True))
                
        # Clear and rebuild the targets view to ensure UI sync
        targets_view.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Security Targets", size=28, weight="bold", color=PRIMARY, expand=True),
                        ft.ElevatedButton("Add File", icon=ft.icons.NOTE_ADD, bgcolor=PRIMARY, color=ft.colors.WHITE, on_click=lambda _: file_picker.pick_files(allow_multiple=True)),
                        ft.ElevatedButton("Add Folder", icon=ft.icons.CREATE_NEW_FOLDER, bgcolor=ACCENT, color=ft.colors.WHITE, on_click=lambda _: folder_picker.get_directory_path())
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(height=20, thickness=1),
                ]),
                padding=ft.padding.only(bottom=10)
            ),
            ft.Container(content=target_list, expand=True)
        ]
        page.update()
        
    def toggle_checkout(path, check_out: bool):
        if check_out:
            engine.checkout(path)
        else:
            engine.checkin(path)
        render_targets()
        page.update()
        
    def change_target_mode(path, mode):
        engine.update_target_mode(path, mode)
        render_targets()
        page.update()
        
    def remove_target(path):
        engine.remove_target(path)
        render_targets()
        render_dashboard()
        page.update()
        
    def on_files_picked(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                engine.add_target(f.path, is_folder=False)
            reboot_engine()
            
    def on_folder_picked(e: ft.FilePickerResultEvent):
        if e.path:
            engine.add_target(e.path, is_folder=True)
            reboot_engine()

    def on_vault_picked(e: ft.FilePickerResultEvent):
        if e.path:
            engine.update_vault_path(e.path)
            render_settings()
            page.update()

    def reboot_engine():
        engine.stop()
        dirs_to_watch = set()
        for p, info in engine.tracked_targets.items():
            if info["type"] == "folder":
                dirs_to_watch.add(p)
            else:
                dirs_to_watch.add(os.path.dirname(p))
        if dirs_to_watch:
            engine.start(list(dirs_to_watch))
        render_targets()
        render_dashboard()
        page.update()

    file_picker = ft.FilePicker(on_result=on_files_picked)
    folder_picker = ft.FilePicker(on_result=on_folder_picked)
    vault_picker = ft.FilePicker(on_result=on_vault_picked)
    page.overlay.extend([file_picker, folder_picker, vault_picker])

    # 3. Audit History View
    history_view = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    
    def render_history():
        
        def show_diff_dialog(diff_data, e_type):
            ui_rows = []
            
            # Step 1: Normalize Data (Modern List vs Legacy String)
            if isinstance(diff_data, str):
                # Legacy items from before the OpCode upgrade
                ui_rows.append(ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.HISTORY, size=40, color=ft.colors.ORANGE_300),
                        ft.Text("Legacy Forensic Data", weight="bold", size=16),
                        ft.Text("This event was captured in an older format. Please capture new modifications to see the high-fidelity OpCode alignment.", 
                                color=ft.colors.BLUE_GREY_400, italic=True),
                        ft.Container(height=20),
                        ft.Text(diff_data, color=ft.colors.BLUE_GREY_200, size=11, font_family="Consolas")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40, expand=True
                ))
            elif isinstance(diff_data, list):
                # Modern OpCode Path - Direct Rendering
                for r in diff_data:
                    # Vault Side (Left)
                    l_color = ft.colors.RED_400 if r["type"] in ["delete", "change"] else ft.colors.BLUE_GREY_200
                    l_bg = ft.colors.with_opacity(0.15, ft.colors.RED_900) if r["type"] in ["delete", "change"] else ft.colors.TRANSPARENT
                    
                    left_cell = ft.Container(
                        content=ft.Row([
                            ft.Container(content=ft.Text(str(r["left_ln"] or ""), size=10, color=ft.colors.BLUE_GREY_400), width=35),
                            ft.Text(r["left_txt"] or "", size=12, font_family="Consolas", color=l_color, selectable=True)
                        ], spacing=10),
                        bgcolor=l_bg, padding=ft.padding.only(left=5, right=5), width=580, height=22
                    )

                    # Live Side (Right)
                    r_color = ft.colors.GREEN_400 if r["type"] in ["insert", "change"] else ft.colors.BLUE_GREY_200
                    r_bg = ft.colors.with_opacity(0.15, ft.colors.GREEN_900) if r["type"] in ["insert", "change"] else ft.colors.TRANSPARENT

                    right_cell = ft.Container(
                        content=ft.Row([
                            ft.Container(content=ft.Text(str(r["right_ln"] or ""), size=10, color=ft.colors.BLUE_GREY_400), width=35),
                            ft.Text(r["right_txt"] or "", size=12, font_family="Consolas", color=r_color, selectable=True)
                        ], spacing=10),
                        bgcolor=r_bg, padding=ft.padding.only(left=5, right=5), width=580, height=22
                    )

                    ui_rows.append(ft.Container(
                        content=ft.Row([left_cell, right_cell], spacing=0),
                        border=ft.border.only(bottom=ft.BorderSide(0.5, ft.colors.GREY_800))
                    ))

            # Step 3: Handle empty state or Status messages
            if not ui_rows:
                status_icon = ft.icons.INFO_OUTLINE
                status_color = ft.colors.BLUE_GREY_600
                display_msg = "No line-level changes recorded for this event."
                
                if "FORENSIC STATUS:" in diff_text:
                    status_icon = ft.icons.SHIELD_OUTLINE
                    status_color = SECONDARY
                    display_msg = "Bridgehead Established"

                ui_rows.append(ft.Container(
                    content=ft.Column([
                        ft.Icon(status_icon, size=60, color=status_color),
                        ft.Container(height=10),
                        ft.Text(display_msg, color=ft.colors.WHITE, size=18, weight="bold"),
                        ft.Text(diff_text, color=ft.colors.BLUE_GREY_400, size=13, italic=True, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    padding=80, expand=True
                ))

            # Final Dialog Construction
            diff_dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.COMPARE_ARROWS, color=ACCENT),
                    ft.Text(f"Target Forensic Audit: {e_type}", weight="bold")
                ]),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Text("VAULT (BASE VERSION)", size=12, weight="bold", color=SECONDARY, text_align=ft.TextAlign.CENTER, expand=True),
                                ft.VerticalDivider(width=1, color=ft.colors.GREY_700),
                                ft.Text("LIVE (CURRENT VERSION)", size=12, weight="bold", color=ERROR, text_align=ft.TextAlign.CENTER, expand=True),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=ft.colors.BLUE_GREY_900, padding=10,
                            border_radius=ft.border_radius.only(top_left=8, top_right=8)
                        ),
                        ft.ListView(controls=ui_rows, spacing=1, expand=True)
                    ], spacing=0),
                    bgcolor=ft.colors.BLACK87,
                    padding=10, border_radius=8, width=1200, height=700
                ),
                actions=[
                    ft.ElevatedButton("Close Analysis", on_click=lambda _: page.close(diff_dlg), bgcolor=PRIMARY, color=ft.colors.WHITE)
                ]
            )
            page.open(diff_dlg)
            
        dt = ft.DataTable(
            heading_row_color=ft.colors.GREY_200,
            columns=[
                ft.DataColumn(ft.Text("Time", weight="bold")),
                ft.DataColumn(ft.Text("Action", weight="bold")),
                ft.DataColumn(ft.Text("Target", weight="bold")),
                ft.DataColumn(ft.Text("Culprit / Log", weight="bold")),
                ft.DataColumn(ft.Text("Diff", weight="bold")),
            ],
            rows=[]
        )
        
        for event in reversed(engine.history_log[-50:]): # Show last 50
            now = datetime.fromtimestamp(event["timestamp"]).strftime('%m/%d %H:%M')
            dt.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(now, size=12)),
                ft.DataCell(ft.Text(event["type"], color=ERROR if "MODIFIED" in event["type"] else PRIMARY, weight="bold")),
                ft.DataCell(ft.Text(os.path.basename(event["file"]), size=12)),
                ft.DataCell(ft.Text(event.get("message", "Unknown"), size=12)),
                ft.DataCell(ft.IconButton(ft.icons.SEARCH, icon_color=ACCENT, tooltip="View Diff", on_click=lambda e, d=event.get('diff', 'No diff recorded.'), t=event['type']: show_diff_dialog(d, t))),
            ]))
            
        history_view.controls = [
            ft.Text("System Audit Log", size=28, weight="bold", color=PRIMARY),
            ft.Divider(),
            dt
        ]

    # 4. Settings View
    settings_view = ft.Column(expand=True)
    
    # Auto Start Logic
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "ScoutFIM"
    def is_auto_start() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as registry_key:
                winreg.QueryValueEx(registry_key, APP_NAME)
                return True
        except FileNotFoundError:
            return False

    def toggle_auto_start(e):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as registry_key:
                if e.control.value:
                    winreg.SetValueEx(registry_key, APP_NAME, 0, winreg.REG_SZ, sys.executable + ' "' + os.path.abspath(__file__) + '"')
                else:
                    winreg.DeleteValue(registry_key, APP_NAME)
        except Exception as ex:
            pass
            
    def render_settings():
        auto_switch = ft.Switch(value=is_auto_start(), on_change=toggle_auto_start, active_color=ACCENT)
        
        wh_col = ft.Column()
        for i, wh in enumerate(engine.discord_webhooks):
            wh_col.controls.append(ft.Container(content=ft.Row([
                ft.Text(wh[:40] + "...", expand=True, color=PRIMARY),
                ft.IconButton(ft.icons.DELETE, on_click=lambda e, idx=i: remove_webhook(idx), icon_color=ERROR)
            ]), bgcolor=ft.colors.GREY_200, padding=10, border_radius=5))
            
        new_wh = ft.TextField(label="Channel Webhook URL", expand=True)
        def add_webhook(e):
            if new_wh.value:
                engine.discord_webhooks.append(new_wh.value)
                engine._save_config()
                render_settings()
                page.update()
                
        def remove_webhook(idx):
            engine.discord_webhooks.pop(idx)
            engine._save_config()
            render_settings()
            page.update()
            
        settings_view.controls = [
            ft.Text("Settings & Routing", size=28, weight="bold", color=PRIMARY),
            ft.Divider(),
            ft.Container(content=ft.Row([
                ft.Icon(ft.icons.POWER_SETTINGS_NEW, color=PRIMARY),
                ft.Text("Run Scout as Daemon on Windows Startup:", size=16, weight="bold", color=PRIMARY), 
                auto_switch
            ]), margin=ft.margin.only(bottom=30)),
            
            ft.Text("Discord Webhooks", size=20, weight="bold", color=PRIMARY),
            ft.Text("Add multiple URLs to broadcast critical alerts everywhere simultaneously.", size=12, color=SECONDARY),
            ft.Container(height=10),
            wh_col,
            ft.Container(height=10),
            ft.Row([new_wh, ft.ElevatedButton("Save Webhook", bgcolor=ACCENT, color=ft.colors.WHITE, on_click=add_webhook)]),
            
            ft.Divider(height=50),
            ft.Text("Recovery Vault Configuration", size=20, weight="bold", color=PRIMARY),
            ft.Text("Choose where Scout stores encrypted 'Last Known Good' versions of your files.", size=12, color=SECONDARY),
            ft.Container(height=15),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.STORAGE, color=ACCENT),
                    ft.Text(engine.vault.vault_path, expand=True, color=PRIMARY, size=13, weight="bold"),
                    ft.ElevatedButton("Change Location", on_click=lambda _: vault_picker.get_directory_path(), bgcolor=PRIMARY, color=ft.colors.WHITE)
                ]),
                bgcolor=ft.colors.GREY_100,
                padding=15,
                border_radius=10
            ),
            ft.Container(height=10),
            ft.Text("Note: Changing location will not move existing backups. Scout will start encoding new backups in the chosen directory.", size=12, italic=True, color=SECONDARY)
        ]

    # Global Engine Callback
    def on_engine_event(event_data):
        render_dashboard()
        render_history()
        page.update()
        
    engine.on_event_callback = on_engine_event

    views = [dashboard_view, targets_view, history_view, settings_view]

    layout = ft.Row([
        nav_rail,
        ft.VerticalDivider(width=1, color=ft.colors.GREY_300),
        pages_container
    ], expand=True)
    
    page.add(layout)
    
    # Initialize UI
    render_dashboard()
    render_targets()
    render_history()
    render_settings()
    change_route(None)

    # Start engine
    dirs_to_watch = set()
    for p, info in engine.tracked_targets.items():
        if info["type"] == "folder":
            dirs_to_watch.add(p)
        else:
            dirs_to_watch.add(os.path.dirname(p))
    if dirs_to_watch:
        engine.start(list(dirs_to_watch))

    # Tray
    def show_window():
        page.window.visible = True
        page.update()

    def quit_app():
        engine.stop()
        page.window.close()

    tray = TrayManager(show_window, quit_app)
    tray.start()
    
    # Critical: Bridge the Engine notifications to the Tray's message pump
    engine.on_notify = tray.notify

    def on_window_event(e):
        if e.data == "close":
            page.window.visible = False
            page.update()

    # Modern Flet event handling
    page.on_window_event = on_window_event
    page.window.prevent_close = True

if __name__ == "__main__":
    ft.app(target=main)
