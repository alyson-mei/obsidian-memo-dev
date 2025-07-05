"""
time.py

This module provides utilities for calculating and describing time progress
across various periods (day, week, month, season, year). It includes:

- get_days_in_month: Returns the number of days in a given month/year.
- get_season_range: Determines the start and end dates of the current meteorological season.
- get_start_of_next_year: Returns a datetime for the start of the next year.
- get_time_info: Calculates progress percentages and labels for day, week, month, season, and year.

Logging is used for observability. All calculations use the current local time.
Includes an extensive __main__ section for edge case testing and demonstration.
"""

import calendar
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union

from app.config import setup_logger

logger = setup_logger("time_service", indent=6)

def get_days_in_month(year: int, month: int) -> int:
    """
    Get the number of days in a given month of a given year.
    
    Args:
        year: The year (e.g., 2024)
        month: The month (1-12)
    
    Returns:
        The number of days in the specified month
        
    Raises:
        ValueError: If month is not in range 1-12
        
    Examples:
        >>> get_days_in_month(2024, 2)  # Leap year February
        29
        >>> get_days_in_month(2023, 2)  # Non-leap year February  
        28
        >>> get_days_in_month(2023, 4)  # April
        30
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    return calendar.monthrange(year, month)[1]


def get_season_range(now: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates of the current season.
    
    Seasons are defined as:
    - Winter: December 1 - February 28/29
    - Spring: March 1 - May 31
    - Summer: June 1 - August 31
    - Autumn: September 1 - November 30
    
    Args:
        now: The current date and time
    
    Returns:
        A tuple containing (season_start, season_end) as datetime objects
        
    Examples:
        >>> import datetime
        >>> get_season_range(datetime.datetime(2024, 1, 15))
        (datetime.datetime(2023, 12, 1, 0, 0), datetime.datetime(2024, 3, 1, 0, 0))
        >>> get_season_range(datetime.datetime(2024, 7, 15))
        (datetime.datetime(2024, 6, 1, 0, 0), datetime.datetime(2024, 9, 1, 0, 0))
    """
    season_start_month = (
        12 if now.month in [12, 1, 2] else
        3 if now.month in [3, 4, 5] else
        6 if now.month in [6, 7, 8] else
        9
    )
    
    # Handle year transition for winter
    if season_start_month == 12:
        season_start = now.replace(month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month in [1, 2]:  # We're in Jan/Feb, so winter started last year
            season_start = season_start.replace(year=now.year - 1)
        season_end = now.replace(year=season_start.year + 1, month=3, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        season_start = now.replace(month=season_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        season_end = season_start.replace(month=season_start_month + 3, day=1)
    
    return season_start, season_end


def get_start_of_next_year(now: datetime) -> datetime:
    """
    Get the start of the next year (January 1st at midnight).
    
    Args:
        now: The current date and time
    
    Returns:
        A datetime object representing January 1st at 00:00:00 of the next year
        
    Examples:
        >>> import datetime
        >>> get_start_of_next_year(datetime.datetime(2024, 6, 15, 14, 30))
        datetime.datetime(2025, 1, 1, 0, 0)
    """
    return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def get_time_info() -> Dict[str, Union[str, float]]:
    """
    Calculate the progress of the current day, week, month, season, and year.
    
    This function computes how much of each time period has elapsed as a percentage,
    along with descriptive labels for the current time periods.
    
    Returns:
        A dictionary containing:
        - day: Day name (e.g., "Monday")
        - month: Month name (e.g., "January") 
        - week: Week description (e.g., "Week 25")
        - season: Season name ("Winter", "Spring", "Summer", or "Autumn")
        - year: Year description (e.g., "Year 2024")
        - datetime: Formatted current datetime string
        - percentage_day: Percentage of current day completed (0.0-100.0)
        - percentage_week: Percentage of current week completed (0.0-100.0)
        - percentage_month: Percentage of current month completed (0.0-100.0)
        - percentage_season: Percentage of current season completed (0.0-100.0)
        - percentage_year: Percentage of current year completed (0.0-100.0)
        
    Examples:
        >>> info = get_time_info()
        >>> print(f"Today is {info['day']} and we're {info['percentage_day']:.1f}% through the day")
        Today is Sunday and we're 45.2% through the day
        
    Note:
        - Week starts on Monday (ISO 8601 standard)
        - Seasons are meteorological (Dec-Feb, Mar-May, Jun-Aug, Sep-Nov)
        - All percentages are calculated based on elapsed minutes
    """
    logger.info("Calculating time progress percentages")
    now = datetime.now()
    day = now.strftime("%A")
    month = now.strftime("%B")
    week = f"Week {now.isocalendar()[1]}"
    season = (
        "Winter" if now.month in [12, 1, 2] else
        "Spring" if now.month in [3, 4, 5] else
        "Summer" if now.month in [6, 7, 8] else
        "Autumn"
    )

    # Day progress
    minutes_today = now.hour * 60 + now.minute
    percentage_day = (minutes_today / (24 * 60)) * 100

    # Week progress (ISO week starting Monday)
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
    minutes_since_start = int((now - start_of_week).total_seconds() // 60)
    percentage_week = (minutes_since_start / (7 * 24 * 60)) * 100

    # Month progress
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    minutes_this_month = int((now - start_of_month).total_seconds() // 60)
    days_in_month = get_days_in_month(now.year, now.month)
    percentage_month = (minutes_this_month / (days_in_month * 24 * 60)) * 100

    # Season progress
    start_of_season, end_of_season = get_season_range(now)
    minutes_this_season = int((now - start_of_season).total_seconds() // 60)
    total_minutes_in_season = int((end_of_season - start_of_season).total_seconds() // 60)
    percentage_season = (minutes_this_season / total_minutes_in_season) * 100

    # Year progress
    year = f"Year {now.year}"
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_year = get_start_of_next_year(now)
    minutes_this_year = int((now - start_of_year).total_seconds() // 60)
    total_minutes_in_year = int((end_of_year - start_of_year).total_seconds() // 60)
    percentage_year = (minutes_this_year / total_minutes_in_year) * 100

    logger.info("Completed calculations")

    return {
        "day": day,
        "month": month,
        "week": week,
        "season": season,
        "year": year,
        "datetime": now.strftime("%A, %d %B %Y | %H:%M"),
        "percentage_day": percentage_day,
        "percentage_week": percentage_week,
        "percentage_month": percentage_month,
        "percentage_season": percentage_season,
        "percentage_year": percentage_year,
    }


# Example usage and testing
if __name__ == "__main__":
   # Test current time
   info = get_time_info()
   print("Current Time Information:")
   print(f"📅 {info['datetime']}")
   print(f"📊 Day: {info['percentage_day']:.1f}% complete")
   print(f"📊 Week: {info['percentage_week']:.1f}% complete") 
   print(f"📊 Month: {info['percentage_month']:.1f}% complete")
   print(f"📊 Season: {info['percentage_season']:.1f}% complete")
   print(f"📊 Year: {info['percentage_year']:.1f}% complete")
   
   print("\n" + "="*50)
   print("Testing Edge Cases:")
   
   # Edge case 1: New Year's Day
   print("\n1. New Year's Day (January 1st):")
   test_date = datetime(2024, 1, 1, 0, 1)
   print(f"   Date: {test_date}")
   start_season, end_season = get_season_range(test_date)
   print(f"   Season range: {start_season} to {end_season}")
   
   # Edge case 2: Leap year February 29th
   print("\n2. Leap Year - February 29th:")
   test_date = datetime(2024, 2, 29, 12, 0)
   print(f"   Date: {test_date}")
   print(f"   Days in month: {get_days_in_month(2024, 2)}")
   
   # Edge case 3: Non-leap year February
   print("\n3. Non-Leap Year February:")
   print(f"   Days in Feb 2023: {get_days_in_month(2023, 2)}")
   print(f"   Days in Feb 2024: {get_days_in_month(2024, 2)}")
   
   # Edge case 4: December 31st (end of year)
   print("\n4. New Year's Eve (December 31st):")
   test_date = datetime(2024, 12, 31, 23, 59)
   print(f"   Date: {test_date}")
   print(f"   Next year starts: {get_start_of_next_year(test_date)}")
   
   # Edge case 5: Season transitions
   print("\n5. Season Transitions:")
   transitions = [
       datetime(2024, 2, 28, 23, 59),  # End of winter
       datetime(2024, 3, 1, 0, 0),     # Start of spring
       datetime(2024, 11, 30, 23, 59), # End of autumn
       datetime(2024, 12, 1, 0, 0),    # Start of winter
   ]
   for date in transitions:
       start_season, end_season = get_season_range(date)
       print(f"   {date} -> Season: {start_season.strftime('%b %d')} to {end_season.strftime('%b %d')}")
   
   # Edge case 6: Week boundaries (Monday transitions)
   print("\n6. Week Boundaries (ISO weeks):")
   test_dates = [
       datetime(2024, 6, 23, 23, 59),  # Sunday night
       datetime(2024, 6, 24, 0, 0),    # Monday morning
   ]
   for date in test_dates:
       iso_week = date.isocalendar()[1]
       print(f"   {date.strftime('%A %b %d, %H:%M')} -> Week {iso_week}")
   
   # Edge case 7: Midnight transitions
   print("\n7. Midnight Transitions:")
   midnight = datetime(2024, 6, 22, 0, 0)
   almost_midnight = datetime(2024, 6, 21, 23, 59)
   print(f"   {almost_midnight}: Day {almost_midnight.hour * 60 + almost_midnight.minute} minutes")
   print(f"   {midnight}: Day {midnight.hour * 60 + midnight.minute} minutes")
   
   # Edge case 8: Month boundaries with different lengths
   print("\n8. Month Length Variations:")
   months_to_test = [
       (2024, 1, "January - 31 days"),
       (2024, 2, "February - 29 days (leap)"),
       (2024, 4, "April - 30 days"),
       (2023, 2, "February - 28 days (non-leap)"),
   ]
   for year, month, desc in months_to_test:
       days = get_days_in_month(year, month)
       print(f"   {desc}: {days} days")
   
   # Edge case 9: Year boundaries across centuries
   print("\n9. Century/Millennium Boundaries:")
   century_dates = [
       datetime(1999, 12, 31, 23, 59),
       datetime(2000, 1, 1, 0, 0),
       datetime(2099, 12, 31, 23, 59),
       datetime(2100, 1, 1, 0, 0),
   ]
   for date in century_dates:
       next_year = get_start_of_next_year(date)
       print(f"   {date.year} -> Next year: {next_year.year}")
   
   # Edge case 10: Invalid month handling
   print("\n10. Error Handling Test:")
   try:
       result = get_days_in_month(2024, 13)  # Invalid month
       print(f"   Month 13: {result} days")
   except ValueError as e:
       print(f"   ✓ Caught expected error: {e}")
   
   try:
       result = get_days_in_month(2024, 0)  # Invalid month
       print(f"   Month 0: {result} days")
   except ValueError as e:
       print(f"   ✓ Caught expected error: {e}")