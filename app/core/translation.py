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

init(autoreset=True)

def translate_texts_with_gemini(text_info_list: list[dict], target_lang: str, gemini: list[str|float], previous_dir: str, output_dir: str, log_level: str):
    '''
    Translate all texts from one chapter and summarize them with Gemini
    '''
    if not text_info_list:
        return text_info_list
    
    logger.info(f"\nTranslating texts to ({target_lang.upper()}) with Gemini.")

    model, temperature, top_p, max_out_tokens = gemini

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
            "Translation": {"type": "string", "description": "The full translated text."},
            "Summary": {"type": "string", "description": "A concise summary of the translated text."}
        },
        "required": ["Translation", "Summary"]
    }

    my_config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_out_tokens,
        response_mime_type="application/json",
        response_schema=response_schema
    )

    # Load previous summary file
    previous_summary_path = f"{previous_dir}/summary.txt"
    if os.path.exists(previous_summary_path):
        prev_summary_list = []
        with open(previous_summary_path, "r", encoding="utf-8") as summary:
            for line in summary:
                prev_summary_list.append(line)

        previous_summary = "\n".join(prev_summary_list)
    else:
        previous_summary = "NOT AVAILABLE"

    # Format input text as list separated by number tag
    enumerated_input = ""
    for i, info in enumerate(text_info_list):
        enumerated_input += f"<|{i+1}|> {info["original_text"]} "

    # Load prompt template from the YAML file
    with open('prompt.yaml', 'r', encoding="utf-8") as file:
        template = yaml.safe_load(file)['prompt-template']

    ## Inject variables into the template with simple replace method
    prompt = template.replace("{previous_summary}", previous_summary).replace("{target_language}", target_lang).replace("{input}", enumerated_input)

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
            logger.info(f"[{model}] {original_text} ==> {translated_text}")
            translation_text_list.append(f"{original_text} ==> {translated_text}")

        with open(f"{output_dir}/translation.txt", "w", encoding="utf-8") as translation:
            translation.write("\n".join(translation_text_list))

        summary_text = f"""{data_dict['Summary']}"""

        logger.info(f"\nSUMMARY:\n{summary_text}\n")
        with open(f"{output_dir}/summary.txt", "w", encoding="utf-8") as summary:
            summary.write(summary_text)

    except Exception as e:
        if data_dict:
            logger.debug(f"\n{data_dict}")
        raise Exception(Fore.RED + f"An error occurred during translation: {e}")

    return text_info_list