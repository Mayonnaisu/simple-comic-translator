import os
import re
import warnings
from google import genai
from google.genai import types
from dotenv import load_dotenv

def translate_texts_with_gemini(text_info_list, target_lang, model):
    if not text_info_list:
        return text_info_list
    
    print(f"\nTranslating texts to ({target_lang.upper()}) with Gemini.")

    # Load environment variables from .env file
    load_dotenv()

    # Get the API key from the environment variables
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        raise Exception('\033[31m' + f"Failed to initialize Gemini client: {e}")
        exit()

    my_config = types.GenerateContentConfig(
        temperature=0.5,
        top_p=0.8,
    )

    enumerated_input = ""
    for i, info in enumerate(text_info_list):
        # Replace actual newlines with a space for a cleaner prompt list entry
        clean_text = info["original_text"].replace("\n", " ")
        enumerated_input += f"{i+1}. {clean_text}\n"

    # The prompt itself is a standard multiline string, no f-string syntax error here.
    prompt = f"""
Translate the following enumerated list of text items to the ISO language code '{target_lang}'.
Each item is prefixed by its number (e.g., '1. Text').
You must maintain the enumeration in your response (e.g., '1. Translated Text').
Crucially, maintain original line breaks and spacing within each item if possible, but prioritize returning only the enumerated list.
Do not add any introductory or concluding text, just the list.

Input List:
{enumerated_input}
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=my_config)
        response_text = response.text.strip()

        translated_map = {}

        # Define the regex pattern outside of any f-string
        # Pattern looks for start of line, digits, dot, space, capture the rest until newline
        pattern = re.compile(
            r"^(\d+)\.\s*(.*?)(?=\n\d+\.|\n*$)", re.DOTALL | re.MULTILINE
        )

        for match in pattern.finditer(response_text):
            item_index = int(match.group(1)) - 1
            translated_text = match.group(2).strip()
            translated_map[item_index] = translated_text

        for i in range(len(text_info_list)):
            if i in translated_map:
                text_info_list[i]["translated_text"] = translated_map[i]
            else:
                warnings.warn(
                    f"Warning: Missing translation for index {i}, using original text."
                )
                text_info_list[i]["translated_text"] = text_info_list[i][
                    "original_text"
                ]
                print(text_info_list[i])

    except Exception as e:
        raise Exception("\033[31m" + f"An error occurred during translation: {e}")

    for info in text_info_list:
        original_text = info["original_text"]
        translated_text = info["translated_text"]
        print(f"[{model}] {original_text} ==> {translated_text}")

    return text_info_list