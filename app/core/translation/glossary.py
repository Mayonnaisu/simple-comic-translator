import os
import json
from loguru import logger

def load_glossary(glossary_path: str, source_lang: str, target_lang: str):

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

    return existing_glossary, ex_glossary_map, glossary_context


def update_glossary(data_dict: dict, existing_glossary: list, ex_glossary_map: dict, glossary_path: str, source_lang: str, target_lang: str):

    new_glossary = {item["source_term"]: item["translated_term"] for item in data_dict["Glossary"]}
    logger.info(f"\nGLOSSARY:")

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
        logger.info(f"Appended {added_count} new terms to '{glossary_path}'")
    else:
        logger.info("No new terms found.")