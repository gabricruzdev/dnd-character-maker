"""
GUI Flet — D&D 5e Character Maker
4 views: Setup, Preferences, Loading, Result
"""

from __future__ import annotations

import json
import random
import threading
import unicodedata
from pathlib import Path

import flet as ft

from config import get_active_key, load_config, save_config
from src.ai.llm import LLMClient
from src.ai.prompts import SYSTEM_PROMPT, build_correction_prompt, build_generation_prompt
from src.ai.schema import CHARACTER_SCHEMA
from src.engine.character import Character
from src.export.pdf_export import export_pdf
from src.gui.native_dialogs import pick_json_file, save_json_file, save_pdf_file
from src.gui.theme import (
    BG, BLUE, BORDER, GOLD, GOLD_DIM, GREEN, GREEN_DIM,
    ON_GOLD, ON_SURFACE, RED,
    SURFACE, SURFACE_BRIGHT, SURFACE_ELEVATED, TEXT_DIM,
    APP_THEME,
)
from src.validator.checker import validate

_ROOT = Path(__file__).resolve().parent.parent.parent
HISTORY_FILE = _ROOT / "history.json"
FICHAS_DIR = _ROOT / "fichas"
FICHAS_DIR.mkdir(exist_ok=True)

LOADING_MSGS = [
    "Rolling the dice of fate...",
    "Consulting ancient tomes...",
    "Forging the hero's soul...",
    "Rolling attributes with 4d6...",
    "Choosing skills and equipment...",
    "Writing the backstory...",
    "Checking D&D rules...",
    "Almost done, just one more spell...",
    "Invoking ancestral powers...",
    "Preparing the final sheet...",
]

SUBCLASS_LEVELS = {
    "barbarian": 3, "bard": 3, "cleric": 1, "druid": 2,
    "fighter": 3, "monk": 3, "paladin": 3, "ranger": 3,
    "rogue": 3, "sorcerer": 1, "warlock": 1, "wizard": 2,
}

_PT_CLASS_TO_EN = {
    "barbaro": "barbarian", "bardo": "bard", "bruxo": "warlock",
    "clerigo": "cleric", "druida": "druid", "guerreiro": "fighter",
    "ladino": "rogue", "mago": "wizard", "monge": "monk",
    "paladino": "paladin", "patrulheiro": "ranger", "feiticeiro": "sorcerer",
}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _subclass_pick_level(class_name: str) -> int:
    raw = (class_name or "").strip().lower()
    if not raw:
        return 3
    key = _strip_accents(raw)
    if key in SUBCLASS_LEVELS:
        return SUBCLASS_LEVELS[key]
    if key in _PT_CLASS_TO_EN:
        return SUBCLASS_LEVELS.get(_PT_CLASS_TO_EN[key], 3)
    for en in SUBCLASS_LEVELS:
        if en in key:
            return SUBCLASS_LEVELS[en]
    for pt, en in _PT_CLASS_TO_EN.items():
        if pt in key:
            return SUBCLASS_LEVELS.get(en, 3)
    return 3


def _load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_history(history: list[dict]):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-20:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _card(content: ft.Control, *, pad: int = 24) -> ft.Container:
    return ft.Container(
        border_radius=14,
        border=ft.Border.all(1, BORDER),
        bgcolor=SURFACE_ELEVATED,
        padding=pad,
        content=content,
    )


def _pill(label: str, value: str, color: str = ON_SURFACE) -> ft.Container:
    return ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=10, vertical=10),
        border_radius=12,
        bgcolor=SURFACE_BRIGHT,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1,
            controls=[
                ft.Text(label, size=10, color=ON_SURFACE, weight=ft.FontWeight.W_500),
                ft.Text(value, size=17, weight=ft.FontWeight.BOLD, color=color),
            ],
        ),
    )


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    ft.app(target=_app)


def _app(page: ft.Page):
    page.title = "D&D 5e Character Maker"
    page.theme = APP_THEME
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.window.width = 1100
    page.window.height = 820
    page.window.min_width = 900
    page.window.min_height = 680
    page.padding = 0

    state = AppState(page)
    state.show_initial_view()


class AppState:

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_char: Character | None = None
        self.current_raw: dict = {}
        self.history: list[dict] = _load_history()
        self.slot_states: dict[str, list[bool]] = {}

    def _navigate(self, view: ft.Control):
        self.page.controls.clear()
        self.page.controls.append(view)
        self.page.update()

    def show_initial_view(self):
        cfg = load_config()
        _, key = get_active_key(cfg)
        if key:
            self._show_prefs()
        else:
            self._show_setup()

    def _snack(self, msg: str, color: str = SURFACE_BRIGHT):
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(msg, color="#fff", size=13),
                bgcolor=color,
                duration=ft.Duration(milliseconds=3000),
            )
        )

    def _snack_ok(self, msg: str):
        self._snack(msg, GREEN_DIM)

    def _snack_err(self, msg: str):
        self._snack(msg, RED)

    # ══════════════════════════════════════════════════════════
    #  VIEW 1 — SETUP
    # ══════════════════════════════════════════════════════════

    def _show_setup(self):
        cfg = load_config()
        provider_group = ft.RadioGroup(
            value=cfg.get("provider", "gemini"),
            content=ft.Row([
                ft.Radio(value="gemini", label="Google Gemini (recommended)"),
                ft.Radio(value="groq", label="Groq"),
            ], spacing=24),
        )
        gemini_field = ft.TextField(
            label="Gemini API Key", value=cfg.get("gemini_api_key", ""),
            password=True, can_reveal_password=True,
            border_radius=10, filled=True,
            prefix_icon=ft.Icons.KEY, expand=True,
        )
        groq_field = ft.TextField(
            label="Groq API Key", value=cfg.get("groq_api_key", ""),
            password=True, can_reveal_password=True,
            border_radius=10, filled=True,
            prefix_icon=ft.Icons.KEY, expand=True,
        )

        def on_save(e):
            p = provider_group.value
            gk = gemini_field.value.strip()
            rk = groq_field.value.strip()
            if p == "gemini" and not gk:
                self._snack_err("Enter your Gemini key!")
                return
            if p == "groq" and not rk:
                self._snack_err("Enter your Groq key!")
                return
            save_config(gk, rk, p)
            self._show_prefs()

        form_col = ft.Column(spacing=18, controls=[
            ft.Text("AI Provider", size=15,
                    weight=ft.FontWeight.W_600, color=ON_SURFACE),
            provider_group,
            ft.Row([gemini_field], expand=True),
            ft.Row([groq_field], expand=True),
            ft.Text(
                "Both are free. Get yours at "
                "aistudio.google.com or console.groq.com",
                size=11, color=TEXT_DIM,
                text_align=ft.TextAlign.CENTER),
        ])

        inner = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=28,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=GOLD, size=44),
                        ft.Container(height=4),
                        ft.Text("D&D 5e",
                                size=40, weight=ft.FontWeight.BOLD,
                                color=GOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text("Character Maker",
                                size=18, weight=ft.FontWeight.W_300,
                                color=ON_SURFACE,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=2),
                        ft.Text("made by gabrielcruzdev",
                                size=11, italic=True, color=TEXT_DIM),
                    ],
                ),
                ft.Divider(height=1, color=BORDER),
                form_col,
                ft.Container(height=4),
                ft.FilledButton(
                    "Save and Continue",
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=on_save,
                    width=340, height=48,
                    style=ft.ButtonStyle(bgcolor=GOLD, color=ON_GOLD),
                ),
            ],
        )

        center_card = ft.Container(
            width=680,
            border_radius=18,
            border=ft.Border.all(1, BORDER),
            bgcolor=SURFACE_ELEVATED,
            padding=ft.padding.symmetric(horizontal=56, vertical=44),
            content=inner,
        )

        view = ft.Column(
            expand=True, spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(expand=True),
                center_card,
                ft.Container(expand=True),
            ],
        )
        self._navigate(view)

    # ══════════════════════════════════════════════════════════
    #  VIEW 2 — PREFERENCES
    # ══════════════════════════════════════════════════════════

    def _show_prefs(self):
        level_text = ft.Text("1", size=30, weight=ft.FontWeight.BOLD, color=GOLD)
        level_slider = ft.Slider(
            min=1, max=20, divisions=19, value=1, label="{value}",
            active_color=GOLD, thumb_color=GOLD, expand=True,
        )

        def on_level(e):
            level_text.value = str(int(level_slider.value))
            self.page.update()

        level_slider.on_change = on_level

        tone_group = ft.RadioGroup(value="neutral", content=ft.Row([
            ft.Radio(value="comic", label="Comic"),
            ft.Radio(value="serious", label="Serious"),
            ft.Radio(value="neutral", label="Neutral"),
        ], spacing=20))
        focus_group = ft.RadioGroup(value="balanced", content=ft.Row([
            ft.Radio(value="power", label="Power"),
            ft.Radio(value="utility", label="Utility"),
            ft.Radio(value="balanced", label="Balanced"),
        ], spacing=20))

        race_field = ft.TextField(
            label="Race (optional)", hint_text="Ex: Tiefling, High Elf...",
            border_radius=10, filled=True, expand=True,
            prefix_icon=ft.Icons.GROUPS)
        class_field = ft.TextField(
            label="Class (optional)", hint_text="Ex: Wizard, Paladin...",
            border_radius=10, filled=True, expand=True,
            prefix_icon=ft.Icons.SHIELD)
        bg_field = ft.TextField(
            label="Background (optional)", hint_text="Ex: Sage, Criminal...",
            border_radius=10, filled=True, expand=True,
            prefix_icon=ft.Icons.MENU_BOOK)
        extra_field = ft.TextField(
            label="Extra details",
            hint_text="Ex: 'blind character', 'grumpy old man', 'afraid of fire'...",
            multiline=True, min_lines=5, max_lines=12,
            border_radius=10, filled=True, expand=True)

        def randomize(e):
            level_slider.value = random.randint(1, 20)
            level_text.value = str(int(level_slider.value))
            tone_group.value = random.choice(["comic", "serious", "neutral"])
            focus_group.value = random.choice(["power", "utility", "balanced"])
            for f in (race_field, class_field, bg_field, extra_field):
                f.value = ""
            self.page.update()

        def generate(e):
            self._on_generate(
                level=int(level_slider.value),
                tone=tone_group.value,
                focus=focus_group.value,
                race=race_field.value.strip(),
                cls=class_field.value.strip(),
                bg=bg_field.value.strip(),
                extra=extra_field.value.strip(),
            )

        def load_char(e):
            path = pick_json_file(FICHAS_DIR)
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.current_raw = data
                char = Character.from_dict(data)
                self._show_result(char)
                self._snack_ok(f"Sheet loaded: {char.name}")
            except Exception as ex:
                self._snack_err(f"Error loading: {ex}")

        hist_count = len(self.history)
        hist_label = f"History ({hist_count})" if hist_count else "History"

        header = ft.Container(
            bgcolor=SURFACE,
            border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
            padding=ft.padding.symmetric(horizontal=32, vertical=14),
            content=ft.Row([
                ft.TextButton(
                    "Settings", icon=ft.Icons.SETTINGS,
                    on_click=lambda e: self._show_setup(),
                    style=ft.ButtonStyle(color=ON_SURFACE)),
                ft.Text("Create your Character", size=20,
                        weight=ft.FontWeight.BOLD, color=GOLD,
                        expand=True, text_align=ft.TextAlign.CENTER),
                ft.TextButton(
                    hist_label, icon=ft.Icons.HISTORY,
                    on_click=lambda e: self._show_history(),
                    style=ft.ButtonStyle(color=ON_SURFACE)),
            ]),
        )

        build_card = _card(ft.Column(spacing=14, controls=[
            ft.Text("Character Essence",
                    size=17, weight=ft.FontWeight.W_600, color=GOLD),
            ft.Row([
                ft.Text("Level", size=14, width=50), level_slider, level_text,
            ]),
            ft.Row([ft.Text("Tone", size=14, width=50), tone_group]),
            ft.Row([ft.Text("Focus", size=14, width=50), focus_group]),
        ]))

        constraints_card = _card(ft.Column(spacing=14, controls=[
            ft.Text("Optional Constraints",
                    size=17, weight=ft.FontWeight.W_600, color=ON_SURFACE),
            ft.Row([race_field, class_field], spacing=12),
            ft.Row([bg_field], expand=True),
            ft.Row([extra_field], expand=True),
        ]))

        action_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER, spacing=14,
            controls=[
                ft.OutlinedButton(
                    "Load Sheet", icon=ft.Icons.FOLDER_OPEN,
                    on_click=load_char,
                    style=ft.ButtonStyle(color=ON_SURFACE)),
                ft.OutlinedButton(
                    "Full Random", icon=ft.Icons.CASINO,
                    on_click=randomize,
                    style=ft.ButtonStyle(color=ON_SURFACE)),
                ft.FilledButton(
                    "Generate Character", icon=ft.Icons.AUTO_AWESOME,
                    on_click=generate,
                    style=ft.ButtonStyle(bgcolor=GOLD, color=ON_GOLD)),
            ],
        )

        body = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=40),
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO, expand=True, spacing=20,
                controls=[
                    ft.Container(height=12),
                    build_card,
                    constraints_card,
                    action_row,
                    ft.Container(height=16),
                ],
            ),
        )

        view = ft.Column(spacing=0, expand=True, controls=[header, body])
        self._navigate(view)

    # ══════════════════════════════════════════════════════════
    #  VIEW 3 — LOADING
    # ══════════════════════════════════════════════════════════

    def _show_loading(self, title: str = "Generating your character..."):
        self._loading_active = True
        self._loading_msg_idx = 0

        dice_text = ft.Text("d20", size=56, weight=ft.FontWeight.BOLD, color=GOLD)
        title_text = ft.Text(title, size=20, weight=ft.FontWeight.W_600, color=ON_SURFACE)
        self._loading_status = ft.Text("Preparing...", size=13, color=ON_SURFACE)
        bar = ft.ProgressBar(width=360, color=GOLD, bgcolor=SURFACE_BRIGHT)

        self._loading_dice = dice_text
        self._loading_bar = bar

        def cancel(e):
            self._loading_active = False
            self._show_prefs()

        view = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            controls=[
                dice_text,
                ft.Container(height=14),
                title_text,
                ft.Container(height=10),
                self._loading_status,
                ft.Container(height=18),
                bar,
                ft.Container(height=28),
                ft.TextButton("Cancel", on_click=cancel,
                              style=ft.ButtonStyle(color=RED)),
            ],
        )
        self._navigate(view)
        self._animate_loading()

    def _animate_loading(self):
        import time

        def loop():
            while self._loading_active:
                faces = ["d4", "d6", "d8", "d10", "d12", "d20"]
                self._loading_dice.value = random.choice(faces)
                if self._loading_msg_idx < len(LOADING_MSGS):
                    self._loading_status.value = LOADING_MSGS[self._loading_msg_idx]
                    self._loading_msg_idx += 1
                try:
                    self.page.update()
                except Exception:
                    break
                time.sleep(2)

        threading.Thread(target=loop, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    #  VIEW 4 — RESULT
    # ══════════════════════════════════════════════════════════

    def _show_result(self, char: Character):
        self._loading_active = False
        self.current_char = char
        self.slot_states = {}

        ability_pt = {
            "strength": "STR", "dexterity": "DEX", "constitution": "CON",
            "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA",
        }
        ability_full_pt = {
            "strength": "Strength", "dexterity": "Dexterity", "constitution": "Constitution",
            "intelligence": "Intelligence", "wisdom": "Wisdom", "charisma": "Charisma",
        }

        # ── Stat cards ──
        _save_aliases = {
            "strength": ("strength", "str", "for", "forca", "força"),
            "dexterity": ("dexterity", "dex", "des", "destreza"),
            "constitution": ("constitution", "con", "constituicao", "constituição"),
            "intelligence": ("intelligence", "int", "inteligencia", "inteligência"),
            "wisdom": ("wisdom", "wis", "sab", "sabedoria"),
            "charisma": ("charisma", "cha", "car", "carisma"),
        }
        _save_prof_lower = [_strip_accents(s.lower()) for s in char.saving_throws]

        stat_cards = []
        for ab in ["strength", "dexterity", "constitution",
                    "intelligence", "wisdom", "charisma"]:
            score = char.ability_scores.get(ab, 10)
            mod = char.get_modifier_str(ab)
            save = char.get_save(ab)
            is_prof = any(
                _strip_accents(alias) in _save_prof_lower
                for alias in _save_aliases[ab]
            )
            stat_cards.append(
                ft.Container(
                    expand=True, padding=12, border_radius=12,
                    bgcolor=SURFACE_BRIGHT,
                    border=ft.Border.all(3 if is_prof else 1,
                                         GOLD if is_prof else BORDER),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(ability_pt[ab], size=10, color=GOLD,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(str(score), size=28,
                                    weight=ft.FontWeight.BOLD, color=ON_SURFACE),
                            ft.Text(f"({mod})", size=13, color=ON_SURFACE),
                            ft.Text(
                                f"Save: {'+' if save >= 0 else ''}{save}"
                                f"{'*' if is_prof else ''}",
                                size=9, color=ON_SURFACE),
                        ],
                    ),
                )
            )

        # ── Combat pills + HP tracker ──
        dex_mod = char.get_modifier("dexterity")
        init_str = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
        wis_mod = char.get_modifier("wisdom")
        passive_perc = 10 + wis_mod + (
            char.proficiency_bonus
            if any(s.lower() in ("perception", "percepcao", "percepção")
                   for s in char.skill_proficiencies)
            else 0
        )

        self._hp_current = char.hit_points
        self._hp_max = char.hit_points
        hp_display = ft.Text(
            f"{self._hp_current}/{self._hp_max}",
            size=17, weight=ft.FontWeight.BOLD, color=GREEN)

        def _hp_color() -> str:
            ratio = self._hp_current / max(self._hp_max, 1)
            if ratio > 0.5:
                return GREEN
            return GOLD if ratio > 0.25 else RED

        def hp_change(delta):
            def handler(e):
                self._hp_current = max(0, min(self._hp_max, self._hp_current + delta))
                hp_display.value = f"{self._hp_current}/{self._hp_max}"
                hp_display.color = _hp_color()
                self.page.update()
            return handler

        hp_tracker = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=4, vertical=6),
            border_radius=12,
            bgcolor=SURFACE_BRIGHT,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0,
                controls=[
                    ft.Text("HP", size=10, color=ON_SURFACE,
                            weight=ft.FontWeight.W_500),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER, spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                icon_size=18, icon_color=RED,
                                on_click=hp_change(-1),
                                tooltip="Damage (-1 HP)"),
                            hp_display,
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                icon_size=18, icon_color=GREEN,
                                on_click=hp_change(1),
                                tooltip="Heal (+1 HP)"),
                        ],
                    ),
                ],
            ),
        )

        combat_pills = ft.Row(
            spacing=10,
            controls=[
                hp_tracker,
                _pill("AC", str(char.armor_class), BLUE),
                _pill("Initiative", init_str, ON_SURFACE),
                _pill("Speed", f"{char.speed}ft"),
                _pill("Hit Die", char.hit_die),
                _pill("Prof.", f"+{char.proficiency_bonus}", GOLD),
                _pill("Pass. Perc.", str(passive_perc), BLUE),
            ],
        )

        # ── Skills ──
        skill_chips = [
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=20,
                bgcolor=SURFACE_BRIGHT,
                content=ft.Text(s, size=11, color=ON_SURFACE),
            ) for s in char.skill_proficiencies
        ] if char.skill_proficiencies else []

        # ── Proficiencies ──
        prof_items = []
        for label, vals in [
            ("Armor", char.armor_proficiencies),
            ("Weapons", char.weapon_proficiencies),
            ("Tools", char.tool_proficiencies),
            ("Languages", char.languages),
        ]:
            if vals:
                prof_items.append(
                    ft.Text(f"{label}: {', '.join(vals)}", size=12, color=ON_SURFACE))

        # ── Race traits ──
        race_tiles = []
        for i, t in enumerate(char.race_traits or []):
            if i > 0:
                race_tiles.append(ft.Divider(height=1, color=BORDER))
            race_tiles.append(ft.ExpansionTile(
                title=ft.Text(t.get("name", ""),
                              weight=ft.FontWeight.W_600, size=13),
                expanded=False,
                controls=[ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    content=ft.Text(t.get("description", ""),
                                    size=12, color=ON_SURFACE))],
            ))

        # ── Class features ──
        feat_tiles = []
        for i, f in enumerate(char.features or []):
            if i > 0:
                feat_tiles.append(ft.Divider(height=1, color=BORDER))
            src = f.get("source", "")
            feat_tiles.append(ft.ExpansionTile(
                title=ft.Text(
                    f"[Nv{f.get('level', '')}] {f.get('name', '')}",
                    weight=ft.FontWeight.W_600, size=13),
                subtitle=ft.Text(src, size=10, color=TEXT_DIM) if src else None,
                expanded=False,
                controls=[ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    content=ft.Text(f.get("description", ""),
                                    size=12, color=ON_SURFACE))],
            ))

        # ── Spellcasting stats row ──
        caster_stats_row = None
        if char.spellcasting_ability and (char.cantrips or char.spells):
            ab_score = char.ability_scores.get(char.spellcasting_ability, 10)
            ab_mod = (ab_score - 10) // 2
            spell_dc = 8 + char.proficiency_bonus + ab_mod
            spell_atk = char.proficiency_bonus + ab_mod
            atk_str = f"+{spell_atk}" if spell_atk >= 0 else str(spell_atk)
            caster_stats_row = ft.Row(spacing=10, controls=[
                _pill("Spell DC", str(spell_dc), GOLD),
                _pill("Spell Attack", atk_str, GOLD),
                _pill(
                    "Ability",
                    ability_full_pt.get(char.spellcasting_ability,
                                        char.spellcasting_ability.title()),
                    ON_SURFACE,
                ),
            ])

        # ── Spellcasting ──
        spell_section = self._build_spell_section(char, ability_full_pt)

        # ── Equipment ──
        equip_chips = [
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=20,
                bgcolor=SURFACE_BRIGHT,
                content=ft.Text(e, size=11, color=ON_SURFACE),
            ) for e in char.equipment
        ] if char.equipment else []

        # ── Assemble content ──
        content: list[ft.Control] = [
            _card(ft.Column(spacing=6, controls=[
                ft.Text(char.name, size=28, weight=ft.FontWeight.BOLD, color=GOLD),
                ft.Text(
                    f"Level {char.level}  ·  {char.race_display()}  ·  "
                    f"{char.class_display()}",
                    size=13, color=ON_SURFACE),
                ft.Text(
                    f"Background: {char.background}  |  "
                    f"Alignment: {char.alignment}",
                    size=12, color=ON_SURFACE),
            ])),
            ft.Container(height=8),
            ft.Row(stat_cards, spacing=8),
            ft.Container(height=6),
            combat_pills,
        ]

        if skill_chips:
            content.append(self._section("Skill Proficiencies"))
            content.append(ft.Row(skill_chips, wrap=True, spacing=6, run_spacing=6))

        if prof_items:
            content.append(self._section("Proficiencies"))
            content.append(_card(ft.Column(prof_items, spacing=6), pad=16))

        if race_tiles:
            content.append(self._section("Racial Traits"))
            content.append(_card(
                ft.Column(race_tiles, spacing=0), pad=0))

        if feat_tiles:
            content.append(self._section("Class Features"))
            content.append(_card(
                ft.Column(feat_tiles, spacing=0), pad=0))

        if spell_section:
            if caster_stats_row:
                content.append(caster_stats_row)
            content.extend(spell_section)

        if equip_chips:
            content.append(self._section("Equipment"))
            content.append(_card(
                ft.Row(equip_chips, wrap=True, spacing=6, run_spacing=6),
                pad=16,
            ))

        personality_items = []
        for label, val in [("Traits", char.personality_traits),
                           ("Ideals", char.ideals),
                           ("Bonds", char.bonds),
                           ("Flaws", char.flaws)]:
            if val:
                personality_items.append(ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    border_radius=10,
                    bgcolor=SURFACE_BRIGHT,
                    content=ft.Column(spacing=2, controls=[
                        ft.Text(label, size=11, weight=ft.FontWeight.BOLD,
                                color=GOLD_DIM),
                        ft.Text(val, size=12, color=ON_SURFACE),
                    ]),
                ))
        if personality_items:
            content.append(self._section("Personality"))
            content.append(ft.Column(spacing=8, controls=personality_items))

        if char.backstory:
            content.append(self._section("Backstory"))
            content.append(_card(ft.Text(
                char.backstory, size=12, color=ON_SURFACE), pad=18))

        content.append(ft.Container(height=30))

        # ── Action buttons ──
        def on_save(e):
            if not self.current_raw:
                self._snack_err("No sheet data to save.")
                return
            name = self.current_raw.get("name", "personagem")
            path = save_json_file(FICHAS_DIR, f"{name}_ficha.json")
            if not path:
                return
            if not path.endswith(".json"):
                path += ".json"
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.current_raw, f, ensure_ascii=False, indent=2)
                self._snack_ok(f"Sheet saved: {Path(path).name}")
            except Exception as ex:
                self._snack_err(f"Error saving: {ex}")

        def on_pdf(e):
            if not self.current_char:
                self._snack_err("No character loaded.")
                return
            name = self.current_char.name or "personagem"
            path = save_pdf_file(FICHAS_DIR, f"{name}_ficha.pdf")
            if not path:
                return
            if not path.endswith(".pdf"):
                path += ".pdf"
            try:
                export_pdf(self.current_char, path)
                self._snack_ok(f"PDF exported: {Path(path).name}")
            except Exception as ex:
                self._snack_err(f"Error exporting: {ex}")

        def on_level_up(e):
            self._do_level_up_flow()

        _bar_btn = ft.ButtonStyle(color=ON_SURFACE)

        top_bar = ft.Container(
            bgcolor=SURFACE,
            border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.TextButton(
                        "Back", icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self._show_prefs(),
                        style=_bar_btn),
                    ft.Text(char.name, size=16, weight=ft.FontWeight.BOLD,
                            color=GOLD, expand=True,
                            text_align=ft.TextAlign.CENTER),
                    ft.Row(spacing=8,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER,
                           controls=[
                        ft.FilledButton(
                            "Level Up", icon=ft.Icons.ARROW_UPWARD,
                            on_click=on_level_up,
                            style=ft.ButtonStyle(
                                bgcolor=GOLD, color=ON_GOLD)),
                        ft.FilledButton(
                            "Save", icon=ft.Icons.SAVE,
                            on_click=on_save,
                            style=ft.ButtonStyle(
                                bgcolor=GREEN, color=ON_GOLD,
                                icon_color=ON_GOLD)),
                        ft.OutlinedButton(
                            "PDF", icon=ft.Icons.PICTURE_AS_PDF,
                            on_click=on_pdf, style=_bar_btn),
                        ft.OutlinedButton(
                            "New", icon=ft.Icons.ADD,
                            on_click=lambda e: self._show_prefs(),
                            style=_bar_btn),
                    ]),
                ],
            ),
        )

        view = ft.Column(spacing=0, expand=True, controls=[
            top_bar,
            ft.Container(
                expand=True,
                content=ft.ListView(
                    padding=ft.padding.symmetric(horizontal=40, vertical=20),
                    spacing=14, controls=content, expand=True,
                ),
            ),
        ])
        self._navigate(view)

    # ── Spell section ─────────────────────────────────────────

    def _build_spell_section(self, char: Character,
                             ability_full_pt: dict) -> list[ft.Control]:
        if not char.cantrips and not char.spells:
            return []

        controls: list[ft.Control] = []
        ab_pt = ability_full_pt.get(
            char.spellcasting_ability, char.spellcasting_ability.title())
        controls.append(self._section(f"Spellcasting ({ab_pt})"))

        if char.spell_slots:
            controls.append(self._build_slot_tracker(char))

        if char.cantrips:
            controls.append(ft.Text(
                "Cantrips", size=14,
                weight=ft.FontWeight.W_600, color=GOLD_DIM))
            cantrip_tiles = []
            for i, sp in enumerate(char.cantrips):
                if i > 0:
                    cantrip_tiles.append(ft.Divider(height=1, color=BORDER))
                cantrip_tiles.append(self._spell_tile(sp))
            controls.append(_card(
                ft.Column(cantrip_tiles, spacing=0), pad=0))

        if char.spells:
            by_level: dict[int, list[dict]] = {}
            for sp in char.spells:
                sl = sp.get("level", 1)
                by_level.setdefault(sl, []).append(sp)
            for sl in sorted(by_level):
                controls.append(ft.Text(
                    f"Level {sl} Spells", size=14,
                    weight=ft.FontWeight.W_600, color=ON_SURFACE))
                spell_tiles = []
                for i, sp in enumerate(by_level[sl]):
                    if i > 0:
                        spell_tiles.append(
                            ft.Divider(height=1, color=BORDER))
                    spell_tiles.append(self._spell_tile(sp))
                controls.append(_card(
                    ft.Column(spell_tiles, spacing=0), pad=0))

        return controls

    def _spell_tile(self, sp: dict) -> ft.Control:
        name = sp.get("name", "?")
        desc = sp.get("description", "")
        meta_parts = []
        for key in ["casting_time", "range", "duration", "school", "components"]:
            if sp.get(key):
                meta_parts.append(sp[key])
        meta = "  ·  ".join(meta_parts)

        subtitle = ft.Text(meta, size=10, color=ON_SURFACE) if meta else None
        inner = [ft.Container(
            padding=ft.padding.only(left=16, right=16, bottom=14),
            content=ft.Text(desc, size=12))] if desc else []

        return ft.ExpansionTile(
            title=ft.Text(name, weight=ft.FontWeight.W_600, size=13),
            subtitle=subtitle,
            controls=inner,
            expanded=False,
            controls_padding=0,
        )

    def _build_slot_tracker(self, char: Character) -> ft.Control:
        rows = []
        for sl, cnt in sorted(char.spell_slots.items()):
            if not isinstance(cnt, int) or cnt <= 0:
                continue
            key = str(sl)
            self.slot_states[key] = [False] * cnt
            circles = []
            for i in range(cnt):
                idx = i

                def make_toggle(k=key, ix=idx):
                    def toggle(e):
                        self.slot_states[k][ix] = not self.slot_states[k][ix]
                        used = self.slot_states[k][ix]
                        e.control.icon = (
                            ft.Icons.CIRCLE_OUTLINED if used else ft.Icons.CIRCLE)
                        e.control.icon_color = TEXT_DIM if used else GOLD
                        self.page.update()
                    return toggle

                circles.append(ft.IconButton(
                    icon=ft.Icons.CIRCLE, icon_color=GOLD, icon_size=22,
                    on_click=make_toggle(),
                    tooltip="Click to use/recover"))

            rows.append(ft.Row([
                ft.Text(f"Lv {sl}:", size=12, width=48, color=ON_SURFACE),
                *circles,
            ], spacing=2))

        def reset_all(e):
            for k in self.slot_states:
                self.slot_states[k] = [False] * len(self.slot_states[k])
            self._show_result(self.current_char)

        return _card(ft.Column([
            ft.Row([
                ft.Text("Spell Slots", size=14,
                        weight=ft.FontWeight.W_600, color=GOLD),
                ft.TextButton(
                    "Long Rest", icon=ft.Icons.HOTEL,
                    on_click=reset_all,
                    style=ft.ButtonStyle(color=ON_SURFACE)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            *rows,
        ], spacing=6), pad=18)

    # ── Helpers ───────────────────────────────────────────────

    def _section(self, text: str) -> ft.Control:
        return ft.Container(
            padding=ft.padding.only(top=14),
            content=ft.Column(spacing=4, controls=[
                ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=GOLD),
                ft.Divider(height=1, color=BORDER),
            ]),
        )

    # ══════════════════════════════════════════════════════════
    #  GENERATION LOGIC
    # ══════════════════════════════════════════════════════════

    def _on_generate(self, level, tone, focus, race, cls, bg, extra):
        self._show_loading()

        def run():
            try:
                cfg = load_config()
                provider, key = get_active_key(cfg)
                client = LLMClient(provider, key)

                prompt = build_generation_prompt(
                    level=level, tone=tone, focus=focus,
                    fixed_race=race, fixed_class=cls,
                    fixed_background=bg, extra_info=extra)

                data = client.generate(
                    prompt, system=SYSTEM_PROMPT, json_schema=CHARACTER_SCHEMA)

                self._loading_status.value = "Validating against rules..."
                self.page.update()
                errors = validate(data)

                if errors:
                    self._loading_status.value = (
                        f"Fixing {len(errors)} issue(s)...")
                    self.page.update()
                    correction = build_correction_prompt(
                        json.dumps(data, indent=2), errors)
                    data = client.generate(
                        correction, system=SYSTEM_PROMPT,
                        json_schema=CHARACTER_SCHEMA)

                self.current_raw = data
                char = Character.from_dict(data)

                self.history.append({
                    "name": data.get("name", "?"),
                    "race": data.get("race", "?"),
                    "class_name": data.get("class_name", "?"),
                    "subclass": data.get("subclass", ""),
                    "level": data.get("level", 1),
                })
                _save_history(self.history)

                self.page.run_thread(lambda: self._show_result(char))

            except Exception as e:
                msg = str(e)

                def show_err():
                    self._show_prefs()
                    self._snack_err(f"Error: {msg}")
                self.page.run_thread(show_err)

        threading.Thread(target=run, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    #  LEVEL UP
    # ══════════════════════════════════════════════════════════

    def _do_level_up_flow(self):
        if not self.current_raw:
            return
        current_level = self.current_raw.get("level", 1)
        if current_level >= 20:
            self._snack_err("Maximum level (20) reached!")
            return

        new_level = current_level + 1
        has_sub = bool(self.current_raw.get("subclass", ""))
        cls_name = self.current_raw.get("class_name", "")
        sub_level = _subclass_pick_level(cls_name)
        needs_sub = not has_sub and new_level >= sub_level

        if needs_sub:
            self._ask_subclass(new_level)
        else:
            self._execute_level_up(new_level)

    def _ask_subclass(self, new_level: int):
        cls_name = self.current_raw.get("class_name", "???")
        sub_field = ft.TextField(
            label="Desired subclass",
            hint_text="Ex: Way of the Open Hand, Battle Master...",
            border_radius=8)

        def confirm(e):
            self.page.pop_dialog()
            self._execute_level_up(new_level, sub_field.value.strip())

        dlg = ft.AlertDialog(
            title=ft.Text(
                f"Level {new_level}: Subclass Choice!", color=GOLD),
            content=ft.Container(width=420, content=ft.Column(
                spacing=14, controls=[
                    ft.Text(
                        f"Your class ({cls_name}) gains a subclass "
                        f"at this level.\nEnter your desired subclass or "
                        f"leave empty for automatic selection.",
                        size=13, color=ON_SURFACE),
                    sub_field,
                ])),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self.page.pop_dialog(),
                    style=ft.ButtonStyle(color=RED)),
                ft.FilledButton(
                    "Level Up", on_click=confirm,
                    style=ft.ButtonStyle(bgcolor=GOLD, color=ON_GOLD)),
            ],
        )
        self.page.show_dialog(dlg)

    def _execute_level_up(self, new_level: int, subclass_pref: str = ""):
        self._show_loading(f"Leveling up to {new_level}...")

        def run():
            try:
                cfg = load_config()
                provider, key = get_active_key(cfg)
                client = LLMClient(provider, key)

                prompt = self._build_level_up_prompt(
                    self.current_raw, new_level, subclass_pref)
                data = client.generate(
                    prompt, system=SYSTEM_PROMPT, json_schema=CHARACTER_SCHEMA)

                self._loading_status.value = "Validating..."
                self.page.update()
                errors = validate(data)

                if errors:
                    self._loading_status.value = (
                        f"Fixing {len(errors)} issue(s)...")
                    self.page.update()
                    correction = build_correction_prompt(
                        json.dumps(data, indent=2), errors)
                    data = client.generate(
                        correction, system=SYSTEM_PROMPT,
                        json_schema=CHARACTER_SCHEMA)

                self.current_raw = data
                char = Character.from_dict(data)

                self.history.append({
                    "name": data.get("name", "?"),
                    "race": data.get("race", "?"),
                    "class_name": data.get("class_name", "?"),
                    "subclass": data.get("subclass", ""),
                    "level": data.get("level", 1),
                })
                _save_history(self.history)

                self.page.run_thread(lambda: self._show_result(char))

            except Exception as e:
                msg = str(e)

                def show_err():
                    self._show_prefs()
                    self._snack_err(f"Error: {msg}")
                self.page.run_thread(show_err)

        threading.Thread(target=run, daemon=True).start()

    def _build_level_up_prompt(self, current_data: dict, new_level: int,
                               subclass_pref: str = "") -> str:
        old_json = json.dumps(current_data, ensure_ascii=False, indent=2)
        old_level = current_data.get("level", 1)

        sub_instr = ""
        if subclass_pref:
            sub_instr = (
                f'\n- SUBCLASS: The player wants "{subclass_pref}". '
                f'Use this exact subclass.')
        elif not current_data.get("subclass", ""):
            sub_instr = (
                "\n- If the class gains a subclass at this level, "
                "choose an appropriate one.")

        return f"""Level up an existing D&D 5e character from level {old_level} to {new_level}.

RULES:
- Keep ALL existing data UNCHANGED (name, race, backstory, personality, equipment, etc.).
- Update "level" to {new_level}.
- Recalculate "proficiency_bonus" if needed.
- Add (average hit die rounded up + CON mod) to "hit_points".
- Add NEW features gained at level {new_level}. Keep ALL existing features.{sub_instr}
- If spellcaster: update spell_slots, add new spells/cantrips if gained. Keep existing. Include descriptions.
- If Ability Score Improvement at level {new_level}: increase scores appropriately.
- Keep ALL text in English.
- Do NOT add features from levels beyond {new_level}.

CURRENT CHARACTER:
{old_json}

Return the COMPLETE updated JSON."""

    # ══════════════════════════════════════════════════════════
    #  HISTORY
    # ══════════════════════════════════════════════════════════

    def _show_history(self):
        if not self.history:
            self._snack("No characters generated yet.", SURFACE_BRIGHT)
            return

        items = []
        for entry in reversed(self.history):
            sub = entry.get("subclass", "")
            cls = entry.get("class_name", "?")
            if sub:
                cls = f"{cls} ({sub})"
            items.append(ft.ListTile(
                title=ft.Text(entry.get("name", "?"),
                              weight=ft.FontWeight.W_600),
                subtitle=ft.Text(
                    f"Nv{entry.get('level', '?')} "
                    f"{entry.get('race', '?')} {cls}",
                    size=12, color=ON_SURFACE),
                leading=ft.Icon(ft.Icons.PERSON, color=GOLD),
            ))

        dlg = ft.AlertDialog(
            title=ft.Text("Character History", color=GOLD),
            content=ft.Container(
                width=460, height=360,
                content=ft.ListView(controls=items, spacing=4),
            ),
            actions=[ft.TextButton(
                "Close",
                on_click=lambda e: self.page.pop_dialog(),
                style=ft.ButtonStyle(color=ON_SURFACE))],
        )
        self.page.show_dialog(dlg)
