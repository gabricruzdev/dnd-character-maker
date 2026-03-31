"""
Cliente para geração de conteúdo via Google Gemini e Groq.
"""

from __future__ import annotations

import json
import re
import time

GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash"]
MAX_RETRIES = 3
RETRY_DELAY = 5


def _repair_json(text: str) -> dict:
    """Tenta reparar JSON malformado."""
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    # Find the first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    if end > start:
        text = text[start:end + 1]
    else:
        text = text[start:]

    # Attempt 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: fix common issues
    fixed = text
    # Remove trailing commas before } or ]
    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
    # Fix unescaped newlines inside strings (replace literal newlines with \n)
    fixed = _escape_newlines_in_strings(fixed)

    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 3: close truncated JSON
    fixed = _close_json(fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Attempt 4: try progressively removing content from the end
    for trim in [100, 500, 1000, 2000]:
        if len(text) > trim:
            trimmed = text[:len(text) - trim]
            trimmed = _close_json(trimmed)
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError:
                continue

    raise json.JSONDecodeError("Could not repair JSON", text, 0)


def _escape_newlines_in_strings(text: str) -> str:
    """Replace actual newlines inside JSON string values with \\n."""
    result = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            result.append(ch)
            escape = False
            continue
        if ch == '\\':
            result.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue
        if in_string and ch == '\n':
            result.append('\\n')
            continue
        result.append(ch)
    return ''.join(result)


def _close_json(text: str) -> str:
    """Close any unclosed strings, arrays, objects."""
    # Close unclosed string
    if text.count('"') % 2 == 1:
        text += '"'

    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth_brace += 1
        elif ch == '}':
            depth_brace -= 1
        elif ch == '[':
            depth_bracket += 1
        elif ch == ']':
            depth_bracket -= 1

    # Remove trailing comma before closing
    text = re.sub(r",\s*$", "", text)
    text += ']' * max(0, depth_bracket)
    text += '}' * max(0, depth_brace)
    return text


class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key

        if self.provider == "gemini":
            from google import genai
            self._gemini = genai.Client(api_key=api_key)
        elif self.provider == "groq":
            from groq import Groq
            self._groq = Groq(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'gemini' or 'groq'.")

    def generate(self, prompt: str, system: str = "", json_schema: dict | None = None) -> dict:
        if self.provider == "gemini":
            return self._generate_gemini(prompt, system, json_schema)
        return self._generate_groq(prompt, system, json_schema)

    def _parse_response(self, text: str) -> dict:
        """Interpreta resposta como JSON, com fallback de reparo."""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return _repair_json(text)

    def _generate_gemini(self, prompt: str, system: str, json_schema: dict | None) -> dict:
        config: dict = {"max_output_tokens": 65536}
        if system:
            config["system_instruction"] = system
        if json_schema:
            config["response_mime_type"] = "application/json"
            config["response_json_schema"] = json_schema

        last_error = None
        for model in GEMINI_MODELS:
            for attempt in range(MAX_RETRIES):
                try:
                    response = self._gemini.models.generate_content(
                        model=model, contents=prompt, config=config,
                    )
                    return self._parse_response(response.text)
                except json.JSONDecodeError as e:
                    last_error = e
                    continue  # retry same model
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    if "not found" in err_str or "not supported" in err_str:
                        break  # next model
                    raise

        raise RuntimeError(
            f"All Gemini models failed. Last error: {last_error}\n\n"
            "If your key is new, wait 2-3 minutes and try again."
        )

    def _generate_groq(self, prompt: str, system: str, json_schema: dict | None) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 32768,
        }
        if json_schema:
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._groq.chat.completions.create(**kwargs)
                return self._parse_response(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "429" in err_str or "rate" in err_str:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                raise

        raise RuntimeError(f"Groq failed after retries. Last error: {last_error}")

    def generate_text(self, prompt: str, system: str = "") -> str:
        if self.provider == "gemini":
            config: dict = {"max_output_tokens": 32768}
            if system:
                config["system_instruction"] = system
            for model in GEMINI_MODELS:
                try:
                    response = self._gemini.models.generate_content(
                        model=model, contents=prompt, config=config,
                    )
                    return response.text.strip()
                except Exception:
                    continue
            raise RuntimeError("All Gemini models failed for text generation.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages, temperature=0.7, max_tokens=32768,
        )
        return response.choices[0].message.content.strip()
