DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "amount": {"type": "number"},
                    "description": {"type": "string"},
                    "date": {"type": "string"}
                },
                "required": ["category", "amount", "description", "date"],
                "additionalProperties": False
            }
        },
        "summary": {
            "type": "string"
        }
    },
    "required": ["items", "summary"],
    "additionalProperties": False
}