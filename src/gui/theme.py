"""Dark theme — black/white base with warm gold accent."""

import flet as ft

# ── Background & surfaces ────────────────────────────────────
BG = "#09090b"
SURFACE = "#111113"
SURFACE_ELEVATED = "#18181b"
SURFACE_BRIGHT = "#27272a"
BORDER = "#3f3f46"

# ── Text ─────────────────────────────────────────────────────
TEXT = "#fafafa"
TEXT_MUTED = "#a1a1aa"
TEXT_DIM = "#71717a"

# ── Gold accent ──────────────────────────────────────────────
GOLD = "#d4a843"
GOLD_DIM = "#a68832"
ON_GOLD = "#0c0a04"

# ── Semantic action colors ───────────────────────────────────
GREEN = "#4ade80"
GREEN_DIM = "#166534"
RED = "#f87171"
RED_DIM = "#7f1d1d"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"

# ── Aliases ──────────────────────────────────────────────────
ON_SURFACE = TEXT
ON_SURFACE_DIM = TEXT_MUTED
ACCENT = GOLD

APP_THEME = ft.Theme(
    color_scheme_seed="#d4a843",
    color_scheme=ft.ColorScheme(
        primary=GOLD,
        on_primary=ON_GOLD,
        primary_container=SURFACE_ELEVATED,
        on_primary_container=TEXT,
        secondary=SURFACE_BRIGHT,
        on_secondary=TEXT,
        surface=SURFACE,
        on_surface=TEXT,
        surface_container_highest=SURFACE_ELEVATED,
        outline=BORDER,
        error=RED,
        on_error="#fff",
    ),
)
