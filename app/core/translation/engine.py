import os
import re
import json
import yaml
import litellm
from loguru import logger
from dotenv import load_dotenv
from colorama import Fore, Style, init

from app.core.translation.glossary import load_glossary, update_glossary


init(autoreset=True)

def translate_texts_and_build_glossary(text_info_list: list[dict], languages: list[str], translator: list[str|float], glossary_path: str, memory: list[object|bool], log_level: str):
    '''
    Translate all texts from one chapter and build glossary with LiteLLM
    '''
    if not text_info_list:
        return text_info_list

    source_lang, target_lang = languages
    provider, model, base_url, temperature, top_p, max_out_tokens, timeout = translator
    tm, overwrite_memory = memory

    logger.info(f"\nTranslating texts to ({target_lang.upper()}) with {provider.upper()}...")

    # Define placeholder to prevent error when logging exception
    data_dict = "data_dict"

    # Load existing glossary file
    existing_glossary, ex_glossary_map, glossary_context = load_glossary(glossary_path, source_lang, target_lang)

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

    # Load environment variables from .env file
    load_dotenv()

    # Get the API key from the environment variables
    api_keys = os.getenv("API_KEYS", "").split(",")

    # Create a model list for the Router
    # Each entry is a "deployment" the router can choose from
    model_list = [
        {
            "model_name": "multi-keys", # Internal alias for the router
            "litellm_params": {
                "model": f"{provider}/{model}",
                "base_url": base_url,
                "api_key": key,
                "temperature": temperature,
                "top_p": top_p,
                "timeout": timeout,
                "max_tokens": max_out_tokens,
            },
        }
        for key in api_keys
    ]

    # Initialize the Router with a rotation strategy
    router = litellm.Router(
        model_list=model_list,
        routing_strategy="simple-shuffle",
        set_verbose=False
    )

    messages = [
        {"role": "system", "content": "You are a professional translator and terminologist."},
        {"role": "user", "content": f"{prompt}"}
    ]

    json_schema = {
        "name": "result",
        "strict": True,
        "schema": {
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
    }

    try:
        response = router.completion(
            model="multi-keys",
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": json_schema
            }
        )

        data_dict = json.loads(response.choices[0].message.content)

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
        for i, info in enumerate(text_info_list):
            if i in translated_map:
                text_info_list[i]["translated_text"] = translated_map[i]
            else:
                # Raise error in case there's any missing translation.
                # No point in letting it silently continue and replacing it with original text.
                raise Exception(
                    Fore.RED + f"Missing translation for tag <|{i+1}|>"
                )

            original_text = info["original_text"]
            translated_text = info["translated_text"]
            logger.info(f"[{model}] {original_text} ▶▶▶ {translated_text}")
            tm.add_translation(original_text, source_lang, translated_text, target_lang, overwrite_memory)

        # Update existing glossary
        update_glossary(data_dict, existing_glossary, ex_glossary_map, glossary_path, source_lang, target_lang)

    except Exception as e:
        if data_dict:
            logger.debug(f"\n{data_dict}")
        raise type(e)(Fore.RED + f"{e}")

    return text_info_list