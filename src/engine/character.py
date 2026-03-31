"""
Modelo de dados do personagem.
Dataclass com métodos auxiliares para exibição e exportação.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


def _clean_str(s: str) -> str:
    """Junta linhas quebradas preservando parágrafos."""
    s = s.replace("\r\n", "\n")
    paragraphs = re.split(r"\n\s*\n", s)
    cleaned = []
    for p in paragraphs:
        cleaned.append(re.sub(r"\s*\n\s*", " ", p).strip())
    return "\n\n".join(p for p in cleaned if p)


def _nfc(obj):
    """Normaliza strings: forma NFC composta + junta linhas quebradas."""
    if isinstance(obj, str):
        s = unicodedata.normalize("NFC", obj)
        return _clean_str(s)
    if isinstance(obj, dict):
        return {k: _nfc(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nfc(item) for item in obj]
    return obj


def _modifier(score: int) -> int:
    return (score - 10) // 2


def _modifier_str(score: int) -> str:
    m = _modifier(score)
    return f"+{m}" if m >= 0 else str(m)


@dataclass
class Character:
    name: str = ""
    race: str = ""
    subrace: str = ""
    race_source: str = ""
    class_name: str = ""
    subclass: str = ""
    class_source: str = ""
    level: int = 1
    background: str = ""
    alignment: str = ""

    ability_scores: dict[str, int] = field(default_factory=dict)
    hit_points: int = 0
    armor_class: int = 10
    speed: int = 30
    hit_die: str = "d8"
    proficiency_bonus: int = 2

    saving_throws: list[str] = field(default_factory=list)
    skill_proficiencies: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    armor_proficiencies: list[str] = field(default_factory=list)
    weapon_proficiencies: list[str] = field(default_factory=list)
    tool_proficiencies: list[str] = field(default_factory=list)

    features: list[dict] = field(default_factory=list)
    race_traits: list[dict] = field(default_factory=list)

    cantrips: list[dict] = field(default_factory=list)
    spells: list[dict] = field(default_factory=list)
    spell_slots: dict[str, int] = field(default_factory=dict)
    spellcasting_ability: str = ""

    equipment: list[str] = field(default_factory=list)

    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""
    backstory: str = ""

    @staticmethod
    def from_dict(data: dict) -> Character:
        data = _nfc(data)
        return Character(
            name=data.get("name", ""),
            race=data.get("race", ""),
            subrace=data.get("subrace", ""),
            race_source=data.get("race_source", ""),
            class_name=data.get("class_name", ""),
            subclass=data.get("subclass", ""),
            class_source=data.get("class_source", ""),
            level=data.get("level", 1),
            background=data.get("background", ""),
            alignment=data.get("alignment", ""),
            ability_scores=data.get("ability_scores", {}),
            hit_points=data.get("hit_points", 0),
            armor_class=data.get("armor_class", 10),
            speed=data.get("speed", 30),
            hit_die=data.get("hit_die", "d8"),
            proficiency_bonus=data.get("proficiency_bonus", 2),
            saving_throws=data.get("saving_throws", []),
            skill_proficiencies=data.get("skill_proficiencies", []),
            languages=data.get("languages", []),
            armor_proficiencies=data.get("armor_proficiencies", []),
            weapon_proficiencies=data.get("weapon_proficiencies", []),
            tool_proficiencies=data.get("tool_proficiencies", []),
            features=data.get("features", []),
            race_traits=data.get("race_traits", []),
            cantrips=data.get("cantrips", []),
            spells=data.get("spells", []),
            spell_slots=data.get("spell_slots", {}),
            spellcasting_ability=data.get("spellcasting_ability", ""),
            equipment=data.get("equipment", []),
            personality_traits=data.get("personality_traits", ""),
            ideals=data.get("ideals", ""),
            bonds=data.get("bonds", ""),
            flaws=data.get("flaws", ""),
            backstory=data.get("backstory", ""),
        )

    def get_modifier(self, ability: str) -> int:
        return _modifier(self.ability_scores.get(ability, 10))

    def get_modifier_str(self, ability: str) -> str:
        return _modifier_str(self.ability_scores.get(ability, 10))

    _SAVE_ALIASES = {
        "strength": {"strength", "str", "for", "forca", "força"},
        "dexterity": {"dexterity", "dex", "des", "destreza"},
        "constitution": {"constitution", "con", "constituicao", "constituição"},
        "intelligence": {"intelligence", "int", "inteligencia", "inteligência"},
        "wisdom": {"wisdom", "wis", "sab", "sabedoria"},
        "charisma": {"charisma", "cha", "car", "carisma"},
    }

    def _is_save_proficient(self, ability: str) -> bool:
        aliases = self._SAVE_ALIASES.get(ability.lower(), {ability.lower()})
        normed = set()
        for s in self.saving_throws:
            normed.add(unicodedata.normalize("NFC", s.strip().lower()))
            normed.add(unicodedata.normalize("NFD", s.strip().lower())
                       .encode("ascii", "ignore").decode())
        return bool(aliases & normed)

    def get_save(self, ability: str) -> int:
        base = self.get_modifier(ability)
        if self._is_save_proficient(ability):
            base += self.proficiency_bonus
        return base

    def race_display(self) -> str:
        parts = self.race
        if self.subrace:
            parts = f"{self.race} ({self.subrace})"
        if self.race_source:
            parts += f" - {self.race_source}"
        return parts

    def class_display(self) -> str:
        parts = self.class_name
        if self.subclass:
            parts = f"{self.class_name} ({self.subclass})"
        if self.class_source:
            parts += f" - {self.class_source}"
        return parts
