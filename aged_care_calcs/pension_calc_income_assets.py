from datetime import date

# Constants (as of Jan 2025) – adjust if rules change
MAX_PENSION_SINGLE = 1116.30  # per fortnight (base rate + supplements)
INCOME_FREE_AREA_SINGLE = 204.00  # per fortnight
INCOME_TAPER = 0.50  # reduction per $1 over free area

ASSETS_THRESHOLD_HOME_SINGLE = 314000  # homeowner, single
ASSETS_THRESHOLD_NONHOME_SINGLE = 566000  # non-homeowner, single
ASSETS_TAPER = 3.00  # reduction per $1000 over threshold (per fortnight)

def calculate_income_test(income):
    """
    Calculate pension based on income test.
    """
    if income <= INCOME_FREE_AREA_SINGLE:
        return MAX_PENSION_SINGLE
    excess = income - INCOME_FREE_AREA_SINGLE
    reduction = excess * INCOME_TAPER
    return max(0, MAX_PENSION_SINGLE - reduction)

def calculate_assets_test(assets, homeowner=True):
    """
    Calculate pension based on assets test.
    """
    threshold = ASSETS_THRESHOLD_HOME_SINGLE if homeowner else ASSETS_THRESHOLD_NONHOME_SINGLE
    if assets <= threshold:
        return MAX_PENSION_SINGLE
    excess = assets - threshold
    reduction = (excess / 1000) * ASSETS_TAPER
    return max(0, MAX_PENSION_SINGLE - reduction)

def calculate_age_pension(income, assets, homeowner=True)->float:
    """
    Returns the pension payable per fortnight.
    Takes other income as income
    """
    pension_income_test = calculate_income_test(income)
    pension_assets_test = calculate_assets_test(assets, homeowner)
    pension = min(pension_income_test, pension_assets_test)
    return pension

# Example usage:
if __name__ == "__main__":
    # Example: single, homeowner, $300 fortnightly income, $350,000 assets
    income = 210.00       # per fortnight
    assets = 180000.00    # total assets
    homeowner = True

    pension = calculate_age_pension(income, assets, homeowner)
    print(f"Age Pension payable: ${pension:.2f} per fortnight (as of {date.today()})")
