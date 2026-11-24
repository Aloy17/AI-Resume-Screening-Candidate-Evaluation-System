
import re
from datetime import date, datetime


# ==========================================================
# 1. DATE PARSING
# ==========================================================

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_date(value: str):
    """
    Convert supported date formats into a date object.

    Supported examples:
        March 2024
        Mar 2024
        03/2024
        2024-03
        18/03/2024
        2024-03-18
    """

    if not isinstance(value, str):
        return None

    value = value.strip()

    formats = [
        "%B %Y",
        "%b %Y",
        "%m/%Y",
        "%Y-%m",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(value, fmt)

            return date(
                parsed.year,
                parsed.month,
                1
            )

        except ValueError:
            continue

    # Handle month-year strings without a space.
    match = re.fullmatch(
        r"([A-Za-z]+)[,\s]+(\d{4})",
        value
    )

    if match:

        month_name = match.group(1).lower()
        year = int(match.group(2))

        month = MONTHS.get(month_name)

        if month:
            return date(year, month, 1)

    return None


# ==========================================================
# 2. CALCULATE DURATION
# ==========================================================

def calculate_duration(
    start_date: date,
    end_date: date
) -> float:
    """
    Calculate duration in years using calendar months.
    """

    if not start_date or not end_date:
        return 0.0

    if end_date < start_date:
        return 0.0

    months = (
        (end_date.year - start_date.year) * 12
        +
        (end_date.month - start_date.month)
        + 1
    )

    return round(months / 12, 2)


# ==========================================================
# 3. EXTRACT DURATION FROM EXPERIENCE ENTRY
# ==========================================================

def extract_experience_duration(experience: dict) -> float:
    """
    Extract duration from a structured experience entry.

    Expected fields:
        start_date
        end_date

    Also supports:
        duration

    The experience parser may use different field names,
    so those are checked as well.
    """

    if not isinstance(experience, dict):
        return 0.0

    duration = experience.get("duration")

    if duration:

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(years?|yrs?)",
            str(duration),
            re.IGNORECASE
        )

        if match:
            return float(match.group(1))

    start_value = (
        experience.get("start_date")
        or experience.get("start")
    )

    end_value = (
        experience.get("end_date")
        or experience.get("end")
    )

    if not start_value or not end_value:
        return 0.0

    start_date = parse_date(str(start_value))

    if str(end_value).strip().lower() in [
        "present",
        "current",
        "currently",
        "till date",
    ]:

        today = date.today()

        end_date = date(
            today.year,
            today.month,
            1
        )

    else:

        end_date = parse_date(str(end_value))

    if not start_date or not end_date:
        return 0.0

    return calculate_duration(
        start_date,
        end_date
    )


# ==========================================================
# 4. CALCULATE TOTAL EXPERIENCE
# ==========================================================

def calculate_total_experience(experiences: list) -> dict:
    """
    Calculate total work experience.

    Internship and full-time experience are reported separately.

    Overlapping employment periods are merged to avoid
    counting the same calendar period twice.
    """

    if not isinstance(experiences, list):
        raise TypeError("Experiences must be provided as a list.")

    periods = []

    internship_periods = []
    other_periods = []

    today = date.today()

    for experience in experiences:

        if not isinstance(experience, dict):
            continue

        start_value = (
            experience.get("start_date")
            or experience.get("start")
        )

        end_value = (
            experience.get("end_date")
            or experience.get("end")
        )

        if not start_value or not end_value:
            continue

        start_date = parse_date(str(start_value))

        if str(end_value).strip().lower() in [
            "present",
            "current",
            "currently",
            "till date",
        ]:

            end_date = date(today.year, today.month, 1)

        else:

            end_date = parse_date(str(end_value))

        if not start_date or not end_date:
            continue

        if end_date < start_date:
            continue

        experience_type = str(
            experience.get("type")
            or experience.get("employment_type")
            or experience.get("position", "")
        ).lower()

        is_internship = "intern" in experience_type

        period = (start_date, end_date)

        if is_internship:
            internship_periods.append(period)

        else:
            other_periods.append(period)

    def merge_periods(period_list):
        """Merge overlapping calendar-month periods."""

        if not period_list:
            return []

        period_list = sorted(period_list)

        merged = []

        current_start, current_end = period_list[0]

        for next_start, next_end in period_list[1:]:

            if next_start <= current_end:

                if next_end > current_end:
                    current_end = next_end

            else:

                merged.append(
                    (current_start, current_end)
                )

                current_start = next_start
                current_end = next_end

        merged.append(
            (current_start, current_end)
        )

        return merged

    def total_months(period_list):

        merged = merge_periods(period_list)

        months = 0

        for start, end in merged:

            months += (
                (end.year - start.year) * 12
                +
                (end.month - start.month)
                + 1
            )

        return months

    professional_months = total_months(
        other_periods
    )

    internship_months = total_months(
        internship_periods
    )

    return {
        "professional_experience_years": round(
            professional_months / 12, 2
        ),

        "internship_experience_years": round(
            internship_months / 12, 2
        ),

        "professional_experience_months": professional_months,

        "internship_experience_months": internship_months,

        "experience_periods": len(periods),
    }


# ==========================================================
# 5. EXTRACT REQUIRED EXPERIENCE FROM JD
# ==========================================================

def get_required_experience(jd_information: dict) -> dict:
    """
    Read the structured experience requirement
    extracted from the job description.
    """

    if not isinstance(jd_information, dict):
        raise TypeError("JD information must be a dictionary.")

    experience = jd_information.get(
        "experience_required",
        {}
    )

    if not isinstance(experience, dict):
        return {
            "minimum": None,
            "maximum": None,
            "unit": "years",
        }

    return {
        "minimum": experience.get("minimum"),
        "maximum": experience.get("maximum"),
        "unit": experience.get("unit", "years"),
    }


# ==========================================================
# 6. EVALUATE EXPERIENCE MATCH
# ==========================================================

def evaluate_experience_match(
    resume_information: dict,
    jd_information: dict
) -> dict:
    """
    Compare candidate professional experience
    against the job's minimum experience requirement.

    Internships are reported separately and are not
    automatically counted as professional experience.
    """

    if not isinstance(resume_information, dict):
        raise TypeError("Resume information must be a dictionary.")

    if not isinstance(jd_information, dict):
        raise TypeError("JD information must be a dictionary.")

    experiences = resume_information.get(
        "experience",
        []
    )

    if not isinstance(experiences, list):
        experiences = []

    candidate_experience = calculate_total_experience(
        experiences
    )

    required_experience = get_required_experience(
        jd_information
    )

    candidate_years = candidate_experience[
        "professional_experience_years"
    ]

    minimum_required = required_experience["minimum"]

    maximum_required = required_experience["maximum"]

    if minimum_required is None:

        status = "requirement_not_specified"
        match_percentage = None
        meets_requirement = None

    else:

        minimum_required = float(minimum_required)

        if minimum_required <= 0:

            status = "no_minimum_experience_required"
            match_percentage = 100.0
            meets_requirement = True

        else:

            match_percentage = round(
                min(
                    candidate_years / minimum_required,
                    1.0
                ) * 100,
                2
            )

            meets_requirement = (
                candidate_years >= minimum_required
            )

            if meets_requirement:
                status = "meets_minimum_requirement"

            else:
                status = "below_minimum_requirement"

    if maximum_required is not None:

        exceeds_preferred_range = (
            candidate_years > float(maximum_required)
        )

    else:

        exceeds_preferred_range = None

    return {

        "candidate_experience": candidate_experience,

        "required_experience": required_experience,

        "experience_match_percentage": match_percentage,

        "meets_minimum_requirement": meets_requirement,

        "exceeds_preferred_range": exceeds_preferred_range,

        "status": status,
    }
