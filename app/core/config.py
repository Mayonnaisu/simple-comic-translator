import json

def load_config(config_file_path):
    """
    Loads configuration settings from a JSON file.
    """
    try:
        with open(config_file_path, 'r') as config_file:
            config_data = json.load(config_file)
        return config_data
    except FileNotFoundError:
        raise FileNotFoundError("\033[31m" + f"Error: Configuration file '{config_file_path}' not found!")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Error: Invalid JSON format in '{config_file_path}'!")


