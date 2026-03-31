"""
Exports a Character to a PDF styled after the official D&D 5e character sheet.
3 pages: Main sheet, Details, Spellcasting (if caster).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fpdf import FPDF

if TYPE_CHECKING:
    from src.engine.character import Character


def _clean(text: str) -> str:
    """Replace Unicode chars unsupported by latin-1 core fonts."""
    return (text
            .replace("\u2014", " - ")   # em dash
            .replace("\u2013", "-")     # en dash
            .replace("\u2018", "'")     # left single quote
            .replace("\u2019", "'")     # right single quote
            .replace("\u201c", '"')     # left double quote
            .replace("\u201d", '"')     # right double quote
            .replace("\u2026", "...")   # ellipsis
            .replace("\u2022", "-")     # bullet
            .replace("\u2212", "-")     # minus sign
            .replace("\u00d7", "x")     # multiplication sign
            .replace("\u2032", "'")     # prime
            .replace("\u2033", '"')     # double prime
            .replace("\u00b7", ".")     # middle dot
            .replace("\u2010", "-")     # hyphen
            .replace("\u2011", "-")     # non-breaking hyphen
            )

# ── Page constants (A4) ──────────────────────────────────────
W, H = 210, 297
M = 8
UW = W - 2 * M  # usable width

# ── Colors ────────────────────────────────────────────────────
C_BLACK = (30, 30, 40)
C_DARK = (50, 50, 65)
C_MID = (100, 100, 120)
C_LIGHT = (230, 230, 238)
C_BG = (245, 245, 250)
C_WHITE = (255, 255, 255)
C_GOLD = (180, 145, 20)
C_ACCENT = (70, 50, 30)

# ── Skills table ──────────────────────────────────────────────
ALL_SKILLS = [
    ("Acrobatics", "dexterity"),
    ("Animal Handling", "wisdom"),
    ("Arcana", "intelligence"),
    ("Athletics", "strength"),
    ("Deception", "charisma"),
    ("History", "intelligence"),
    ("Insight", "wisdom"),
    ("Intimidation", "charisma"),
    ("Investigation", "intelligence"),
    ("Medicine", "wisdom"),
    ("Nature", "intelligence"),
    ("Perception", "wisdom"),
    ("Performance", "charisma"),
    ("Persuasion", "charisma"),
    ("Religion", "intelligence"),
    ("Sleight of Hand", "dexterity"),
    ("Stealth", "dexterity"),
    ("Survival", "wisdom"),
]

ABILITY_ORDER = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
ABILITY_LABEL = {
    "strength": "STRENGTH", "dexterity": "DEXTERITY", "constitution": "CONSTITUTION",
    "intelligence": "INTELLIGENCE", "wisdom": "WISDOM", "charisma": "CHARISMA",
}
ABILITY_ABBR = {
    "strength": "STR", "dexterity": "DEX", "constitution": "CON",
    "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA",
}


def _modifier(score: int) -> int:
    return (score - 10) // 2


def _mod_str(score: int) -> str:
    m = _modifier(score)
    return f"+{m}" if m >= 0 else str(m)


class CharacterSheet(FPDF):
    """Custom FPDF subclass for drawing D&D character sheet elements."""

    def __init__(self, char: "Character"):
        super().__init__()
        self.char = char
        self.set_auto_page_break(auto=True, margin=15)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_MID)
        self.cell(0, 5, f"Page {self.page_no()}  |  D&D Character Maker  -  gabrielcruzdev",
                  align="C")

    # ── Drawing primitives ────────────────────────────────────

    def _section_header(self, x: float, y: float, w: float, title: str):
        self.set_xy(x, y)
        self.set_fill_color(*C_DARK)
        self.set_text_color(*C_WHITE)
        self.set_font("Helvetica", "B", 8)
        self.cell(w, 5.5, _clean(f"  {title}"), fill=True)
        self.set_text_color(*C_BLACK)

    def _box(self, x: float, y: float, w: float, h: float, fill: bool = True):
        if fill:
            self.set_fill_color(*C_BG)
            self.rect(x, y, w, h, "DF")
        else:
            self.rect(x, y, w, h, "D")

    def _circle(self, cx: float, cy: float, r: float, filled: bool = False):
        if filled:
            self.set_fill_color(*C_BLACK)
            self.ellipse(cx - r, cy - r, 2 * r, 2 * r, "F")
        else:
            self.set_draw_color(*C_MID)
            self.ellipse(cx - r, cy - r, 2 * r, 2 * r, "D")

    def _text_at(self, x: float, y: float, text: str, font: str = "Helvetica",
                 style: str = "", size: float = 9, color: tuple = C_BLACK,
                 align: str = "L", w: float = 0):
        self.set_xy(x, y)
        self.set_font(font, style, size)
        self.set_text_color(*color)
        self.cell(w, size * 0.4, _clean(text), align=align)

    # ══════════════════════════════════════════════════════════
    #  PAGE 1: MAIN CHARACTER SHEET
    # ══════════════════════════════════════════════════════════

    def draw_page1(self):
        self.add_page()
        self.set_draw_color(*C_MID)
        self.set_line_width(0.3)

        self._draw_header()
        self._draw_abilities()
        self._draw_saving_throws()
        self._draw_skills()
        self._draw_combat_block()
        self._draw_proficiencies_block()
        self._draw_equipment_block()
        self._draw_personality_block()

    def _draw_header(self):
        c = self.char
        y = M

        self.set_fill_color(*C_DARK)
        self.rect(M, y, UW, 14, "F")
        self._text_at(M + 3, y + 2, c.name, style="B", size=14, color=C_WHITE)
        self._text_at(M + UW - 3, y + 5,
                      f"made by gabrielcruzdev",
                      size=6, color=C_MID, align="R", w=0)
        y += 14

        boxes = [
            ("Class & Level", f"Lv{c.level} {c.class_display()}", 65),
            ("Background", c.background, 40),
            ("Race", c.race_display(), 50),
            ("Alignment", c.alignment, 35),
        ]
        bx = M
        for label, value, bw in boxes:
            self._box(bx, y, bw, 12)
            self._text_at(bx + 1, y + 0.5, label, size=5, color=C_MID)
            self._text_at(bx + 1, y + 4, value, style="B", size=7, color=C_BLACK)
            bx += bw

        self._header_y_end = y + 13

    def _draw_abilities(self):
        c = self.char
        x0 = M
        y0 = self._header_y_end + 1
        box_w = 22
        box_h = 22

        self._section_header(x0, y0, box_w, "ABILITIES")
        y = y0 + 6.5

        for ab in ABILITY_ORDER:
            score = c.ability_scores.get(ab, 10)
            mod = _mod_str(score)

            self._box(x0, y, box_w, box_h)
            self._text_at(x0, y + 1, ABILITY_LABEL[ab], size=4.5, color=C_MID,
                          align="C", w=box_w)
            self._text_at(x0, y + 5.5, str(score), style="B", size=16,
                          color=C_BLACK, align="C", w=box_w)

            cx = x0 + box_w / 2
            cy = y + box_h - 3.5
            self._circle(cx, cy, 4)
            self._text_at(x0, y + box_h - 6, mod, style="B", size=8,
                          color=C_BLACK, align="C", w=box_w)

            y += box_h + 1

        self._abilities_y_end = y

    def _draw_saving_throws(self):
        c = self.char
        x0 = M + 23
        y0 = self._header_y_end + 1
        w = 38

        self._section_header(x0, y0, w, "SAVING THROWS")
        y = y0 + 7

        for ab in ABILITY_ORDER:
            score = c.ability_scores.get(ab, 10)
            mod = _modifier(score)
            is_prof = c._is_save_proficient(ab)
            save_val = mod + (c.proficiency_bonus if is_prof else 0)

            self._circle(x0 + 2.5, y + 1.5, 1.5, filled=is_prof)

            val_str = f"{'+' if save_val >= 0 else ''}{save_val}"
            self._text_at(x0 + 5.5, y - 0.5, val_str, style="B", size=7, color=C_BLACK)
            self._text_at(x0 + 13, y - 0.5, ABILITY_ABBR[ab], size=7, color=C_MID)

            y += 5.5

        self._saves_y_end = y

    def _draw_skills(self):
        c = self.char
        x0 = M + 23
        y0 = self._saves_y_end + 2
        w = 38

        self._section_header(x0, y0, w, "SKILLS")
        y = y0 + 6.5

        prof_lower = [s.lower().replace(" ", "") for s in c.skill_proficiencies]

        for eng_name, ability in ALL_SKILLS:
            score = c.ability_scores.get(ability, 10)
            mod = _modifier(score)
            is_prof = eng_name.lower().replace(" ", "") in prof_lower
            val = mod + (c.proficiency_bonus if is_prof else 0)

            self._circle(x0 + 2.5, y + 1.2, 1.2, filled=is_prof)

            val_str = f"{'+' if val >= 0 else ''}{val}"
            self._text_at(x0 + 5, y - 0.5, val_str, size=6, color=C_BLACK, style="B")
            self._text_at(x0 + 11, y - 0.5, eng_name, size=5.5, color=C_DARK)

            y += 4.5

        self._skills_y_end = y

    def _draw_combat_block(self):
        c = self.char
        x0 = M + 63
        y0 = self._header_y_end + 1
        col_w = 64

        stat_w = 20
        stats = [
            ("AC", str(c.armor_class)),
            ("Initiative", _mod_str(c.ability_scores.get("dexterity", 10))),
            ("Speed", f"{c.speed}ft"),
        ]
        for i, (label, value) in enumerate(stats):
            sx = x0 + i * (stat_w + 1.5)
            self._box(sx, y0, stat_w, 18)
            self._text_at(sx, y0 + 1, label, size=5, color=C_MID, align="C", w=stat_w)
            self._text_at(sx, y0 + 6, value, style="B", size=14, color=C_BLACK,
                          align="C", w=stat_w)

        y = y0 + 20

        self._section_header(x0, y, col_w, "HIT POINTS")
        y += 6.5
        self._box(x0, y, col_w, 14)
        self._text_at(x0 + 2, y + 1, "Max HP", size=5, color=C_MID)
        self._text_at(x0 + 2, y + 5, str(c.hit_points), style="B", size=14, color=C_BLACK)
        y += 15

        self._box(x0, y, col_w / 2 - 0.5, 11)
        self._text_at(x0 + 1, y + 0.5, "Hit Dice", size=5, color=C_MID)
        self._text_at(x0 + 1, y + 4.5, f"{c.level}{c.hit_die}", style="B", size=8, color=C_BLACK)

        self._box(x0 + col_w / 2 + 0.5, y, col_w / 2 - 0.5, 11)
        self._text_at(x0 + col_w / 2 + 1.5, y + 0.5, "Prof. Bonus", size=5, color=C_MID)
        self._text_at(x0 + col_w / 2 + 1.5, y + 4.5, f"+{c.proficiency_bonus}",
                      style="B", size=10, color=C_BLACK)

        self._combat_y_end = y + 12

    def _draw_proficiencies_block(self):
        c = self.char
        x0 = M + 63
        y = self._combat_y_end + 2
        col_w = 64

        self._section_header(x0, y, col_w, "PROFICIENCIES")
        y += 6

        items = []
        if c.armor_proficiencies:
            items.append(("Armor", ", ".join(c.armor_proficiencies)))
        if c.weapon_proficiencies:
            items.append(("Weapons", ", ".join(c.weapon_proficiencies)))
        if c.tool_proficiencies:
            items.append(("Tools", ", ".join(c.tool_proficiencies)))
        if c.languages:
            items.append(("Languages", ", ".join(c.languages)))

        for label, text in items:
            self._text_at(x0 + 1, y, label, size=5.5, color=C_GOLD, style="B")
            y += 3.5
            self.set_xy(x0 + 1, y)
            self.set_font("Helvetica", "", 6)
            self.set_text_color(*C_BLACK)
            self.multi_cell(col_w - 2, 3, _clean(text))
            y = self.get_y() + 1.5

        self._prof_y_end = y

    def _draw_equipment_block(self):
        c = self.char
        x0 = M + 63
        y = self._prof_y_end + 1
        col_w = 64

        self._section_header(x0, y, col_w, "EQUIPMENT")
        y += 6

        if c.equipment:
            for item in c.equipment:
                self._text_at(x0 + 2, y, f"- {item}", size=6, color=C_BLACK)
                y += 3.5

    def _draw_personality_block(self):
        c = self.char
        x0 = M + 129
        y0 = self._header_y_end + 1
        col_w = UW - (x0 - M)

        sections = [
            ("PERSONALITY TRAITS", c.personality_traits),
            ("IDEALS", c.ideals),
            ("BONDS", c.bonds),
            ("FLAWS", c.flaws),
        ]

        y = y0
        for label, text in sections:
            self._section_header(x0, y, col_w, label)
            y += 6
            if text:
                self.set_xy(x0 + 1, y)
                self.set_font("Helvetica", "", 6.5)
                self.set_text_color(*C_BLACK)
                self.multi_cell(col_w - 2, 3.2, _clean(text))
                y = self.get_y() + 2
            else:
                y += 15

    # ══════════════════════════════════════════════════════════
    #  PAGE 2: TRAITS, FEATURES, BACKSTORY
    # ══════════════════════════════════════════════════════════

    def draw_page2(self):
        self.add_page()
        self.set_draw_color(*C_MID)
        self.set_line_width(0.3)
        c = self.char
        y = M

        self.set_fill_color(*C_DARK)
        self.rect(M, y, UW, 10, "F")
        self._text_at(M + 3, y + 1.5, f"{c.name}  —  Character Details",
                      style="B", size=11, color=C_WHITE)
        y += 12

        if c.race_traits:
            y = self._draw_feature_section(y, "RACIAL TRAITS", c.race_traits, show_level=False)

        if c.features:
            feat_list = [
                {
                    "name": f"[Lv{f.get('level', '?')}] {f.get('name', '')} ({f.get('source', '')})",
                    "description": f.get("description", ""),
                }
                for f in c.features
            ]
            y = self._draw_feature_section(y, "CLASS FEATURES", feat_list, show_level=False)

        if c.backstory:
            if y > H - 60:
                self.add_page()
                y = M
            self._section_header(M, y, UW, "BACKSTORY")
            y += 6.5
            self.set_xy(M + 1, y)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*C_BLACK)
            self.multi_cell(UW - 2, 4, _clean(c.backstory))

    def _draw_feature_section(self, y: float, title: str, features: list[dict],
                               show_level: bool = True) -> float:
        if y > H - 40:
            self.add_page()
            y = M

        self._section_header(M, y, UW, title)
        y += 6.5

        for feat in features:
            name = feat.get("name", "")
            desc = feat.get("description", "")

            needed = 8 + (len(desc) // 70) * 3.5
            if y + needed > H - 20:
                self.add_page()
                y = M

            self.set_xy(M + 1, y)
            self.set_font("Helvetica", "B", 7.5)
            self.set_text_color(*C_ACCENT)
            self.cell(UW - 2, 4, _clean(name))
            y += 4

            if desc:
                self.set_xy(M + 3, y)
                self.set_font("Helvetica", "", 7)
                self.set_text_color(*C_BLACK)
                self.multi_cell(UW - 6, 3.2, _clean(desc))
                y = self.get_y() + 1.5
            else:
                y += 2

        return y + 2

    # ══════════════════════════════════════════════════════════
    #  PAGE 3: SPELLCASTING
    # ══════════════════════════════════════════════════════════

    def draw_page3(self):
        c = self.char
        if not c.cantrips and not c.spells:
            return

        self.add_page()
        self.set_draw_color(*C_MID)
        self.set_line_width(0.3)
        y = M

        self.set_fill_color(*C_DARK)
        self.rect(M, y, UW, 10, "F")
        ability_name = {
            "strength": "Strength", "dexterity": "Dexterity", "constitution": "Constitution",
            "intelligence": "Intelligence", "wisdom": "Wisdom", "charisma": "Charisma",
        }.get(c.spellcasting_ability, c.spellcasting_ability.title())
        self._text_at(M + 3, y + 1.5, f"Spellcasting  —  {ability_name}",
                      style="B", size=11, color=C_WHITE)
        y += 12

        ab_score = c.ability_scores.get(c.spellcasting_ability, 10)
        ab_mod = _modifier(ab_score)
        spell_dc = 8 + c.proficiency_bonus + ab_mod
        spell_atk = c.proficiency_bonus + ab_mod

        stats = [
            ("Ability", ability_name),
            ("Spell DC", str(spell_dc)),
            ("Spell Attack", f"+{spell_atk}" if spell_atk >= 0 else str(spell_atk)),
        ]
        stat_w = UW / 3
        for i, (label, value) in enumerate(stats):
            sx = M + i * stat_w
            self._box(sx, y, stat_w - 1, 14)
            self._text_at(sx + 1, y + 1, label, size=6, color=C_MID)
            self._text_at(sx + 1, y + 5.5, value, style="B", size=11, color=C_BLACK)
        y += 16

        if c.spell_slots:
            self._section_header(M, y, UW, "SPELL SLOTS")
            y += 6.5
            slot_w = UW / min(len(c.spell_slots), 9)
            for i, (sl, cnt) in enumerate(sorted(c.spell_slots.items())):
                sx = M + i * slot_w
                self._box(sx, y, slot_w - 1, 10)
                self._text_at(sx + 1, y + 0.5, f"Level {sl}", size=5, color=C_MID)
                self._text_at(sx + 1, y + 4, str(cnt), style="B", size=9, color=C_BLACK)
            y += 12

        if c.cantrips:
            self._section_header(M, y, UW, "CANTRIPS")
            y += 6.5
            for sp in c.cantrips:
                y = self._draw_spell_entry(y, sp)
            y += 2

        if c.spells:
            by_level: dict[int, list[dict]] = {}
            for sp in c.spells:
                sl = sp.get("level", 1)
                by_level.setdefault(sl, []).append(sp)

            for sl in sorted(by_level):
                if y > H - 30:
                    self.add_page()
                    y = M

                slot_count = c.spell_slots.get(str(sl), c.spell_slots.get(sl, "?"))
                self._section_header(M, y, UW, f"LEVEL {sl}  -  {slot_count} slot(s)")
                y += 6.5

                for sp in by_level[sl]:
                    y = self._draw_spell_entry(y, sp)
                y += 2

    def _draw_spell_entry(self, y: float, sp: dict) -> float:
        name = sp.get("name", "?")
        desc = sp.get("description", "")
        meta_parts = []
        if sp.get("casting_time"):
            meta_parts.append(sp["casting_time"])
        if sp.get("range"):
            meta_parts.append(sp["range"])
        if sp.get("duration"):
            meta_parts.append(sp["duration"])
        if sp.get("school"):
            meta_parts.append(sp["school"])
        meta = "  |  ".join(meta_parts)

        needed = 6 + (len(desc) // 80) * 3.5 + (4 if meta else 0)
        if y + needed > H - 20:
            self.add_page()
            y = M

        self.set_xy(M + 2, y)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*C_ACCENT)
        self.cell(UW - 4, 4, _clean(name))
        y += 4

        if meta:
            self._text_at(M + 4, y, meta, size=5.5, color=C_MID)
            y += 3.5

        if desc:
            self.set_xy(M + 4, y)
            self.set_font("Helvetica", "", 6.5)
            self.set_text_color(*C_BLACK)
            self.multi_cell(UW - 8, 3, _clean(desc))
            y = self.get_y() + 1.5

        return y


# ══════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════

def export_pdf(char: "Character", filepath: str | Path) -> Path:
    filepath = Path(filepath)
    pdf = CharacterSheet(char)

    pdf.draw_page1()
    pdf.draw_page2()
    pdf.draw_page3()

    pdf.output(str(filepath))
    return filepath
