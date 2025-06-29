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
    validating the format.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format.")

    if not isinstance(data, dict) or data.get("type") != F2T2F_MARKER:
        raise ValueError("JSON is not a valid f2t2f folder structure format.")
    
    if "data" not in data:
        raise ValueError("Invalid f2t2f format: 'data' key is missing.")

    return data["data"]