"""
Validação de fichas de personagem contra as regras de D&D 5e.

Estratégia:
  1. Conteúdo SRD -> verifica contra dnd5eapi.co
  2. Fonte oficial não-SRD -> aceita se a fonte é conhecida
  3. Verificações matemáticas -> bônus de proficiência, PV, atributos no intervalo
"""

from __future__ import annotations

from src.validator.dnd_api import (
    class_exists,
    is_official_source,
    race_exists,
    spell_exists,
)

PROFICIENCY_BY_LEVEL = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

HIT_DICE = {
    "d6": 6, "d8": 8, "d10": 10, "d12": 12,
}


def validate(data: dict) -> list[str]:
    """
    Validate a character dict. Returns a list of error strings.
    Empty list = valid character.
    """
    errors: list[str] = []

    level = data.get("level", 1)
    if not 1 <= level <= 20:
        errors.append(f"Level {level} is out of range (must be 1-20).")

    _check_ability_scores(data, errors)
    _check_proficiency_bonus(data, level, errors)
    _check_hp(data, level, errors)
    _check_race(data, errors)
    _check_class(data, errors)
    _check_spells(data, errors)
    _check_feature_levels(data, level, errors)

    return errors


def _check_ability_scores(data: dict, errors: list[str]):
    scores = data.get("ability_scores", {})
    for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
        val = scores.get(ability)
        if val is None:
            errors.append(f"Missing ability score: {ability}")
        elif not 3 <= val <= 20:
            errors.append(f"Ability score {ability} = {val} is out of range (3-20).")


def _check_proficiency_bonus(data: dict, level: int, errors: list[str]):
    expected = PROFICIENCY_BY_LEVEL.get(level, 2)
    actual = data.get("proficiency_bonus", 0)
    if actual != expected:
        errors.append(
            f"Proficiency bonus is {actual} but should be {expected} at level {level}."
        )


def _check_hp(data: dict, level: int, errors: list[str]):
    hit_die_str = data.get("hit_die", "d8")
    die_max = HIT_DICE.get(hit_die_str.lower())
    if die_max is None:
        errors.append(f"Unknown hit die: {hit_die_str}")
        return

    con_score = data.get("ability_scores", {}).get("constitution", 10)
    con_mod = (con_score - 10) // 2

    min_hp = die_max + con_mod + (level - 1) * (1 + con_mod)
    max_hp = die_max + con_mod + (level - 1) * (die_max + con_mod)
    actual_hp = data.get("hit_points", 0)

    if actual_hp < min_hp:
        errors.append(
            f"HP {actual_hp} is too low. Minimum for level {level} with {hit_die_str} "
            f"and CON {con_score} is {min_hp}."
        )
    elif actual_hp > max_hp:
        errors.append(
            f"HP {actual_hp} is too high. Maximum for level {level} with {hit_die_str} "
            f"and CON {con_score} is {max_hp}."
        )


def _check_race(data: dict, errors: list[str]):
    race_name = data.get("race", "")
    source = data.get("race_source", "")

    if not race_name:
        errors.append("Race is missing.")
        return

    if is_official_source(source):
        in_srd = race_exists(race_name)
        if in_srd is False and source == "PHB":
            errors.append(f"Race '{race_name}' claimed to be from PHB but not found in SRD.")
    else:
        errors.append(f"Race '{race_name}' has unknown source '{source}'. Must be an official book or VSoS.")


def _check_class(data: dict, errors: list[str]):
    class_name = data.get("class_name", "")
    source = data.get("class_source", "")

    if not class_name:
        errors.append("Class is missing.")
        return

    if is_official_source(source):
        in_srd = class_exists(class_name)
        if in_srd is False and source == "PHB":
            errors.append(f"Class '{class_name}' claimed to be from PHB but not found in SRD.")
    else:
        errors.append(f"Class '{class_name}' has unknown source '{source}'. Must be an official book or VSoS.")


def _check_feature_levels(data: dict, level: int, errors: list[str]):
    """Reject any class/subclass feature whose listed level exceeds the character level."""
    features = data.get("features", [])
    if not isinstance(features, list):
        return
    for feat in features:
        feat_level = feat.get("level")
        feat_name = feat.get("name", "???")
        if isinstance(feat_level, int) and feat_level > level:
            errors.append(
                f"Feature '{feat_name}' is level {feat_level} but character is only level {level}. Remove it."
            )

    subclass = data.get("subclass", "")
    SUBCLASS_LEVELS = {
        "barbarian": 3, "bard": 3, "cleric": 1, "druid": 2,
        "fighter": 3, "monk": 3, "paladin": 3, "ranger": 3,
        "rogue": 3, "sorcerer": 1, "warlock": 1, "wizard": 2,
    }
    _PT_TO_EN = {
        "barbaro": "barbarian", "bardo": "bard", "bruxo": "warlock",
        "clerigo": "cleric", "druida": "druid", "guerreiro": "fighter",
        "ladino": "rogue", "mago": "wizard", "monge": "monk",
        "paladino": "paladin", "patrulheiro": "ranger", "feiticeiro": "sorcerer",
    }
    class_name = data.get("class_name", "").lower()
    en_class = _PT_TO_EN.get(class_name, class_name)
    min_sub_level = SUBCLASS_LEVELS.get(en_class, 3)
    if subclass and level < min_sub_level:
        errors.append(
            f"Subclass '{subclass}' listed but {en_class} only gets a subclass at level {min_sub_level}. "
            f"Character is level {level}, so subclass must be empty."
        )


def _check_spells(data: dict, errors: list[str]):
    """Verifica algumas magias contra a API do SRD."""
    all_spells = data.get("cantrips", []) + data.get("spells", [])
    checked = 0
    for sp in all_spells:
        if checked >= 5:
            break
        name = sp.get("name", "")
        source = sp.get("source", "PHB")
        if not name:
            continue

        if source in ("PHB", ""):
            found = spell_exists(name)
            if found is False:
                errors.append(f"Spell '{name}' not found in SRD. If it's from another book, specify the source.")
            if found is not None:
                checked += 1
