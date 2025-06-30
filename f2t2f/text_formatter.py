import json

F2T2F_MARKER = "f2t2f_folder_structure_v1"

def serialize_to_json(folder_data: dict) -> str:
    """
    Serializes the folder structure dictionary to a JSON string with a marker.
    """
    wrapper = {
        "type": F2T2F_MARKER,
        "data": folder_data
    }
    return json.dumps(wrapper, indent=2)

def deserialize_from_json(json_string: str) -> dict:
    """
    Deserializes a JSON string back into a folder structure dictionary,
    validating the format and providing detailed error messages.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON syntax: {e.msg} at line {e.lineno}, column {e.colno}."
        raise ValueError(error_message)

    if not isinstance(data, dict):
        raise ValueError("The provided text is not a valid JSON object.")
        
    if data.get("type") != F2T2F_MARKER:
        raise ValueError(f"Not a valid f2t2f structure. The 'type' key must be '{F2T2F_MARKER}'.")
    
    if "data" not in data:
        raise ValueError("Not a valid f2t2f structure. The top-level 'data' key is missing.")

    return data["data"]