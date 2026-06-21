import re

def parse_filename(filename: str) -> dict:
    """
    Parses an anime filename to extract title, episode, and quality.
    
    Examples:
        "[SubGroup] One Piece - 1010 [1080p].mkv" -> {"title": "One Piece", "episode": "1010", "quality": "1080p"}
        "Naruto Shippuden - 500.mp4" -> {"title": "Naruto Shippuden", "episode": "500", "quality": "HD"}
    """
    result = {
        "title": None,
        "episode": None,
        "quality": "HD"
    }
    
    # Clean brackets content usually contains subgroup or hashes
    clean_name = re.sub(r'\[.*?\]', '', filename).strip()
    # Remove file extension
    clean_name = re.sub(r'\.\w+$', '', clean_name).strip()
    
    # Pattern: Title - Episode
    # This is a simple heuristic.
    match = re.search(r'(.+?)\s*-\s*(\d+(?:\.\d+)?)', clean_name)
    if match:
        result["title"] = match.group(1).strip()
        result["episode"] = match.group(2).strip()
    else:
        # Try to find just the last number as episode
        match = re.search(r'(.+?)\s+(\d+(?:\.\d+)?)', clean_name)
        if match:
            result["title"] = match.group(1).strip()
            result["episode"] = match.group(2).strip()

    # Detect Quality
    if "1080" in filename:
        result["quality"] = "1080p"
    elif "720" in filename:
        result["quality"] = "720p"
    elif "480" in filename:
        result["quality"] = "480p"
        
    return result
