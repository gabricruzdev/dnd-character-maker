"""
JSON schema para a estrutura da ficha de personagem.
"""

CHARACTER_SCHEMA = {
    "type": "object",
    "properties": {
        "name":          {"type": "string", "description": "Character's full name"},
        "race":          {"type": "string", "description": "Race name (e.g. 'Tiefling')"},
        "subrace":       {"type": "string", "description": "Subrace if applicable, empty string if none"},
        "race_source":   {"type": "string", "description": "Source book abbreviation for race (e.g. 'PHB', 'VGtM')"},
        "class_name":    {"type": "string", "description": "Class name (e.g. 'Wizard')"},
        "subclass":      {"type": "string", "description": "Subclass name"},
        "class_source":  {"type": "string", "description": "Source book abbreviation for class/subclass"},
        "level":         {"type": "integer"},
        "background":    {"type": "string"},
        "alignment":     {"type": "string"},
        "ability_scores": {
            "type": "object",
            "properties": {
                "strength":     {"type": "integer"},
                "dexterity":    {"type": "integer"},
                "constitution": {"type": "integer"},
                "intelligence": {"type": "integer"},
                "wisdom":       {"type": "integer"},
                "charisma":     {"type": "integer"},
            },
            "required": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
        },
        "hit_points":    {"type": "integer"},
        "armor_class":   {"type": "integer"},
        "speed":         {"type": "integer"},
        "hit_die":       {"type": "string", "description": "e.g. 'd8'"},
        "proficiency_bonus": {"type": "integer"},
        "saving_throws": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ability names the character is proficient in for saves",
        },
        "skill_proficiencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skill names the character is proficient in",
        },
        "languages":        {"type": "array", "items": {"type": "string"}},
        "armor_proficiencies":  {"type": "array", "items": {"type": "string"}},
        "weapon_proficiencies": {"type": "array", "items": {"type": "string"}},
        "tool_proficiencies":   {"type": "array", "items": {"type": "string"}},
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "source":      {"type": "string", "description": "e.g. 'PHB' or 'XGtE'"},
                    "level":       {"type": "integer", "description": "Level at which this feature is gained"},
                    "description": {"type": "string"},
                },
                "required": ["name", "source", "level", "description"],
            },
        },
        "race_traits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "source":      {"type": "string", "description": "Source book abbreviation, e.g. 'PHB'"},
                    "description": {"type": "string"},
                },
                "required": ["name", "description"],
            },
        },
        "cantrips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "source":      {"type": "string", "description": "Source book abbreviation, e.g. 'PHB'"},
                    "casting_time": {"type": "string", "description": "e.g. '1 action'"},
                    "range":       {"type": "string", "description": "e.g. '120 feet'"},
                    "duration":    {"type": "string", "description": "e.g. 'Instantaneous'"},
                    "components":  {"type": "string", "description": "e.g. 'V, S'"},
                    "description": {"type": "string", "description": "Full spell effect in Portuguese"},
                },
                "required": ["name", "casting_time", "range", "duration", "description"],
            },
        },
        "spells": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "level":       {"type": "integer"},
                    "source":      {"type": "string", "description": "Source book abbreviation, e.g. 'PHB'"},
                    "school":      {"type": "string", "description": "e.g. 'Evocation'"},
                    "casting_time": {"type": "string"},
                    "range":       {"type": "string"},
                    "duration":    {"type": "string"},
                    "components":  {"type": "string", "description": "e.g. 'V, S, M (a bit of fleece)'"},
                    "description": {"type": "string", "description": "Full spell effect in Portuguese"},
                },
                "required": ["name", "level", "casting_time", "range", "duration", "description"],
            },
        },
        "spell_slots": {
            "type": "object",
            "description": "Spell slots per level, e.g. {'1': 4, '2': 3}",
        },
        "spellcasting_ability": {"type": "string", "description": "e.g. 'charisma', empty if non-caster"},
        "equipment": {
            "type": "array",
            "items": {"type": "string"},
        },
        "personality_traits": {"type": "string"},
        "ideals":             {"type": "string"},
        "bonds":              {"type": "string"},
        "flaws":              {"type": "string"},
        "backstory":          {"type": "string", "description": "Complete character backstory (3-5 paragraphs)"},
    },
    "required": [
        "name", "race", "subrace", "race_source", "class_name", "subclass",
        "class_source", "level", "background", "alignment", "ability_scores",
        "hit_points", "armor_class", "speed", "hit_die", "proficiency_bonus",
        "saving_throws", "skill_proficiencies", "languages",
        "armor_proficiencies", "weapon_proficiencies", "tool_proficiencies",
        "features", "race_traits", "cantrips", "spells", "spell_slots",
        "spellcasting_ability", "equipment",
        "personality_traits", "ideals", "bonds", "flaws", "backstory",
    ],
}
