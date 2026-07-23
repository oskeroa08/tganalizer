
def check_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return False  # If no keywords, allow nothing
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False


def check_priority(text: str, priority_keywords: list[str]) -> tuple[bool, str]:
    text_lower = text.lower()
    for keyword in priority_keywords:
        if keyword.lower() in text_lower:
            return True, keyword
    return False, ""


def process_message(text: str, config: dict) -> dict:
    result = {
        "should_send": False,
        "is_priority": False,
        "priority_keyword": "",
        "filtered": False
    }

    # Check priority first
    is_priority, priority_keyword = check_priority(text, config["filters"]["priority_keywords"])
    result["is_priority"] = is_priority
    result["priority_keyword"] = priority_keyword

    # If priority, send immediately
    if is_priority:
        result["should_send"] = True
        return result

    # Check regular keywords
    if check_keywords(text, config["filters"]["keywords"]):
        result["should_send"] = True

    return result

