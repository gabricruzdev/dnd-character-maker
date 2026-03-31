"""
Prompts for D&D 5e 2014 character sheet generation.
"""

SYSTEM_PROMPT = """You are an expert D&D 5e (2014 rules) character builder. You have encyclopedic knowledge 
of ALL official sourcebooks and Valda's Spire of Secrets. You follow the rules STRICTLY and never invent 
content that doesn't exist in the books. Every race, class, subclass, spell, and feature you use MUST 
come from one of the approved sources listed in the user prompt.

ALL output text (backstory, personality, descriptions, feature descriptions) MUST be written in English.
Use proper D&D terminology and write in a vivid, engaging style."""


def build_generation_prompt(
    level: int,
    tone: str,
    focus: str,
    fixed_race: str = "",
    fixed_class: str = "",
    fixed_background: str = "",
    extra_info: str = "",
) -> str:
    tone_instructions = {
        "comic": (
            "The backstory must be COMIC — funny situations, absurd coincidences, "
            "witty remarks, hilarious misadventures. Make the reader laugh."
        ),
        "serious": (
            "The backstory must be SERIOUS and dramatic — meaningful struggles, "
            "deep motivations, moral dilemmas, emotional moments."
        ),
        "neutral": (
            "The backstory should be balanced — a mix of light and serious moments."
        ),
    }

    focus_instructions = {
        "power": (
            "OPTIMIZE FOR POWER. Place the best rolls in the class's primary attributes. "
            "Choose the strongest subclass, damage spells, and combat-focused features. "
            "Build a character that hits hard and is effective in battle."
        ),
        "utility": (
            "OPTIMIZE FOR UTILITY. Distribute attributes to cover multiple areas. "
            "Choose utility/support spells, social skills, and versatile features. "
            "Build a character useful in many situations outside of combat."
        ),
        "balanced": (
            "Balance between power and utility. Good combat capability with some versatility."
        ),
    }

    constraints = []
    if fixed_race:
        constraints.append(f"- Race MUST be: {fixed_race}")
    if fixed_class:
        constraints.append(f"- Class MUST be: {fixed_class}")
    if fixed_background:
        constraints.append(f"- Background MUST be: {fixed_background}")
    constraints_text = "\n".join(constraints) if constraints else "- No constraints — choose freely from any approved source."

    return f"""Generate a COMPLETE, ready-to-play D&D 5e (2014 rules) character sheet at level {level}.

ALL text content (descriptions, backstory, personality, feature descriptions) MUST be written in English.

APPROVED SOURCES (use ANY content from these books):
- Player's Handbook (PHB)
- Dungeon Master's Guide (DMG)
- Xanathar's Guide to Everything (XGtE)
- Tasha's Cauldron of Everything (TCoE)
- Fizban's Treasury of Dragons (FToD)
- Volo's Guide to Monsters (VGtM)
- Mordenkainen's Tome of Foes (MToF)
- Mordenkainen Presents: Monsters of the Multiverse (MotM)
- Sword Coast Adventurer's Guide (SCAG)
- Eberron: Rising from the Last War (ERLW)
- Explorer's Guide to Wildemount (EGtW)
- Mythic Odysseys of Theros (MOoT)
- Strixhaven: A Curriculum of Chaos (SaCoC)
- Van Richten's Guide to Ravenloft (VRGtR)
- Spelljammer: Adventures in Space (SjAiS)
- Dragonlance: Shadow of the Dragon Queen (DSotDQ)
- Guildmasters' Guide to Ravnica (GGtR)
- Acquisitions Incorporated (AI)
- Bigby Presents: Glory of the Giants (BPGotG)
- The Book of Many Things (TBoMT)
- Planescape: Adventures in the Multiverse (PAitM)
- Valda's Spire of Secrets (VSoS) — by Mage Hand Press

CONSTRAINTS:
{constraints_text}

{f"EXTRA PLAYER REQUESTS (incorporate into the character):{chr(10)}{extra_info}" if extra_info else ""}

BUILD FOCUS: {focus_instructions.get(focus, focus_instructions["balanced"])}

TONE: {tone_instructions.get(tone, tone_instructions["neutral"])}

RULES — follow STRICTLY:

ABILITY SCORES:
1. Simulate 4d6-drop-lowest for EACH of the 6 attributes independently.
2. Show realistic roll values (typically 8-16, occasionally 7 or 17-18). Do NOT use standard arrays or round numbers.
3. After rolling, distribute among attributes based on class priorities and build focus.
4. Apply racial ability score bonuses on top of rolled values.
5. Final values after racial bonuses can range from 3 to 20.

HIT POINTS:
6. HP at level 1 = maximum hit die value + CON modifier.
7. Each level after 1st adds (average hit die rounded up) + CON modifier.

PROFICIENCY:
8. Proficiency bonus: +2 (levels 1-4), +3 (5-8), +4 (9-12), +5 (13-16), +6 (17-20).

CLASS FEATURES — THIS IS CRITICAL:
9. List ONLY class and subclass features gained from level 1 to level {level} — NOTHING BEYOND.
   Do NOT include ANY feature from a level higher than {level}. If the character is level 1, list ONLY level 1 features.
   If the character is level 3, list features from levels 1, 2, and 3 — NEVER level 4 or above.
10. For EACH feature, provide:
    - The exact official name
    - The source book abbreviation
    - The level at which it is gained
    - A COMPLETE description of what the feature does (not just the name — write the actual mechanical effect)
11. Do NOT skip any feature the character HAS at level {level}.
12. Do NOT add features from levels the character has NOT YET reached. This is a serious error.

SUBCLASS:
13. Subclasses are only chosen at the level the class grants them (usually level 3, but varies).
    If the character is BELOW the subclass selection level, the "subclass" field MUST be empty ("").
    Example: Monk level 1 does NOT have a subclass. Monk level 3+ has a subclass.

RACIAL TRAITS:
14. List ALL racial traits with complete descriptions of their mechanical effects.

SPELLS (if spellcaster):
15. Include the correct number of known cantrips for this class and level {level}.
16. Include the correct number of known/prepared spells for this class and level {level}.
17. Include the correct spell slot table for level {level}.
18. Every spell must actually exist and be available to this class.
19. Do NOT include spells of a spell level the character does not yet have access to at level {level}.
19b. For EACH spell and cantrip, include:
    - casting_time (e.g. "1 action", "1 reaction")
    - range (e.g. "120 feet", "Touch", "Self")
    - duration (e.g. "Instantaneous", "Concentration, up to 1 minute")
    - components (e.g. "V, S, M (a bit of sulfur)")
    - school (school of magic, e.g. "Evocation", "Abjuration") — for spells only, not cantrips
    - description: COMPLETE description of the spell's effect (damage, effects, saving throws, etc.)

EQUIPMENT:
20. Include appropriate starting equipment for the class.

OTHER:
21. For each feature, spell, race, class, and subclass — indicate the SOURCE BOOK ABBREVIATION.
22. Backstory: A complete and engaging backstory (3-5 paragraphs).
23. Personality traits, ideals, bonds, and flaws in English.
24. The name should match the race and tone of the character.

FINAL SUMMARY: The character is LEVEL {level}. Include ONLY what a level {level} character possesses. Nothing from future levels.

OUTPUT: Return ONLY a valid JSON object following the schema. No markdown, no code fences, no explanations — just the raw JSON."""


def build_correction_prompt(original_json: str, errors: list[str]) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return f"""The following D&D 5e (2014 rules) character sheet has validation errors. Fix ONLY the errors listed below.

IMPORTANT RULES:
- Keep ALL existing text UNCHANGED unless an error specifically requires changing it.
- ALL text (descriptions, backstory, personality, feature descriptions) MUST be in English.
- Follow D&D 5e 2014 rules STRICTLY — ability scores 3-20, correct proficiency bonus, correct HP calculation.
- Spell and feature descriptions must be COMPLETE with mechanical effects.
- Do NOT add features from levels beyond the character's current level.

ERRORS TO FIX:
{error_list}

ORIGINAL CHARACTER JSON:
{original_json}

Return the corrected JSON only. No markdown, no code fences, no explanations — just the raw JSON."""
