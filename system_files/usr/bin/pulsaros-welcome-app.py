#!/usr/bin/env python3
# Copyright (c) 2026 Sizedalloy33
# SPDX-License-Identifier: Apache-2.0
# See LICENSE file in the project root for full license information.
"""
PulsarOS Welcome App

Lets users optionally install curated apps, drivers, and system extras
after first boot (or any time later from the app menu).

Design notes for anyone reading/maintaining this later:
- Each installable thing is one entry in the ITEMS list below. Add a new
  item there and it automatically shows up in the right tab with a working
  install button -- no other code changes needed.
- Installs run in a background thread so the window doesn't freeze while
  a command is running.
- GTK is NOT thread-safe. The background thread never touches a widget
  directly -- it always hands the update off to the main thread via
  GLib.idle_add(). This is the standard, correct pattern for this kind
  of app.
"""

import os
import subprocess
import sys
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

def ensure_user_remote():
    try:
        subprocess.run(
            ["flatpak", "remote-add", "--if-not-exists", "--user",
            "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"],
            capture_output=True, text=True
        )
    except Exception as e:
        print (f"Warning: could not ensure flathub remote: {e}")

# ---------------------------------------------------------------------------
# All installable items live here. To add something new, add one dict below.
#   name        -- shown in bold
#   description -- shown underneath, smaller/grey
#   command     -- list of args, exactly as you'd type them in a terminal
#   tab         -- which notebook tab this item appears under
#   reboot      -- True if this needs a reboot to take effect (rpm-ostree
#                  installs do; flatpak installs don't)
# ---------------------------------------------------------------------------
ITEMS = [
    {
        "name": "ProtonPlus",
        "description": "Manage GE-Proton and other Steam compatibility tools",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "com.vysp3r.ProtonPlus"],
        "tab": "Recommended",
        "reboot": False,
    },
    {
        "name": "Discord",
        "description": "Voice, video, and text chat for gamers and communities",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "com.discordapp.Discord"],
        "tab": "Recommended",
        "reboot": False,
    },
    {
        "name": "OnlyOffice",
        "description": "Document, spreadsheet, and presentation editor with strong Microsoft Office file compatibility",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "org.onlyoffice.desktopeditors"],
        "tab": "Recommended",
        "reboot": False,
    },
   {
        "name": "Prism Launcher",
        "description": "An open-source Minecraft launcher with the ability to manage multiple instances, accounts and mods.",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "org.prismlauncher.PrismLauncher"],
        "tab": "Gaming",
        "reboot": False,
    },
    {
        "name": "Video Codec Support (H.264)",
        "description": "Enables smooth video calls and playback in Firefox (WebRTC, some streaming sites)",
        "command": ["sudo", "rpm-ostree", "install", "mozilla-openh264"],
        "tab": "Essentials",
        "reboot": True,
    },
    {
        "name": "OnlyOffice",
        "description": "Document, spreadsheet, and presentation editor with strong Microsoft Office file compatibility",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "org.onlyoffice.desktopeditors"],
        "tab": "Productivity",
        "reboot": False,
    },
    {
        "name": "ProtonPlus",
        "description": "Manage GE-Proton and other Steam compatibility tools",
        "command": ["flatpak", "install", "-y", "--user", "flathub", "com.vysp3r.ProtonPlus"],
        "tab": "Gaming",
        "reboot": False,
    },
    {
        "name": "Fanatec Wheel Support",
        "description": "Driver support for Fanatec force-feedback racing wheels",
        "command": ["sudo", "rpm-ostree", "install", "hid-fanatecff", "kmod-hid-fanatecff"],
        "tab": "Drivers",
        "reboot": True,
    },
    {
        "name": "Thrustmaster Wheel Support",
        "description": "Driver support for Thrustmaster force-feedback racing wheels",
        "command": ["sudo", "rpm-ostree", "install", "hid-tmff2", "kmod-hid-tmff2"],
        "tab": "Drivers",
        "reboot": True,
    },
    {
        "name": "Logitech Wheel Support",
        "description": "Driver support for Logitech G-series force-feedback racing wheels",
        "command": ["sudo", "rpm-ostree", "install", "new-lg4ff", "new-lg4ff-akmod-modules"],
        "tab": "Drivers",
        "reboot": True,
    },
    {
        "name": "Razer Peripheral Support",
        "description": "Driver support for Razer keyboards, mice, and other peripherals",
        "command": ["sudo", "rpm-ostree", "install", "openrazer-kmod-common"],
        "tab": "Drivers",
        "reboot": True,
    },
    {
    	"name": "Cockpit",
    	"description": "Web-based system management UI for monitoring, storage, networking, and containers",
    	"command": ["sudo", "rpm-ostree", "install", "cockpit-bridge", "cockpit-files", "cockpit-networkmanager", "cockpit-podman", "cockpit-selinux", "cockpit-storaged", "cockpit-system"],
    	"tab": "System",
    	"reboot": True,
    },
    {
    "name": "Wii Remote Support",
    "description": "Driver support for Nintendo Wii Remote and Wii U Pro Controller via Bluetooth",
    "command": ["sudo", "rpm-ostree", "install", "xwiimote-ng"],
    "tab": "Drivers",
    "reboot": True,
    },
]

TAB_ORDER = ["Recommended", "Essentials", "Drivers", "Gaming", "Productivity", "System"]

# If this file exists, the app won't auto-launch at startup (it can still be
# opened manually from the app menu, which passes --force and skips this check).
DISABLE_FLAG = os.path.expanduser("~/.config/no-welcome-app")


class InstallRow(Gtk.Box):
    """One row in a tab: name/description on the left, button + status on the right."""

    def __init__(self, item):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.item = item
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)

        # --- Left side: name + description ---
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_label = Gtk.Label(label=f"<b>{item['name']}</b>", use_markup=True, xalign=0)
        desc_label = Gtk.Label(label=item["description"], xalign=0)
        desc_label.get_style_context().add_class("dim-label")
        desc_label.set_line_wrap(True)
        text_box.pack_start(name_label, False, False, 0)
        text_box.pack_start(desc_label, False, False, 0)
        self.pack_start(text_box, True, True, 0)

        # --- Right side: progress bar (hidden until running) + button ---
        self.progress = Gtk.ProgressBar()
        self.progress.set_size_request(100, -1)
        self.progress.set_no_show_all(True)  # stays hidden until we explicitly show it

        self.button = Gtk.Button(label="Install")
        self.button.connect("clicked", self.on_install_clicked)

        self.pack_start(self.progress, False, False, 0)
        self.pack_start(self.button, False, False, 0)

    def on_install_clicked(self, _button):
        self.button.set_sensitive(False)
        self.button.set_label("Installing…")
        self.progress.show()
        self.progress.pulse()

        # Pulse the bar every 100ms while the install runs.
        self._pulse_timer_id = GLib.timeout_add(100, self._pulse)

        # Run the actual install off the main thread so the UI stays responsive.
        thread = threading.Thread(target=self._run_install, daemon=True)
        thread.start()

    def _pulse(self):
        self.progress.pulse()
        return True  # returning True keeps the timer running

    def _run_install(self):
        """Runs in a background thread. Never touch GTK widgets directly here --
        always hand off to the main thread via GLib.idle_add."""
        try:
            result = subprocess.run(
                self.item["command"],
                capture_output=True,
                text=True,
            )
            success = result.returncode == 0
            error_text = result.stderr.strip() if not success else ""
        except Exception as e:
            success = False
            error_text = str(e)

        GLib.idle_add(self._on_install_finished, success, error_text)

    def _on_install_finished(self, success, error_text):
        GLib.source_remove(self._pulse_timer_id)
        self.progress.hide()

        if success:
            self.button.set_label("Installed ✓")
            if self.item.get("reboot"):
                self.button.set_label("Installed ✓ (reboot required)")
        else:
            self.button.set_label("Install")
            self.button.set_sensitive(True)
            self._show_error_dialog(error_text)

        return False  # required by GLib.idle_add convention; don't call again

    def _show_error_dialog(self, error_text):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=f"Failed to install {self.item['name']}",
        )
        dialog.format_secondary_text(error_text or "No error details were returned.")
        dialog.run()
        dialog.destroy()


class WelcomeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Welcome to PulsarOS")
        ensure_user_remote()
        self.set_default_size(600, 450)
        self.set_border_width(0)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        header = Gtk.Label(
            label="<span size='x-large' weight='bold'>Welcome to PulsarOS</span>\n"
            "Install anything you'd like below -- nothing downloads until you click Install.",
            use_markup=True,
        )
        header.set_margin_top(16)
        header.set_margin_bottom(12)
        outer_box.pack_start(header, False, False, 0)

        notebook = Gtk.Notebook()
        outer_box.pack_start(notebook, True, True, 0)

        self.disable_checkbox = Gtk.CheckButton(label="Don't show this on startup")
        self.disable_checkbox.set_margin_top(4)
        self.disable_checkbox.set_margin_bottom(4)
        self.disable_checkbox.set_margin_start(12)
        # Reflect whatever the current setting actually is, so this stays
        # accurate whether the app was auto-launched or opened from the menu.
        self.disable_checkbox.set_active(os.path.exists(DISABLE_FLAG))

        # Build one tab per category, and one row per item in that category.
        for tab_name in TAB_ORDER:
            tab_items = [i for i in ITEMS if i["tab"] == tab_name]

            scroller = Gtk.ScrolledWindow()
            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            if tab_items:
                for item in tab_items:
                    list_box.pack_start(InstallRow(item), False, False, 0)
                    list_box.pack_start(Gtk.Separator(), False, False, 0)
            else:
                placeholder = Gtk.Label(label="Nothing here yet.")
                placeholder.set_margin_top(20)
                list_box.pack_start(placeholder, False, False, 0)

            scroller.add(list_box)
            notebook.append_page(scroller, Gtk.Label(label=tab_name))

        outer_box.pack_start(self.disable_checkbox, False, False, 0)

        self.add(outer_box)
        self.connect("destroy", self.on_close)

    def on_close(self, _widget):
        if self.disable_checkbox.get_active():
            # Create the file if it doesn't already exist.
            open(DISABLE_FLAG, "a").close()
        else:
            if os.path.exists(DISABLE_FLAG):
                os.remove(DISABLE_FLAG)


def main():
    forced = "--force" in sys.argv
    if not forced and os.path.exists(DISABLE_FLAG):
        # Auto-started at boot, but the user asked not to see this. Exit quietly.
        return

    win = WelcomeWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
