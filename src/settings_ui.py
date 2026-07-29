from __future__ import annotations

import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Callable

from . import assets
from .config import CROSSHAIR_STYLES, DEFAULTS, HANDS, TRACER_STYLES, WEAPONS, Config

# Modern dark palette
BG = "#0f1117"
BG2 = "#171a22"
CARD = "#1c2030"
CARD_BORDER = "#2a3145"
TEXT = "#e8ecf5"
MUTED = "#8b93a7"
ACCENT = "#4f8cff"
ACCENT2 = "#3d6fd4"
SUCCESS = "#3dd68c"
DANGER = "#ff5c7a"
ENTRY_BG = "#12151e"


class SettingsWindow:
    """Modern dark settings UI on its own thread."""

    def __init__(self, config: Config, on_quit: Callable[[], None] | None = None) -> None:
        self.config = config
        self.on_quit = on_quit
        self.root: tk.Tk | None = None
        self._vars: dict[str, tk.Variable] = {}
        self._combos: dict[str, ttk.Combobox] = {}
        self._building = True
        self._ready = threading.Event()
        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._run, name="settings-ui", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5.0):
            raise RuntimeError("Settings UI failed to start")

    def _run(self) -> None:
        assets.ensure_asset_dirs()
        self.root = tk.Tk()
        self.root.title("CorporateDroneAIM")
        self.root.geometry("520x780")
        self.root.minsize(460, 560)
        self.root.configure(bg=BG)
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

        self._setup_style()
        self._building = True
        self._build()
        self._building = False
        self.config.on_change(self._on_config_changed)
        self.root.protocol("WM_DELETE_WINDOW", self._hide)
        self._ready.set()
        try:
            self.root.mainloop()
        finally:
            self._closed.set()

    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BG, foreground=TEXT, fieldbackground=ENTRY_BG)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 18))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Section.TLabel", background=CARD, foreground=ACCENT, font=("Segoe UI Semibold", 11))
        style.configure(
            "TCheckbutton",
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 10),
            focuscolor=CARD,
        )
        style.map("TCheckbutton", background=[("active", CARD)], foreground=[("active", TEXT)])
        style.configure(
            "TCombobox",
            fieldbackground=ENTRY_BG,
            background=ENTRY_BG,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=CARD_BORDER,
            lightcolor=CARD_BORDER,
            darkcolor=CARD_BORDER,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", ENTRY_BG)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", ACCENT)],
            selectforeground=[("readonly", "#fff")],
        )
        style.configure(
            "Horizontal.TScale",
            background=CARD,
            troughcolor="#0c0e14",
            bordercolor=CARD,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#fff",
            font=("Segoe UI Semibold", 10),
            padding=(12, 8),
            borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", ACCENT2), ("pressed", ACCENT2)])
        style.configure(
            "Ghost.TButton",
            background=CARD,
            foreground=TEXT,
            font=("Segoe UI", 10),
            padding=(10, 7),
            borderwidth=0,
        )
        style.map("Ghost.TButton", background=[("active", "#262b3d")])
        style.configure(
            "Danger.TButton",
            background="#3a1d28",
            foreground=DANGER,
            font=("Segoe UI", 10),
            padding=(10, 7),
        )
        style.map("Danger.TButton", background=[("active", "#4a2432")])
        style.configure(
            "Vertical.TScrollbar",
            background=CARD,
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=MUTED,
        )

    def _hide(self) -> None:
        if self.root is not None:
            self.root.withdraw()

    def show(self) -> None:
        root = self.root
        if root is None or self._closed.is_set():
            return

        def _show() -> None:
            try:
                self._refresh_asset_lists()
                root.deiconify()
                root.lift()
                root.focus_force()
            except tk.TclError:
                pass

        try:
            root.after(0, _show)
        except tk.TclError:
            pass

    def close(self) -> None:
        root = self.root
        if root is None:
            return

        def _destroy() -> None:
            try:
                root.quit()
                root.destroy()
            except tk.TclError:
                pass

        try:
            root.after(0, _destroy)
        except tk.TclError:
            pass
        self._thread.join(timeout=2.0)

    def _card(self, parent: tk.Widget, title: str) -> tk.Frame:
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="x", pady=8, padx=8)
        outer = tk.Frame(wrap, bg=CARD_BORDER, bd=0, highlightthickness=0)
        outer.pack(fill="x")
        inner = tk.Frame(outer, bg=CARD, bd=0)
        inner.pack(fill="x", padx=1, pady=1)
        head = tk.Frame(inner, bg=CARD)
        head.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(head, text=title, bg=CARD, fg=ACCENT, font=("Segoe UI Semibold", 11)).pack(anchor="w")
        body = tk.Frame(inner, bg=CARD)
        body.pack(fill="x", padx=12, pady=(0, 14))
        return body

    def _add_scale(
        self,
        parent: tk.Misc,
        key: str,
        label: str,
        from_: float,
        to: float,
        fmt: str,
    ) -> None:
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label, bg=CARD, fg=MUTED, font=("Segoe UI", 9), width=18, anchor="w").pack(
            side="left"
        )
        var = tk.DoubleVar(value=float(self.config.get(key)))
        self._vars[key] = var
        val_lbl = tk.Label(row, bg=CARD, fg=TEXT, font=("Segoe UI Semibold", 9), width=7, anchor="e")

        def apply_value(persist: bool) -> None:
            v = float(var.get())
            val_lbl.configure(text=fmt.format(v))
            if self._building:
                return
            self.config.update(immediate_save=persist, **{key: v})

        def on_slide(_=None) -> None:
            apply_value(persist=False)

        def on_release(_event=None) -> None:
            apply_value(persist=True)

        scale = ttk.Scale(row, from_=from_, to=to, variable=var, command=on_slide)
        scale.pack(side="left", fill="x", expand=True, padx=8)
        scale.bind("<ButtonRelease-1>", on_release)
        val_lbl.pack(side="left")
        val_lbl.configure(text=fmt.format(float(var.get())))

    def _add_check(self, parent: tk.Misc, key: str, label: str) -> None:
        var = tk.BooleanVar(value=bool(self.config.get(key)))
        self._vars[key] = var

        def on_toggle() -> None:
            if not self._building:
                self.config.update(immediate_save=True, **{key: bool(var.get())})

        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            command=on_toggle,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            selectcolor=ENTRY_BG,
            font=("Segoe UI", 10),
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        cb.pack(fill="x", pady=2)

    def _add_combo(
        self,
        parent: tk.Misc,
        key: str,
        label: str,
        values: list[str],
        *,
        allow_empty: bool = False,
    ) -> ttk.Combobox:
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=CARD, fg=MUTED, font=("Segoe UI", 9), width=18, anchor="w").pack(
            side="left"
        )
        cur = str(self.config.get(key) or "")
        if allow_empty and not cur:
            cur = assets.NONE_LABEL
        vals = list(values)
        if cur and cur not in vals and cur != assets.NONE_LABEL:
            vals.append(cur)
        var = tk.StringVar(value=cur)
        self._vars[key] = var
        cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly")
        cb.pack(side="left", fill="x", expand=True)
        self._combos[key] = cb

        def on_sel(_e=None) -> None:
            if self._building:
                return
            val = var.get()
            if allow_empty and val == assets.NONE_LABEL:
                val = ""
            self.config.update(immediate_save=True, **{key: val})

        cb.bind("<<ComboboxSelected>>", on_sel)
        return cb

    def _color_row(self, parent: tk.Misc, prefix: str, label: str) -> None:
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=CARD, fg=MUTED, font=("Segoe UI", 9), width=18, anchor="w").pack(
            side="left"
        )
        r = int(self.config.get(f"{prefix}_r"))
        g = int(self.config.get(f"{prefix}_g"))
        b = int(self.config.get(f"{prefix}_b"))
        preview = tk.Label(row, text="  ", bg=f"#{r:02x}{g:02x}{b:02x}", width=4, relief="flat")
        preview.pack(side="left", padx=(0, 8))

        def pick() -> None:
            cr = int(self.config.get(f"{prefix}_r"))
            cg = int(self.config.get(f"{prefix}_g"))
            cb_ = int(self.config.get(f"{prefix}_b"))
            result = colorchooser.askcolor(color=(cr, cg, cb_), title=label)
            if not result or not result[0]:
                return
            nr, ng, nb = (int(x) for x in result[0])
            self.config.update(
                immediate_save=True,
                **{f"{prefix}_r": nr, f"{prefix}_g": ng, f"{prefix}_b": nb},
            )
            preview.configure(bg=f"#{nr:02x}{ng:02x}{nb:02x}")

        def sync_preview(*_a) -> None:
            try:
                pr = int(self.config.get(f"{prefix}_r"))
                pg = int(self.config.get(f"{prefix}_g"))
                pb = int(self.config.get(f"{prefix}_b"))
                preview.configure(bg=f"#{pr:02x}{pg:02x}{pb:02x}")
            except Exception:
                pass

        self._vars[f"__preview_{prefix}"] = tk.StringVar()  # placeholder marker
        btn = ttk.Button(row, text="Выбрать цвет", style="Ghost.TButton", command=pick)
        btn.pack(side="left")
        # store preview widget for sync
        setattr(self, f"_preview_{prefix}", preview)

    def _sound_choices(self) -> list[str]:
        return [assets.NONE_LABEL] + assets.list_sound_files()

    def _weapon_img_choices(self) -> list[str]:
        return [assets.NONE_LABEL] + assets.list_weapon_images()

    def _glove_img_choices(self) -> list[str]:
        return [assets.NONE_LABEL] + assets.list_glove_images()

    def _refresh_asset_lists(self) -> None:
        mapping = {
            "shot_sound": self._sound_choices(),
            "shell_sound": self._sound_choices(),
            "custom_weapon": self._weapon_img_choices(),
            "custom_gloves": self._glove_img_choices(),
        }
        for key, values in mapping.items():
            cb = self._combos.get(key)
            if cb is None:
                continue
            cb.configure(values=values)
            var = self._vars.get(key)
            if var is None:
                continue
            cur = var.get()
            if cur not in values:
                cb.configure(values=list(values) + ([cur] if cur else []))

    def _import_weapon_png(self) -> None:
        path = filedialog.askopenfilename(
            title="PNG оружия (ствол вправо)",
            filetypes=[("PNG", "*.png"), ("WebP", "*.webp"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            name = assets.import_image(path, "weapon")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.config.update(immediate_save=True, custom_weapon=name, use_custom_weapon=True)
        self._refresh_asset_lists()
        if "custom_weapon" in self._vars:
            self._vars["custom_weapon"].set(name)
        if "use_custom_weapon" in self._vars:
            self._vars["use_custom_weapon"].set(True)

    def _import_gloves_png(self) -> None:
        path = filedialog.askopenfilename(
            title="PNG перчаток",
            filetypes=[("PNG", "*.png"), ("WebP", "*.webp"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            name = assets.import_image(path, "gloves")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.config.update(immediate_save=True, custom_gloves=name, use_custom_gloves=True)
        self._refresh_asset_lists()
        if "custom_gloves" in self._vars:
            self._vars["custom_gloves"].set(name)
        if "use_custom_gloves" in self._vars:
            self._vars["use_custom_gloves"].set(True)

    def _import_sound(self, target_key: str) -> None:
        path = filedialog.askopenfilename(
            title="Звуковой файл",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            name = assets.import_sound(path)
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.config.update(immediate_save=True, **{target_key: name})
        self._refresh_asset_lists()
        if target_key in self._vars:
            self._vars[target_key].set(name)

    def _build(self) -> None:
        assert self.root is not None
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=BG)
        header.pack(fill="x", padx=18, pady=(16, 4))
        tk.Label(header, text="CorporateDroneAIM", bg=BG, fg=TEXT, font=("Segoe UI Semibold", 18)).pack(
            anchor="w"
        )
        tk.Label(
            header,
            text="Настройки оверлея · F1 показать · Esc выход",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        container = tk.Frame(shell, bg=BG)
        container.pack(fill="both", expand=True, padx=10, pady=6)
        canvas = tk.Canvas(container, bg=BG, highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        pad = tk.Frame(canvas, bg=BG)
        pad.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=pad, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def _wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _wheel)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))

        # Model
        c = self._card(pad, "МОДЕЛЬ")
        self._add_combo(c, "weapon", "Оружие", list(WEAPONS))
        self._add_combo(c, "hands", "Руки", list(HANDS))

        # Custom
        c = self._card(pad, "КАСТОМНЫЕ PNG")
        tk.Label(
            c,
            text="Оружие: ствол вправо, рукоять слева · PNG с альфой",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))
        self._add_check(c, "use_custom_weapon", "Кастомное оружие")
        self._add_combo(c, "custom_weapon", "Файл оружия", self._weapon_img_choices(), allow_empty=True)
        self._add_scale(c, "custom_weapon_scale", "Масштаб оружия", 0.2, 3.0, "{:.2f}")
        ttk.Button(c, text="Добавить PNG оружия", style="Ghost.TButton", command=self._import_weapon_png).pack(
            anchor="w", pady=4
        )
        tk.Frame(c, bg=CARD_BORDER, height=1).pack(fill="x", pady=10)
        self._add_check(c, "use_custom_gloves", "Кастомные перчатки")
        self._add_combo(c, "custom_gloves", "Файл перчаток", self._glove_img_choices(), allow_empty=True)
        self._add_scale(c, "custom_gloves_scale", "Масштаб перчаток", 0.2, 3.0, "{:.2f}")
        ttk.Button(c, text="Добавить PNG перчаток", style="Ghost.TButton", command=self._import_gloves_png).pack(
            anchor="w", pady=4
        )

        # Transform
        c = self._card(pad, "ТРАНСФОРМ")
        self._add_scale(c, "scale", "Размер", 0.4, 2.5, "{:.2f}")
        self._add_scale(c, "offset_x", "Смещение X", -400, 400, "{:.0f}")
        self._add_scale(c, "offset_y", "Смещение Y", -400, 200, "{:.0f}")
        self._add_scale(c, "opacity", "Прозрачность окна", 0.15, 1.0, "{:.2f}")
        self._add_scale(c, "fire_rate_ms", "Темп огня (мс)", 40, 600, "{:.0f}")

        # Effects
        c = self._card(pad, "ЭФФЕКТЫ")
        self._add_check(c, "muzzle_flash", "Вспышка дула")
        self._add_check(c, "tracer", "Трассер")
        self._add_check(c, "impact", "Попадание")
        self._add_check(c, "recoil", "Отдача")
        self._add_check(c, "shell_eject", "Гильзы")
        self._add_check(c, "always_on_top", "Поверх всех окон")

        # Crosshair
        c = self._card(pad, "ПРИЦЕЛ")
        self._add_check(c, "crosshair", "Показывать прицел")
        self._add_combo(c, "crosshair_style", "Стиль", list(CROSSHAIR_STYLES))
        self._add_scale(c, "crosshair_size", "Размер", 4, 48, "{:.0f}")
        self._add_scale(c, "crosshair_thickness", "Толщина", 1, 8, "{:.0f}")
        self._add_scale(c, "crosshair_gap", "Зазор", 0, 24, "{:.0f}")
        self._add_scale(c, "crosshair_opacity", "Прозрачность", 0.1, 1.0, "{:.2f}")
        self._color_row(c, "crosshair", "Цвет")

        # Tracer look
        c = self._card(pad, "ТРАССЕР")
        self._add_combo(c, "tracer_style", "Стиль", list(TRACER_STYLES))
        self._add_scale(c, "tracer_width", "Толщина", 0.5, 12, "{:.1f}")
        self._add_scale(c, "tracer_duration", "Длительность", 0.02, 0.4, "{:.2f}")
        self._add_scale(c, "tracer_opacity", "Яркость", 0.1, 1.0, "{:.2f}")
        self._color_row(c, "tracer", "Цвет")

        # Sound
        c = self._card(pad, "ЗВУК")
        self._add_check(c, "sound", "Включить звук")
        self._add_combo(c, "shot_sound", "Выстрел", self._sound_choices(), allow_empty=True)
        self._add_combo(c, "shell_sound", "Гильза", self._sound_choices(), allow_empty=True)
        self._add_scale(c, "shot_volume", "Громкость выстрела", 0.0, 1.0, "{:.2f}")
        self._add_scale(c, "shell_volume", "Громкость гильзы", 0.0, 1.0, "{:.2f}")
        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x", pady=4)
        ttk.Button(
            row, text="Добавить звук выстрела", style="Ghost.TButton", command=lambda: self._import_sound("shot_sound")
        ).pack(side="left")
        ttk.Button(
            row, text="Добавить звук гильзы", style="Ghost.TButton", command=lambda: self._import_sound("shell_sound")
        ).pack(side="left", padx=6)

        # Help overlay
        c = self._card(pad, "ПОДСКАЗКИ НА ЭКРАНЕ")
        self._add_check(c, "show_controls", "Показывать управление (H)")
        self._add_scale(c, "controls_opacity", "Плотность панели", 0.2, 1.0, "{:.2f}")

        # Footer buttons
        foot = tk.Frame(pad, bg=BG)
        foot.pack(fill="x", pady=16, padx=4)

        def reset() -> None:
            self.config.update(immediate_save=True, **DEFAULTS)
            self._refresh_asset_lists()
            self._sync_from_config(self.config.as_dict())

        ttk.Button(foot, text="Сбросить", style="Ghost.TButton", command=reset).pack(side="left")
        ttk.Button(foot, text="Скрыть", style="Ghost.TButton", command=self._hide).pack(side="left", padx=8)
        ttk.Button(foot, text="Выход", style="Danger.TButton", command=self._quit).pack(side="right")

    def _quit(self) -> None:
        if self.on_quit:
            self.on_quit()
        self.close()

    def _on_config_changed(self, data: dict) -> None:
        root = self.root
        if root is None or self._closed.is_set():
            return

        def _sync() -> None:
            self._sync_from_config(data)

        try:
            root.after(0, _sync)
        except tk.TclError:
            pass

    def _sync_from_config(self, data: dict) -> None:
        root = self.root
        if root is None:
            return
        try:
            if not root.winfo_exists():
                return
        except tk.TclError:
            return

        self._building = True
        try:
            for key, var in self._vars.items():
                if key.startswith("__"):
                    continue
                if key not in data:
                    continue
                val = data[key]
                try:
                    if isinstance(var, tk.BooleanVar):
                        new_v = bool(val)
                    elif isinstance(var, tk.DoubleVar):
                        new_v = float(val)
                    else:
                        new_v = val
                        if key in ("shot_sound", "shell_sound", "custom_weapon", "custom_gloves"):
                            if not new_v:
                                new_v = assets.NONE_LABEL
                    if var.get() != new_v:
                        var.set(new_v)
                except tk.TclError:
                    pass
            for prefix in ("crosshair", "tracer"):
                preview = getattr(self, f"_preview_{prefix}", None)
                if preview is not None:
                    r = int(data.get(f"{prefix}_r", 255))
                    g = int(data.get(f"{prefix}_g", 255))
                    b = int(data.get(f"{prefix}_b", 255))
                    preview.configure(bg=f"#{r:02x}{g:02x}{b:02x}")
        finally:
            self._building = False
