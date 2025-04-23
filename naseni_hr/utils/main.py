from datetime import date
from dateutil.relativedelta import relativedelta


def safe_retirement_date(date_of_birth, date_of_joining):
    """Get safe minimum between the date_of_birth and date_of_joining"""
    if not date_of_birth and not date_of_joining:
        return None  # Both are None, return None
    if not date_of_birth:
        return date_of_joining + relativedelta(years=35)
    if not date_of_joining:
        return date_of_birth + relativedelta(years=60)
    return min(
        date_of_birth + relativedelta(years=60),
        date_of_joining + relativedelta(years=35),
    )


def has_three_months_to_retirement(date_of_birth: date, date_of_joining: date) -> bool:
    """Check if the retirement date is due in 3 months.

    Params
    ------
    date_of_birth (date): employee's date of birth
    date_of_joining (date): date employee joined the organization

    Returns
    -------
    (bool): returns True or False
    """
    if not date_of_birth and not date_of_joining:
        return False
    if not date_of_birth:
        ret
    td = date.today()
    date_of_retirement = safe_retirement_date(date_of_birth, date_of_joining)
    if not date_of_retirement:
        return False
    if td == date_of_retirement - relativedelta(months=3):
        return True
    return False
