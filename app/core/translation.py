import os
import re
import json
import yaml
from google import genai
from pathlib import Path
from loguru import logger
from google.genai import types
from dotenv import load_dotenv
from colorama import Fore, Style, init
import sys


init(autoreset=True)

def translate_texts_with_gemini(text_info_list: list[dict], languages: list[str], gemini: list[str|float], glossary_path: str, output_dir: str, log_level: str):
    '''
    Translate all texts from one chapter and summarize them with Gemini
    '''
    if not text_info_list:
        return text_info_list

    source_lang, target_lang = languages
    model, temperature, top_p, max_out_tokens = gemini

    logger.info(f"\nTranslating texts to ({target_lang.upper()}) with Gemini.")

    data_dict = "data_dict" # define placeholder to prevent error when logging exception

    # Load environment variables from .env file
    load_dotenv()

    # Get the API key from the environment variables
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        raise Exception(Fore.RED + f"Failed to initialize Gemini client: {e}")

    response_schema={
        "type": "object",
        "properties": {
            "Translation": {
                "type": "string",
                "description": "The full translated text."},
            "Glossary": {
                "type": "array",
                "description": "A glossary of new terms",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_term": {
                            "type": "string"
                        },
                        "translated_term": {
                            "type": "string"
                        }
                    },
                    "required": ["source_term", "translated_term"]
                }
            }
        },
        "required": ["Translation", "Glossary"]
    }

    my_config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_out_tokens,
        response_mime_type="application/json",
        response_schema=response_schema
    )

    # Load existing glossary file
    if os.path.exists(glossary_path):
        with open(glossary_path, "r", encoding="utf-8") as glossary:
            existing_glossary = json.load(glossary)["GLOSSARY"]

        # Create a lookup map for AI context: { "source term": "target term" }
        ex_glossary_map = {item[source_lang]: item[target_lang] for item in existing_glossary if source_lang in item and target_lang in item}

        glossary_context = json.dumps(ex_glossary_map, ensure_ascii=False)
    else:
        existing_glossary = []
        ex_glossary_map = {}
        glossary_context = "Not Available"

    # Format input text as list separated by number tag
    enumerated_input = ""
    for i, info in enumerate(text_info_list):
        enumerated_input += f"<|{i+1}|> {info['original_text']} "

    # Load prompt template from the YAML file
    with open('prompt.yaml', 'r', encoding="utf-8") as file:
        template = yaml.safe_load(file)['prompt-template']

    ## Inject variables into the template with simple replace method
    prompt = template.replace("{glossary}", glossary_context) \
                     .replace("{target_language}", target_lang) \
                     .replace("{input}", enumerated_input)

    logger.info(f"\nPROMPT:\n{prompt}")

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=my_config
        )

        data_dict = json.loads(response.text.strip())

        translation_text = f"{data_dict['Translation']}"
        translated_map = {}

        # Define the regex pattern outside of any f-string
        # <\|(\d+)\|>  -> Matches the literal <|number|> tag
        # \s*          -> Consumes any whitespace after tag
        # (.*?)        -> Non-greedily captures the translation
        # (?=...)      -> Lookahead to stop at the next tag or end of string
        pattern = re.compile(
            r"<\|(\d+)\|>\s*(.*?)(?=<\|\d+\|>|$)", re.DOTALL
        )

        for match in pattern.finditer(translation_text):
            item_index = int(match.group(1)) - 1
            translated_text = match.group(2).strip()
            translated_map[item_index] = translated_text

        logger.info("\nTRANSLATION:")
        translation_text_list = []
        for i, info in enumerate(text_info_list):
            if i in translated_map:
                text_info_list[i]["translated_text"] = translated_map[i]
            else:
                # Raise error in case there's any missing translation. No point in letting it silently continue and replacing it with original text.
                raise Exception(
                    Fore.RED + f"Missing translation for tag <|{i+1}|>"
                )

            original_text = info["original_text"]
            translated_text = info["translated_text"]
            text_pair = f"{original_text} ==> {translated_text}"
            logger.info(f"[{model}] {text_pair}")
            translation_text_list.append(text_pair)

        with open(f"{output_dir}/translation.txt", "w", encoding="utf-8") as translation:
            translation.write("\n".join(translation_text_list))

        # Update existing glossary
        new_glossary = {item["source_term"]: item["translated_term"] for item in data_dict["Glossary"]}
        logger.info(f"\nGLOSSARY:\n")

        added_count = 0
        for source_term, target_term in new_glossary.items():
            logger.info(f"{source_term}: {target_term}")
            # Add new dict if source and target terms do not exist
            if source_term and source_term not in ex_glossary_map and target_term and target_term not in ex_glossary_map:
                # Format: {"en": "...", "es": "..."},
                new_item = {
                    source_lang: source_term,
                    target_lang: target_term
                }
                existing_glossary.append(new_item)
                added_count += 2

        for dict in existing_glossary:
            for source_term, target_term in new_glossary.items():
                # Add target term if not exist and source term exists
                if source_term and source_term in dict.values() and target_lang not in dict:
                    dict[target_lang] = target_term
                    added_count += 1
                # Add source term if not exist and target term exists
                elif target_term and target_term in dict.values() and source_lang not in dict:
                    dict[source_lang] = source_term
                    added_count += 1

        if added_count > 0:
            with open(glossary_path, "w", encoding="utf-8") as f:
                json.dump({"GLOSSARY": existing_glossary}, f, ensure_ascii=False, indent=4)
            logger.info(f"Appended {added_count} new terms to '{(glossary_path)}'")
        else:
            logger.info("No new terms found.")

    except Exception as e:
        if data_dict:
            logger.debug(f"\n{data_dict}")
        raise type(e)(Fore.RED + f"{e}")

    return text_info_list