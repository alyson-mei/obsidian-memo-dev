from app.config import setup_logger

logger = setup_logger("part_of_day_service", indent=6)

def get_part_of_day_description(hour: int) -> str:
    """
    Return a human-readable description for the part of day based on the hour.

    Args:
        hour (int): The hour of the day (0-23).

    Returns:
        str: Description of the part of day.
    """
    logger.info(f"Getting part of day description for hour: {hour}")
    if 5 <= hour < 8:
        return "early morning"
    elif 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 13:
        return "noon"
    elif 13 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 18:
        return "early evening"
    elif 18 <= hour < 21:
        return "evening"
    elif 21 <= hour < 23:
        return "late evening"
    else:
        return "night"
    
if __name__ == "__main__":
    from datetime import datetime
    print(get_part_of_day_description(datetime.now().hour))