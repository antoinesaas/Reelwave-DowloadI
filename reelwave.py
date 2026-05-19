"""ReelWave — entry point with dependency check screen."""
from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path


# ── Dependency check ──────────────────────────────────────────────────────
def _has_module(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


def _show_install_screen(missing: list[str]) -> None:
    """Minimal install helper shown when yt-dlp / customtkinter is absent."""
    root = tk.Tk()
    root.title("ReelWave — Installation requise")
    root.geometry("500x320")
    root.configure(bg="#FFFFFF")
    root.resizable(False, False)

    tk.Label(
        root, text="Dépendances manquantes",
        font=("Segoe UI", 16, "bold"),
        bg="#FFFFFF", fg="#1D1D1F",
    ).pack(pady=(32, 8))

    tk.Label(
        root,
        text="Les paquets suivants sont requis pour faire fonctionner ReelWave :",
        font=("Segoe UI", 12),
        bg="#FFFFFF", fg="#6E6E73",
        wraplength=440,
    ).pack(pady=(0, 12))

    for pkg in missing:
        tk.Label(
            root, text=f"  pip install {pkg}",
            font=("Consolas", 12),
            bg="#F5F5F7", fg="#1D1D1F",
            padx=16, pady=6, anchor="w",
        ).pack(fill="x", padx=40, pady=2)

    status_lbl = tk.Label(
        root, text="",
        font=("Segoe UI", 11),
        bg="#FFFFFF", fg="#6E6E73",
    )
    status_lbl.pack(pady=(12, 0))

    def install():
        btn.configure(state="disabled", text="Installation…")
        status_lbl.configure(text="Installation en cours, veuillez patienter…")
        root.update()

        for pkg in missing:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True,
            )

        status_lbl.configure(
            text="✓ Installation terminée — relancez ReelWave.",
            fg="#34C759",
        )
        btn.configure(text="Fermer", state="normal", command=root.destroy)

    btn = tk.Button(
        root, text="Installer maintenant",
        font=("Segoe UI", 13, "bold"),
        bg="#1D1D1F", fg="white",
        activebackground="#3A3A3C",
        activeforeground="white",
        relief="flat", bd=0,
        padx=24, pady=12,
        cursor="hand2",
        command=install,
    )
    btn.pack(pady=(16, 0))

    root.mainloop()
    sys.exit(0)


def main() -> None:
    # Check critical dependencies
    missing = []
    if not _has_module("yt_dlp"):
        missing.append("yt-dlp")
    if not _has_module("customtkinter") and not _has_module("tkinter"):
        missing.append("customtkinter")

    if missing:
        _show_install_screen(missing)
        return

    # All good — launch app
    from ui.app import ReelWaveApp
    app = ReelWaveApp()

    # Set window icon (generate from canvas if possible)
    _set_icon(app)

    app.mainloop()


def _set_icon(root: tk.Tk) -> None:
    """Generate a .ico in the data folder and set it as taskbar icon."""
    try:
        ico_path = Path(__file__).parent / "data" / "icon.ico"
        if not ico_path.exists():
            _generate_ico(ico_path)
        if ico_path.exists():
            root.iconbitmap(str(ico_path))
    except Exception:
        pass


def _generate_ico(path: Path) -> None:
    """Draw the RW logo at 48x48 and save as .ico using Pillow."""
    try:
        from PIL import Image, ImageDraw
        size = 48
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded square background
        r = int(size * 0.22)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=(29, 29, 31, 255))

        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(path), format="ICO", sizes=[(48, 48), (32, 32), (16, 16)])
    except Exception:
        pass


if __name__ == "__main__":
    main()
