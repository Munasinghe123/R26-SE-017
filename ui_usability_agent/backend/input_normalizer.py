def normalize_input(raw_input: dict) -> dict:
    """
    Cleans whatever comes from the other agents.
    Handles missing fields, empty lists, malformed keys, and None values.
    """
    raw_input = raw_input or {}

    return{
        "project_name" : raw_input.get("project_name") or "Unnamed System",
        "domain": raw_input.get("domain") or "General",
        "functional_requirements": raw_input.get("functional_requirements") or raw_input.get("fr") or [],
        "non_functional_requirements": raw_input.get("non_functional_requirements") or raw_input.get("nfr") or [],
        "use_cases": raw_input.get("use_cases") or [],
        "design_artifacts": raw_input.get("design_artifacts") or {},
        "user_flows": raw_input.get("user_flows") or [],
    }