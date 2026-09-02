"""Configuration dialog using tkinter."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List, Optional

from .config import Config, load_config, save_config
from .effects import get_available_effect_names


class ConfigDialog:
    """Configuration dialog for the screensaver."""

    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("TTE Screensaver Settings")
        self.root.geometry("800x900")
        self.root.resizable(True, True)

        # Store checkbox variables
        self.effect_vars: dict[str, tk.BooleanVar] = {}

        self._create_widgets()
        self._load_current_config()

    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Live dashboard section
        dash_frame = ttk.LabelFrame(main_frame, text="Live dashboard", padding="10")
        dash_frame.pack(fill=tk.X, pady=(0, 10))

        self.use_live_dashboard_var = tk.BooleanVar(value=self.config.use_live_dashboard)
        ttk.Checkbutton(
            dash_frame,
            text="Use live time / date / weather",
            variable=self.use_live_dashboard_var,
        ).pack(anchor=tk.W, pady=(0, 6))

        clock_row = ttk.Frame(dash_frame)
        clock_row.pack(fill=tk.X, pady=2)
        ttk.Label(clock_row, text="Clock format:").pack(side=tk.LEFT)
        self.clock_format_var = tk.StringVar(value=self.config.clock_format or "24h")
        clock_combo = ttk.Combobox(
            clock_row,
            textvariable=self.clock_format_var,
            values=("24h", "12h"),
            state="readonly",
            width=8,
        )
        clock_combo.pack(side=tk.LEFT, padx=(10, 0))

        font_row = ttk.Frame(dash_frame)
        font_row.pack(fill=tk.X, pady=2)
        ttk.Label(font_row, text="Figlet font:").pack(side=tk.LEFT)
        self.figlet_font_var = tk.StringVar(value=self.config.figlet_font or "slant")
        ttk.Entry(font_row, textvariable=self.figlet_font_var, width=16).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        coord_row = ttk.Frame(dash_frame)
        coord_row.pack(fill=tk.X, pady=2)
        ttk.Label(coord_row, text="Latitude:").pack(side=tk.LEFT)
        lat_val = "" if self.config.latitude is None else str(self.config.latitude)
        self.lat_var = tk.StringVar(value=lat_val)
        ttk.Entry(coord_row, textvariable=self.lat_var, width=12).pack(
            side=tk.LEFT, padx=(10, 16)
        )
        ttk.Label(coord_row, text="Longitude:").pack(side=tk.LEFT)
        lon_val = "" if self.config.longitude is None else str(self.config.longitude)
        self.lon_var = tk.StringVar(value=lon_val)
        ttk.Entry(coord_row, textvariable=self.lon_var, width=12).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        ttk.Label(
            dash_frame,
            text="Paste lat/lon from Google Maps. Leave empty for time/date only.",
            font=("", 8),
        ).pack(anchor=tk.W, pady=(0, 4))

        unit_row = ttk.Frame(dash_frame)
        unit_row.pack(fill=tk.X, pady=2)
        ttk.Label(unit_row, text="Temperature unit:").pack(side=tk.LEFT)
        self.temp_unit_var = tk.StringVar(value=self.config.temperature_unit or "celsius")
        ttk.Radiobutton(
            unit_row, text="C", variable=self.temp_unit_var, value="celsius"
        ).pack(side=tk.LEFT, padx=(10, 4))
        ttk.Radiobutton(
            unit_row, text="F", variable=self.temp_unit_var, value="fahrenheit"
        ).pack(side=tk.LEFT)

        loc_row = ttk.Frame(dash_frame)
        loc_row.pack(fill=tk.X, pady=2)
        ttk.Label(loc_row, text="Location label (optional):").pack(side=tk.LEFT)
        self.location_label_var = tk.StringVar(value=self.config.location_label or "")
        ttk.Entry(loc_row, textvariable=self.location_label_var, width=28).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        max_row = ttk.Frame(dash_frame)
        max_row.pack(fill=tk.X, pady=2)
        ttk.Label(max_row, text="Max effect seconds:").pack(side=tk.LEFT)
        self.max_effect_seconds_var = tk.StringVar(
            value=str(getattr(self.config, "max_effect_seconds", 45) or 45)
        )
        ttk.Entry(max_row, textvariable=self.max_effect_seconds_var, width=8).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        # ASCII Art section
        art_label = ttk.Label(main_frame, text="ASCII Art (fallback):", font=("", 10, "bold"))
        art_label.pack(anchor=tk.W, pady=(0, 5))

        art_hint = ttk.Label(
            main_frame,
            text="Used when live dashboard is off. Generate at: patorjk.com/software/taag",
            font=("", 8),
        )
        art_hint.pack(anchor=tk.W)

        # ASCII art text area with monospace font
        self.art_text = scrolledtext.ScrolledText(
            main_frame,
            width=80,
            height=8,
            font=("Consolas", 10),
            wrap=tk.NONE,
        )
        self.art_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # Add horizontal scrollbar
        h_scroll = ttk.Scrollbar(
            self.art_text, orient=tk.HORIZONTAL, command=self.art_text.xview
        )
        self.art_text.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Effects section
        effects_header = ttk.Frame(main_frame)
        effects_header.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(effects_header, text="Enabled Effects:", font=("", 10, "bold")).pack(side=tk.LEFT)

        # Select All / None buttons
        ttk.Button(effects_header, text="Select All", command=self._select_all_effects, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(effects_header, text="Select None", command=self._select_no_effects, width=10).pack(side=tk.RIGHT)

        # Effects frame - simple grid, no scrolling needed
        effects_frame = ttk.Frame(main_frame)
        effects_frame.pack(fill=tk.X, pady=(0, 10))

        # Create checkboxes for each effect in a 5-column grid
        available_effects = get_available_effect_names()
        num_cols = 5
        for idx, effect_name in enumerate(available_effects):
            var = tk.BooleanVar(value=effect_name in self.config.enabled_effects)
            self.effect_vars[effect_name] = var

            row = idx // num_cols
            col = idx % num_cols

            cb = ttk.Checkbutton(effects_frame, text=effect_name, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=8, pady=3)

        # Make columns expand evenly
        for col in range(num_cols):
            effects_frame.columnconfigure(col, weight=1)

        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Font size
        font_frame = ttk.Frame(settings_frame)
        font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT)
        self.font_var = tk.StringVar(value=str(self.config.font_size))
        font_entry = ttk.Entry(font_frame, textvariable=self.font_var, width=10)
        font_entry.pack(side=tk.LEFT, padx=(10, 0))

        # FPS
        fps_frame = ttk.Frame(settings_frame)
        fps_frame.pack(fill=tk.X, pady=2)

        ttk.Label(fps_frame, text="Target FPS:").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value=str(self.config.target_fps))
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=10)
        fps_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Save", command=self._save).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(
            side=tk.RIGHT
        )
        ttk.Button(button_frame, text="Preview", command=self._preview).pack(
            side=tk.LEFT
        )

    def _select_all_effects(self) -> None:
        """Select all effects."""
        for var in self.effect_vars.values():
            var.set(True)

    def _select_no_effects(self) -> None:
        """Deselect all effects."""
        for var in self.effect_vars.values():
            var.set(False)

    def _load_current_config(self) -> None:
        """Load current config values into the dialog."""
        self.art_text.delete("1.0", tk.END)
        self.art_text.insert("1.0", self.config.ascii_art)

        self.use_live_dashboard_var.set(bool(self.config.use_live_dashboard))
        self.clock_format_var.set(self.config.clock_format or "24h")
        self.figlet_font_var.set(self.config.figlet_font or "slant")
        self.lat_var.set("" if self.config.latitude is None else str(self.config.latitude))
        self.lon_var.set("" if self.config.longitude is None else str(self.config.longitude))
        self.temp_unit_var.set(self.config.temperature_unit or "celsius")
        self.location_label_var.set(self.config.location_label or "")
        self.max_effect_seconds_var.set(str(getattr(self.config, "max_effect_seconds", 45) or 45))
        self.font_var.set(str(self.config.font_size))
        self.fps_var.set(str(self.config.target_fps))

    def _get_enabled_effects(self) -> List[str]:
        """Get list of enabled effects from checkboxes."""
        return [name for name, var in self.effect_vars.items() if var.get()]

    def _parse_coord(self, raw: str, name: str) -> tuple[Optional[float], Optional[str]]:
        raw = (raw or "").strip()
        if raw == "":
            return None, None
        try:
            return float(raw), None
        except ValueError:
            return None, f"Invalid {name}. Use a number or leave empty."

    def _validate_and_get_config(self) -> Config | None:
        """Validate inputs and return new config, or None if invalid."""
        try:
            font_size = int(self.font_var.get())
            if font_size <= 0:
                raise ValueError("Font size must be positive")
        except ValueError:
            messagebox.showerror("Error", "Invalid font size. Must be a positive integer.")
            return None

        try:
            fps = int(self.fps_var.get())
            if fps <= 0:
                raise ValueError("FPS must be positive")
        except ValueError:
            messagebox.showerror("Error", "Invalid FPS. Must be a positive integer.")
            return None

        enabled_effects = self._get_enabled_effects()
        if not enabled_effects:
            messagebox.showerror("Error", "Please select at least one effect.")
            return None

        use_live = bool(self.use_live_dashboard_var.get())
        ascii_art = self.art_text.get("1.0", tk.END).rstrip()
        if not use_live and not ascii_art.strip():
            messagebox.showerror("Error", "Please enter some ASCII art.")
            return None

        latitude, err = self._parse_coord(self.lat_var.get(), "latitude")
        if err:
            messagebox.showerror("Error", err)
            return None
        longitude, err = self._parse_coord(self.lon_var.get(), "longitude")
        if err:
            messagebox.showerror("Error", err)
            return None

        try:
            max_effect_seconds = int(self.max_effect_seconds_var.get().strip())
            if max_effect_seconds <= 0:
                raise ValueError("must be positive")
        except ValueError:
            messagebox.showerror("Error", "Max effect seconds must be a positive integer.")
            return None

        clock_format = (self.clock_format_var.get() or "24h").strip()
        if clock_format not in ("24h", "12h"):
            clock_format = "24h"

        temp_unit = (self.temp_unit_var.get() or "celsius").strip()
        if temp_unit not in ("celsius", "fahrenheit"):
            temp_unit = "celsius"

        return Config(
            ascii_art=ascii_art,
            enabled_effects=enabled_effects,
            font_size=font_size,
            background_color=self.config.background_color,
            target_fps=fps,
            use_live_dashboard=use_live,
            clock_format=clock_format,
            figlet_font=(self.figlet_font_var.get() or "slant").strip() or "slant",
            latitude=latitude,
            longitude=longitude,
            temperature_unit=temp_unit,
            location_label=self.location_label_var.get(),
            max_effect_seconds=max_effect_seconds,
        )

    def _save(self) -> None:
        """Save configuration and close dialog."""
        new_config = self._validate_and_get_config()
        if new_config:
            save_config(new_config)
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.root.destroy()

    def _cancel(self) -> None:
        """Close dialog without saving."""
        self.root.destroy()

    def _preview(self) -> None:
        """Run a preview of the screensaver with current settings."""
        new_config = self._validate_and_get_config()
        if new_config:
            # Import here to avoid circular imports
            from .screensaver import run_screensaver

            # Hide the dialog while previewing
            self.root.withdraw()
            try:
                run_screensaver(fullscreen=False, config=new_config)
            finally:
                self.root.deiconify()

    def run(self) -> None:
        """Run the dialog."""
        self.root.mainloop()


def show_config_dialog() -> None:
    """Show the configuration dialog."""
    dialog = ConfigDialog()
    dialog.run()
