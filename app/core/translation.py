import os
import re
import json
import warnings
from google import genai
from google.genai import types
from dotenv import load_dotenv

def translate_texts_with_gemini(text_info_list, target_lang, model, output_dir, prev_summary_path):
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

    response_schema={
        "type": "object",
        "properties": {
            "Translation": {"type": "string", "description": "The full translated text."},
            "Summary": {"type": "string", "description": "A concise summary of the translated text."}
        },
        "required": ["Translation", "Summary"]
    }

    my_config = types.GenerateContentConfig(
        temperature=0.5,
        top_p=0.8,
        response_mime_type="application/json",
        response_schema=response_schema
    )

    previous_summary_path = f"{prev_summary_path}/summary.txt"
    if os.path.exists(previous_summary_path):
        prev_summary_list = []
        with open(previous_summary_path, "r", encoding="utf-8") as summary:
            for line in summary:
                prev_summary_list.append(line)

        previous_summary = "\n".join(prev_summary_list)
    else:
        previous_summary = "NOT AVAILABLE"

    enumerated_input = ""
    for i, info in enumerate(text_info_list):
        # Replace actual newlines with a space for a cleaner prompt list entry
        clean_text = info["original_text"].replace("\n", " ")
        enumerated_input += f"{i+1}. {clean_text}\n"

    # The prompt itself is a standard multiline string, no f-string syntax error here.
    prompt = f"""
Summary of Previous Translation:
{previous_summary}

Task 1 (Translation):
* Translate the following enumerated list of text items to the ISO language code '{target_lang}'.
* Each item is prefixed by its number (e.g., '1. Text').
* You must maintain the enumeration in your response (e.g., '1. Translated Text').
* Crucially, maintain original line breaks and spacing within each item.
* Do not add any introductory or concluding text, just the list.
* Use the Summary of Previous Translation above as additional context if available.

Task 2 (Summarization):
* Please provide a concise summary of the translation in {target_lang}.
* Do not include the enumeration.
* Do not add any introductory or concluding text, just the summary.

Output Format:
Format your response strictly as a JSON object matching the requested schema.

Input List:
{enumerated_input}
"""

    print(f"\nPROMPT:\n{prompt}")

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
        # Pattern looks for start of line, digits, dot, space, capture the rest until newline
        pattern = re.compile(
            r"^(\d+)\.\s*(.*?)(?=\n\d+\.|\n*$)", re.DOTALL | re.MULTILINE
        )

        for match in pattern.finditer(translation_text):
            item_index = int(match.group(1)) - 1
            translated_text = match.group(2).strip()
            translated_map[item_index] = translated_text

        print("\nTRANSLATION:")
        for i, info in enumerate(text_info_list):
            if i in translated_map:
                text_info_list[i]["translated_text"] = translated_map[i]
            else:
                warnings.warn(
                    f"Warning: Missing translation for index {i}, using original text."
                )
                text_info_list[i]["translated_text"] = text_info_list[i][
                    "original_text"
                ]

            original_text = info["original_text"]
            translated_text = info["translated_text"]
            print(f"[{model}] {original_text} ==> {translated_text}")
            with open(f"{output_dir}/translation.txt", "a", encoding="utf-8") as translation:
                translation.write(f"{original_text} ==> {translated_text}\n")

        summary_text = f"""{data_dict['Summary']}"""

        print(f"\nSUMMARY:\n{summary_text}\n")
        with open(f"{output_dir}/summary.txt", "w", encoding="utf-8") as summary:
            summary.write(summary_text)

    except Exception as e:
        raise Exception("\033[31m" + f"An error occurred during translation: {e}")

    return text_info_list