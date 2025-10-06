from datetime import date

# Constants (Jan 2025, approximate — check Services Australia updates)
BASIC_DAILY_FEE = 61.96  # per day
INCOME_FREE_AREA_SINGLE = 34762  # per year

ASSET_FREE_AREA_SINGLE = 197735  # for homeowners
ASSET_FREE_AREA_NONHOME = 214956  # for non-homeowners


INCOME_RATE = 0.50  # 50% of income above threshold
ASSET_RATE = 0.175  # 17.5% annualised (per $1 of excess assets)

# 0% of her assets below $63,000
# 17.5% of her assets in excess of $63,000 up to $210,555.20
# 1% of her assets in excess of $210,555.20 up to $505,665.60
#  2% of her assets in excess of $505,665.60



ANNUAL_CAP = 32718.57
LIFETIME_CAP = 78524.69

MAX_ACCOM_SUPP = 70.94 #maximum accommodation supplement 

def asset_test(assets: float, homeowner: bool) -> float:
    """
    Calculate annual asset-tested contribution for Means Tested Care Fee.
    Thresholds/rates are as at 1 July 2025.
    """

    print(f"asset_test: { assets } , is home owner:{ homeowner}")
    contribution = 0.0

    # Tier 1
    if assets > 61_500:
        tier_amount = min(assets, 206_663.20) - 61_500
        contribution += 0.175 * tier_amount

    # Tier 2
    if assets > 206_663.20:
        tier_amount = min(assets, 496_989.60) - 206_663.20
        contribution += 0.01 * tier_amount

    # Tier 3
    if assets > 496_989.60:
        tier_amount = assets - 496_989.60
        contribution += 0.02 * tier_amount

    return contribution


def income_test(income: float, is_single: bool = True) -> float:
    """
    Calculate annual income-tested contribution for Means Tested Care Fee.
    Thresholds/rates are as at 1 July 2025.
    """

    print(f"income_test: {income}, is_single:{is_single}")

    if is_single:
        free_area = 34_005.40
    else:
        free_area = 25_984.40  # per person in a couple

    contribution = 0.0
    excess = max(0, income - free_area)

    # Tier 1
    tier_cap = 27_611.65
    tier_amount = min(excess, tier_cap)
    contribution += 0.50 * tier_amount
    excess -= tier_amount

    # Tier 2
    if excess > 0:
        tier_amount = min(excess, tier_cap)
        contribution += 0.25 * tier_amount
        excess -= tier_amount

    # Tier 3 (ignored, no further contribution)

    return contribution





def calculate_means_tested_fee(income_yearly, assets, homeowner=True, already_paid=0):
    """
    Calculate Means Tested Care Fee (MTCF).
    income_yearly: assessable annual income
    assets: assessable assets
    homeowner: bool
    already_paid: amount already paid toward lifetime cap
    """
    income_contrib = income_test(income_yearly)
    print(f"income_contrib: {income_contrib}, daily:{income_contrib/364} ")
    asset_contrib = asset_test(assets, homeowner)
    print(f"asset_contrib: { asset_contrib }, daily:{ asset_contrib/364 } ")

    # Combine contributions
    mtcf_annual = income_contrib + asset_contrib

    # Apply annual and lifetime caps
    #mtcf_annual = min(mtcf_annual, ANNUAL_CAP)
    mtcf_total_cap = max(0, LIFETIME_CAP - already_paid)
    mtcf_annual = min(mtcf_annual, mtcf_total_cap)

    mtcf_daily = (mtcf_annual / 365) - MAX_ACCOM_SUPP
    mtcf_daily = mtcf_daily if mtcf_daily > 0 else 0


    return {
        "basic_daily_fee": BASIC_DAILY_FEE,
        "means_tested_fee_daily": mtcf_daily,
        "total_daily_fee": BASIC_DAILY_FEE + mtcf_daily,
        "annual_means_tested_fee": mtcf_annual
    }


# deeming calculations
def deemed_income(assets, status='single', lower_threshold=None, lower_rate=None, upper_rate=None):
    """
    Calculate deemed income from financial assets using two-tier deeming.

    Parameters:
      assets (float): total financial assets (AUD)
      status (str): 'single' or 'couple' (combined)
      lower_threshold (float): lower deeming threshold (AUD). If None, defaults to Centrelink thresholds.
      lower_rate (float): lower deeming rate (decimal). If None, defaults to Centrelink rates.
      upper_rate (float): upper deeming rate (decimal). If None, defaults to Centrelink rates.

    Returns:
      dict with:
        - assets
        - status
        - lower_threshold
        - lower_rate
        - upper_rate
        - deemed_lower_amount (portion up to threshold)
        - deemed_upper_amount (portion above threshold)
        - deemed_lower_income
        - deemed_upper_income
        - deemed_income (total)
    """
    # Default (Services Australia, effective 20 Sep 2025):
    # Single: lower threshold 64,200 ; Couple combined: 106,200
    # Rates: lower 0.75% (0.0075), upper 2.75% (0.0275)
    if lower_threshold is None or lower_rate is None or upper_rate is None:
        if status.lower() == 'single':
            lower_threshold = 64200.0 if lower_threshold is None else lower_threshold
        else:
            lower_threshold = 106200.0 if lower_threshold is None else lower_threshold
        lower_rate = 0.0075 if lower_rate is None else lower_rate
        upper_rate = 0.0275 if upper_rate is None else upper_rate

    assets = float(assets)
    lower_portion = min(assets, lower_threshold)
    upper_portion = max(0.0, assets - lower_threshold)
    deemed_lower_income = lower_portion * lower_rate
    deemed_upper_income = upper_portion * upper_rate
    total_deemed = deemed_lower_income + deemed_upper_income

    return {
        'assets': round(assets, 2),
        'status': status,
        'lower_threshold': round(lower_threshold, 2),
        'lower_rate': lower_rate,
        'upper_rate': upper_rate,
        'deemed_lower_amount': round(lower_portion, 2),
        'deemed_upper_amount': round(upper_portion, 2),
        'deemed_lower_income': round(deemed_lower_income, 2),
        'deemed_upper_income': round(deemed_upper_income, 2),
        'deemed_income': round(total_deemed, 2), # per annum
    }


def calculate_mtf_daily(income_ex_deemed: float, assets_ex_home: float, homeowner: bool, home_val:float) ->float:
    
    print(f"calculate_mtf_daily( income_ex_deemed:{income_ex_deemed}, assets_ex_home:{assets_ex_home}, homeowner:{homeowner}, home_val:{home_val}")
    deemed_out = deemed_income(assets_ex_home + min(home_val,210555), status='single')#,upper_rate=0.0075)
    print(deemed_out)

    result = calculate_means_tested_fee(income_ex_deemed+deemed_out['deemed_income'], deemed_out['assets'], homeowner, already_paid=0)
    print(f"Basic daily fee: ${result['basic_daily_fee']:.2f}")
    print(f"Means tested fee (daily): ${result['means_tested_fee_daily']:.2f}")
    print(f"Total daily fee: ${result['total_daily_fee']:.2f}")
    print(f"Annual MTCF payable: ${result['annual_means_tested_fee']:.2f}")
    print(f"(As of {date.today()})")

    return result['means_tested_fee_daily']


# Example usage:
if __name__ == "__main__":

    print("**** As homeowner:")
    income_ex_deemed = 28600  # yearly income: pension plus any non bank dividend and interest. Bank account and home (up to cap) is deemded
    assets_ex_home = 140000  # assets   
    homeowner = True
    home_val = 1000000 #Ex debts/mortgage home value limited to $210,555.20
    already_paid = 0

    # 
    deemed_out = deemed_income(assets_ex_home + min(home_val,210555), status='single')#,upper_rate=0.0075)
    print(deemed_out)



    result = calculate_means_tested_fee(income_ex_deemed+deemed_out['deemed_income'], deemed_out['assets'], homeowner, already_paid)
    print(f"Basic daily fee: ${result['basic_daily_fee']:.2f}")
    print(f"Means tested fee (daily): ${result['means_tested_fee_daily']:.2f}")
    print(f"Total daily fee: ${result['total_daily_fee']:.2f}")
    print(f"Annual MTCF payable: ${result['annual_means_tested_fee']:.2f}")
    print(f"(As of {date.today()})")

   
    print("running function")
    mtfd = calculate_mtf_daily(income_ex_deemed, assets_ex_home, homeowner, home_val)
    print(f"mtfd: {mtfd}")


    print("**** As NON homeowner:")
    RAD = 700000
    income_ex_deemed = 28600  # yearly income: pension plus any non bank dividend and interest. Bank account and home (up to cap) is deemded
    assets_ex_home = 140000+(1000000-RAD) + RAD  # assets   
    homeowner = False 
    home_val = 0 #Ex debts/mortgage home value limited to $210,555.20
    already_paid = 0

    deemed_out = deemed_income(assets_ex_home + min(home_val,210555), status='single') #,upper_rate=0.0075)
    print(deemed_out)



    result = calculate_means_tested_fee(income_ex_deemed+deemed_out['deemed_income'], deemed_out['assets'], homeowner, already_paid)
    print(f"Basic daily fee: ${result['basic_daily_fee']:.2f}")
    print(f"Means tested fee (daily): ${result['means_tested_fee_daily']:.2f}")
    print(f"Total daily fee: ${result['total_daily_fee']:.2f}")
    print(f"Annual MTCF payable: ${result['annual_means_tested_fee']:.2f}")
    print(f"(As of {date.today()})")


    print("running function")
    mtfd = calculate_mtf_daily(income_ex_deemed, assets_ex_home, homeowner, home_val)
    print(f"mtfd: {mtfd}")


    print("**** As homeowner:")
    income_ex_deemed = 52000-13856.26  # yearly income: pension plus any non bank dividend and interest. Bank account and home (up to cap) is deemded
    assets_ex_home = 340000  # assets   
    homeowner = True
    home_val = 1000000 #Ex debts/mortgage home value limited to $210,555.20
    already_paid = 0

    # 
    print("running function")
    mtfd = calculate_mtf_daily(income_ex_deemed, assets_ex_home, homeowner, home_val)
    print(f"mtfd: {mtfd}")

