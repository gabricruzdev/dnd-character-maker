# D&D 5e Character Maker

A complete character sheet generator for Dungeons & Dragons 5th Edition (2014 rules), featuring a modern desktop interface and PDF export.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flet](https://img.shields.io/badge/GUI-Flet-purple)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Groq](https://img.shields.io/badge/AI-Groq-green)
![License](https://img.shields.io/badge/license-MIT-green)

## Tech Stack

- **Python 3.10+** — core language
- **[Flet](https://flet.dev/)** — modern desktop GUI framework
- **[Google Gemini](https://aistudio.google.com/) / [Groq](https://console.groq.com/)** — AI APIs for character generation (free tier)
- **[fpdf2](https://py-pdf.github.io/fpdf2/)** — PDF export engine
- **[dnd5eapi.co](https://www.dnd5eapi.co/)** — SRD validation API

## Features

- **Full character sheet generation** — rolled attributes (4d6 drop lowest), abilities, spells, equipment, racial traits, backstory and more
- **20+ official books supported** — Player's Handbook, Xanathar's, Tasha's, Fizban's, Volo's, Mordenkainen's, Valda's Spire of Secrets and others
- **All levels (1-20)** — including detailed spells, subclasses and correct features for each level
- **Rule validation** — checks the sheet against the SRD via dnd5eapi.co and verifies HP calculations, proficiency bonus and ability scores
- **PDF export** — layout inspired by the official D&D 5e character sheet, with 3 pages (main sheet, details and spellcasting)
- **Level Up** — load an existing sheet and level up, automatically adding new features, spells and attributes
- **Spell slot tracker** — mark used spell slots and recover them on Long Rest
- **HP tracker** — track hit points during your session
- **Save/Load** — sheets saved as JSON for future editing
- **Customization** — choose tone (comic/serious/neutral), focus (power/utility/balanced), race, class, background and extra details

## Screenshots

> Coming soon

## Requirements

- Python 3.10 or higher
- A free API key from [Google Gemini](https://aistudio.google.com/) or [Groq](https://console.groq.com/)

## Installation

```bash
git clone https://github.com/gabricruzdev/dnd-character-maker.git
cd dnd-character-maker
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. On the first run, enter your API key (Gemini or Groq)
2. Choose the level, tone, focus and optional constraints for your character
3. Click **Generate Character** and wait
4. Explore the sheet, export to PDF or save as JSON

## Project Structure

```
├── main.py                  # Entry point
├── config.py                # API key management
├── requirements.txt         # Dependencies
├── src/
│   ├── ai/
│   │   ├── llm.py           # Gemini and Groq client
│   │   ├── prompts.py       # Generation and correction prompts
│   │   └── schema.py        # Character sheet JSON schema
│   ├── engine/
│   │   └── character.py     # Character data model
│   ├── export/
│   │   └── pdf_export.py    # PDF export
│   ├── gui/
│   │   ├── app.py           # Main interface (Flet)
│   │   ├── theme.py         # Visual theme
│   │   └── native_dialogs.py # Native file dialogs
│   └── validator/
│       ├── checker.py       # D&D 5e rule validation
│       └── dnd_api.py       # dnd5eapi.co client
└── fichas/                  # Saved sheets (git-ignored)
```

## Supported Books

PHB, DMG, XGtE, TCoE, FToD, VGtM, MToF, MotM, SCAG, ERLW, EGtW, MOoT, SaCoC, VRGtR, SjAiS, DSotDQ, GGtR, AI, BPGotG, TBoMT, PAitM and Valda's Spire of Secrets (VSoS).

## Disclaimer

This project is unofficial and not affiliated with or endorsed by Wizards of the Coast. "Dungeons & Dragons" and "D&D" are trademarks of Wizards of the Coast. SRD 5.1 content is used under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/).

## Made by

**gabrielcruzdev**
