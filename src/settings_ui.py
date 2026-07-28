from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from . import assets
from .config import DEFAULTS, HANDS, WEAPONS, Config


class SettingsWindow:
    """Tk settings UI. Must live on its own thread with mainloop()."""

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
        self.root.title("CorporateDroneAIM — Settings")
        self.root.geometry("460x720")
        self.root.minsize(400, 520)
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

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

    def _add_scale(
        self,
        parent: ttk.Frame,
        key: str,
        label: str,
        from_: float,
        to: float,
        fmt: str,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=18).pack(side="left")
        var = tk.DoubleVar(value=float(self.config.get(key)))
        self._vars[key] = var
        val_lbl = ttk.Label(row, width=8)

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
        scale.pack(side="left", fill="x", expand=True, padx=6)
        scale.bind("<ButtonRelease-1>", on_release)
        val_lbl.pack(side="left")
        val_lbl.configure(text=fmt.format(float(var.get())))

    def _add_check(self, parent: ttk.Frame, key: str, label: str) -> None:
        var = tk.BooleanVar(value=bool(self.config.get(key)))
        self._vars[key] = var

        def on_toggle() -> None:
            if not self._building:
                self.config.update(immediate_save=True, **{key: bool(var.get())})

        ttk.Checkbutton(parent, text=label, variable=var, command=on_toggle).pack(anchor="w", pady=2)

    def _add_combo(
        self,
        parent: ttk.Frame,
        key: str,
        label: str,
        values: list[str],
        *,
        allow_empty: bool = False,
    ) -> ttk.Combobox:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=label, width=18).pack(side="left")
        cur = str(self.config.get(key) or "")
        if allow_empty and not cur:
            cur = assets.NONE_LABEL
        if cur and cur not in values and cur != assets.NONE_LABEL:
            values = list(values) + [cur]
        var = tk.StringVar(value=cur)
        self._vars[key] = var
        cb = ttk.Combobox(row, textvariable=var, values=values, state="readonly")
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
                # keep showing stored name if missing file
                cb.configure(values=list(values) + ([cur] if cur else []))

    def _import_weapon_png(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите PNG оружия (ствол вправо, прозрачный фон)",
            filetypes=[("PNG images", "*.png"), ("WebP", "*.webp"), ("All", "*.*")],
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
        messagebox.showinfo(
            "Готово",
            f"Оружие добавлено: {name}\n\nРекомендация: ствол смотрит вправо, рукоять слева снизу, PNG с альфой.",
        )

    def _import_gloves_png(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите PNG перчаток (прозрачный фон)",
            filetypes=[("PNG images", "*.png"), ("WebP", "*.webp"), ("All", "*.*")],
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
        messagebox.showinfo("Готово", f"Перчатки добавлены: {name}")

    def _import_sound(self, target_key: str) -> None:
        path = filedialog.askopenfilename(
            title="Выберите звуковой файл",
            filetypes=[
                ("Audio", "*.mp3 *.wav *.ogg"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("All", "*.*"),
            ],
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

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        pad = ttk.Frame(canvas, padding=14)

        pad.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=pad, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _resize_inner(event):
            canvas.itemconfigure(canvas.find_all()[0], width=event.width)

        canvas.bind("<Configure>", _resize_inner)

        ttk.Label(pad, text="FPV Weapon Overlay", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(
            pad,
            text="ЛКМ — выстрел · F1 — настройки · F2 — оружие · Esc — выход",
            justify="left",
        ).pack(anchor="w", pady=(4, 12))

        # Model
        box = ttk.LabelFrame(pad, text="Модель (процедурная)", padding=10)
        box.pack(fill="x", pady=6)
        self._add_combo(box, "weapon", "Оружие", list(WEAPONS))
        self._add_combo(box, "hands", "Руки", list(HANDS))

        # Custom sprites
        cbox = ttk.LabelFrame(pad, text="Кастомные PNG", padding=10)
        cbox.pack(fill="x", pady=6)
        ttk.Label(
            cbox,
            text="Оружие: ствол вправо, рукоять слева. PNG с прозрачностью.",
            wraplength=400,
        ).pack(anchor="w", pady=(0, 6))

        self._add_check(cbox, "use_custom_weapon", "Использовать кастомное оружие")
        self._add_combo(cbox, "custom_weapon", "Файл оружия", self._weapon_img_choices(), allow_empty=True)
        self._add_scale(cbox, "custom_weapon_scale", "Масштаб оружия", 0.2, 3.0, "{:.2f}")
        wbtn = ttk.Frame(cbox)
        wbtn.pack(fill="x", pady=4)
        ttk.Button(wbtn, text="Добавить PNG оружия…", command=self._import_weapon_png).pack(side="left")

        ttk.Separator(cbox, orient="horizontal").pack(fill="x", pady=8)
        self._add_check(cbox, "use_custom_gloves", "Использовать кастомные перчатки")
        self._add_combo(cbox, "custom_gloves", "Файл перчаток", self._glove_img_choices(), allow_empty=True)
        self._add_scale(cbox, "custom_gloves_scale", "Масштаб перчаток", 0.2, 3.0, "{:.2f}")
        gbtn = ttk.Frame(cbox)
        gbtn.pack(fill="x", pady=4)
        ttk.Button(gbtn, text="Добавить PNG перчаток…", command=self._import_gloves_png).pack(side="left")

        # Transform
        tbox = ttk.LabelFrame(pad, text="Размер / положение / прозрачность", padding=10)
        tbox.pack(fill="x", pady=6)
        self._add_scale(tbox, "scale", "Размер", 0.4, 2.5, "{:.2f}")
        self._add_scale(tbox, "offset_x", "Смещение X", -400, 400, "{:.0f}")
        self._add_scale(tbox, "offset_y", "Смещение Y", -400, 200, "{:.0f}")
        self._add_scale(tbox, "opacity", "Прозрачность", 0.15, 1.0, "{:.2f}")
        self._add_scale(tbox, "fire_rate_ms", "Темп (мс)", 40, 600, "{:.0f}")

        # Effects
        ebox = ttk.LabelFrame(pad, text="Эффекты стрельбы", padding=10)
        ebox.pack(fill="x", pady=6)
        self._add_check(ebox, "muzzle_flash", "Вспышка дула")
        self._add_check(ebox, "tracer", "Трассер к курсору")
        self._add_check(ebox, "impact", "Попадание в точку курсора")
        self._add_check(ebox, "recoil", "Отдача")
        self._add_check(ebox, "shell_eject", "Гильзы")
        self._add_check(ebox, "always_on_top", "Поверх всех окон")

        # Sound
        sbox = ttk.LabelFrame(pad, text="Звуки", padding=10)
        sbox.pack(fill="x", pady=6)
        self._add_check(sbox, "sound", "Включить звук")
        self._add_combo(sbox, "shot_sound", "Выстрел", self._sound_choices(), allow_empty=True)
        self._add_combo(sbox, "shell_sound", "Падение гильзы", self._sound_choices(), allow_empty=True)
        self._add_scale(sbox, "shot_volume", "Громкость выстрела", 0.0, 1.0, "{:.2f}")
        self._add_scale(sbox, "shell_volume", "Громкость гильзы", 0.0, 1.0, "{:.2f}")
        sbtns = ttk.Frame(sbox)
        sbtns.pack(fill="x", pady=4)
        ttk.Button(sbtns, text="Добавить звук выстрела…", command=lambda: self._import_sound("shot_sound")).pack(
            side="left"
        )
        ttk.Button(sbtns, text="Добавить звук гильзы…", command=lambda: self._import_sound("shell_sound")).pack(
            side="left", padx=6
        )
        ttk.Label(
            sbox,
            text="Файлы из папки sounds/. Можно кидать mp3/wav вручную.",
            wraplength=400,
        ).pack(anchor="w", pady=(4, 0))

        btns = ttk.Frame(pad)
        btns.pack(fill="x", pady=16)

        def reset() -> None:
            self.config.update(immediate_save=True, **DEFAULTS)
            self._refresh_asset_lists()

        ttk.Button(btns, text="Сбросить", command=reset).pack(side="left")
        ttk.Button(btns, text="Скрыть", command=self._hide).pack(side="left", padx=8)
        ttk.Button(btns, text="Выход", command=self._quit).pack(side="right")

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
        finally:
            self._building = False
