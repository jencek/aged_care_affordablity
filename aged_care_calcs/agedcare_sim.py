#!/usr/bin/env python3
import argparse
import csv
from openpyxl import Workbook
from . import pension_calc_income_assets 
from . import mtf_calc 
import datetime


from collections import defaultdict

current_year = '1900'
year_total_mtf = defaultdict(float)




from dateutil.relativedelta import relativedelta

def parse_year(start_date: datetime.date, months: int) -> int:
    """
    Return the year as an integer for start_date incremented by months.
    """
    new_date = start_date + relativedelta(months=months)
    return new_date.year

def incr_year(start_date: datetime.date, months: int) -> int:
    """
    Return the year as an integer for start_date incremented by months.
    """
    new_date = start_date + relativedelta(months=months)
    return new_date

def simulate_finances(
    initial_assets,
    rad,
    house_value,
    dap_percentage,
    income_interest_rate,
    start_date,
    months_till_house_sale,
    total_months_after_sale,
    basic_daily_fee,
    means_tested_fee,
    means_tested_lifetime_limit,
    special_services_fee,
    pension_initial,
    pension_final,
    incidental_expenditure_mthly,
    asset_interest_percentage,
):
    global current_year, year_total_mtf

    # Convert daily fees → monthly
    monthly_basic_special = (basic_daily_fee + special_services_fee) * 30.44

    #not used as means tested is calculated
    monthly_means_tested = means_tested_fee * 30.44

    assets = initial_assets  # pay RAD up front
    lifetime_means_paid = 0

    rows = []


    def apply_month(month_idx, extra_cash=0):
        nonlocal assets, lifetime_means_paid


        # Lump sum (e.g., house sale)
        assets += extra_cash

        # Interest income per month
        interest_income = assets * (asset_interest_percentage/ 100)  *(income_interest_rate / 100 / 12)
        assets += interest_income
        #assets += pension_initial

        # deemed interest for use in pension calculation - annual number returned
        # requires assets excluding home as the home is ecluded
        deemed_out = mtf_calc.deemed_income(assets, status='single')#,upper_rate=0.0075)
    

        # pension calc is for fortnioght, hence double for month
        # income is per fortnight. This interest should be deemed rather than actual
        pension = pension_calc_income_assets.calculate_age_pension(deemed_out['deemed_income']/24, assets, homeowner=True)*2
        assets += pension

        # Fees
        # Fixed MTF
        # mtf = 0
        # fees = monthly_basic_special
        # if lifetime_means_paid < means_tested_lifetime_limit:
        #     mtf = min(monthly_means_tested,
        #               means_tested_lifetime_limit - lifetime_means_paid)
        #     fees += mtf
        #     lifetime_means_paid += mtf

        # calculated MTF
        mtf = 0
        fees = monthly_basic_special
        if lifetime_means_paid < means_tested_lifetime_limit and year_total_mtf[current_year]< mtf_calc.ANNUAL_CAP:

            monthly_means_tested = mtf_calc.calculate_mtf_daily(pension*24, #income_ex_deemed: float, 
                                                        assets, #assets_ex_home: float, 
                                                        True,#homeowner: bool, 
                                                        1000000 #home_val:float
                                                        ) *30

            mtf = min(monthly_means_tested,
                      means_tested_lifetime_limit - lifetime_means_paid)

            fees += mtf
            lifetime_means_paid += mtf

            year_total_mtf[current_year] += mtf



        # DAP fee
        dap_fee = rad * (dap_percentage / 100) / 12
        fees += dap_fee

        assets -= fees
        assets-=incidental_expenditure_mthly

        rows.append({
            "month": month_idx + 1,
            "year": current_year,
            "assets": round(assets, 2),
            "interest_income": round(interest_income, 2),
            "pension_income": round(pension, 2),
            "fees_total": round(fees, 2),
            "dap_fee": round(dap_fee, 2),
            "mtf": round(mtf,2),
            "annual_mtf_paid": round(year_total_mtf[current_year] ,2),
            "lifetime_means_paid": round(lifetime_means_paid, 2),
            "house_contribution": round(extra_cash,2),
            "rad_paid": round(0,2),
        })

    def apply_month_post_house_sale(month_idx, extra_cash=0):
        nonlocal assets, lifetime_means_paid

        print(f"apply_month_post_house_sale( {month_idx},{extra_cash})")

        # Lump sum (e.g., house sale)
        assets += extra_cash

        # Interest income
        interest_income = assets * (asset_interest_percentage/ 100)  *(income_interest_rate / 100 / 12)
        assets += interest_income # assets * (income_interest_rate / 100 / 12)

        #assets += pension_final
        # for pension we must use a deemed version of income from assets.
        # deemed interest for use in pension calculation - annual number returned
        # requires assets excluding home as the home is ecluded
        deemed_out = mtf_calc.deemed_income(assets, status='single')#,upper_rate=0.0075)
        print(f"deemed_out: {deemed_out}")

        # pension calc is for fortnioght, hence double for month
        # income is per fortnight. This interest should be deemed rather than actual
        pension = pension_calc_income_assets.calculate_age_pension(deemed_out['deemed_income']/24, assets, homeowner=False)*2
        print(f"pension: {pension}")

        assets += pension
        print(f"assets:{assets}")

        # Fees
        # mtf = 0
        # fees = monthly_basic_special
        # if lifetime_means_paid < means_tested_lifetime_limit:
        #     mtf = min(monthly_means_tested,
        #               means_tested_lifetime_limit - lifetime_means_paid)
        #     fees += mtf
        #     lifetime_means_paid += mtf

        # calculated MTF
        mtf = 0
        fees = monthly_basic_special

        print(f"lifetime_means_paid:{lifetime_means_paid}, means_tested_lifetime_limit: {means_tested_lifetime_limit}, year_total_mtf[current_year]: {year_total_mtf[current_year]}, mtf_calc.ANNUAL_CAP: {mtf_calc.ANNUAL_CAP}")

        if lifetime_means_paid < means_tested_lifetime_limit and year_total_mtf[current_year]< mtf_calc.ANNUAL_CAP:
            print(f"in if lifetime_means_paid: lifetime_means_paid:{lifetime_means_paid}, year_total_mtf[current_year]: {year_total_mtf[current_year]}")

            monthly_means_tested = mtf_calc.calculate_mtf_daily(pension*24, #income_ex_deemed: float, 
                                                        assets+rad, #assets_ex_home: float, 
                                                        False,#homeowner: bool, 
                                                        0 #home_val:float
                                                        ) *30

            mtf = min(monthly_means_tested,
                      means_tested_lifetime_limit - lifetime_means_paid)

            print(f"mtf: {mtf}")
            fees += mtf
            lifetime_means_paid += mtf

            year_total_mtf[current_year] += mtf


        # DAP fee
        dap_fee = 0 #rad * (dap_percentage / 100) / 12
        #fees += dap_fee

        assets -= fees

        rows.append({
            "month": month_idx + 1,
            "year": current_year,
            "assets": round(assets, 2),
            "interest_income": round(interest_income, 2),
            "pension_income": round(pension, 2),
            "fees_total": round(fees, 2),
            "dap_fee": round(dap_fee, 2),
            "mtf": round(mtf,2),
            "annual_mtf_paid": round(year_total_mtf[current_year] ,2),
            "lifetime_means_paid": round(lifetime_means_paid, 2),
            "house_contribution": round(extra_cash,2),
            "rad_paid": round(rad if extra_cash >0 else 0 ,2),
        })
        print(f"row appended: month: {month_idx + 1}, year: {current_year}, assets: {round(assets, 2)},interest_income: {round(interest_income, 2)},pension_income: {round(pension, 2)}")


    # ***
    # Start of simulate_finances()
    #

    # as we iterate through the months we need to identify what year we are in. This allows the annual 
    #mtf cap to be applied
    current_year = parse_year(start_date,0)

    # Before house sale
    for m in range(months_till_house_sale):
        current_year = parse_year(start_date,m)
        print(f"date;{start_date}+{m}")
        print(f"current_year: {current_year}")
        print(f"current_year_date: {incr_year(start_date,m)}")

        apply_month(m)

    assets -= rad  # pay RAD after house sale

    # After house sale
    for m in range(total_months_after_sale):
        current_year = parse_year(start_date,months_till_house_sale + m)
        print(f"date;{start_date}+{months_till_house_sale + m}")
        print(f"current_year: {current_year}")
        print(f"current_year_date: {incr_year(start_date,months_till_house_sale + m)}")
        apply_month_post_house_sale(
            months_till_house_sale + m,
            extra_cash=house_value if m == 0 else 0
        )

    return rows

def save_csv(filename, results):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"✅ Saved results to {filename}")


def save_excel(filename, results):
    wb = Workbook()
    ws = wb.active
    ws.title = "AgedCare Simulation"

    headers = list(results[0].keys())
    ws.append(headers)

    for r in results:
        ws.append([r[h] for h in headers])

    wb.save(filename)
    print(f"✅ Saved results to {filename}")


import datetime

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD.")



def main():

    parser = argparse.ArgumentParser(description="Aged Care Financial Simulator (Named Args)")

    parser.add_argument("--initial-assets", type=float, required=True, help="Initial financial assets ($)")
    parser.add_argument("--rad", type=float, required=True, help="Refundable Accommodation Deposit ($)")
    parser.add_argument("--start-date",type=valid_date,required=True,help="Date in YYYY-MM-DD format")
    parser.add_argument("--house-value", type=float, required=True, help="Value of house to be sold later ($)")
    parser.add_argument("--dap-percentage", type=float, required=True, help="Annual DAP percentage on RAD (e.g. 5 for 5%)")
    parser.add_argument("--income-interest-rate", type=float, required=True, help="Annual income interest rate on assets (%)")
    parser.add_argument("--months-till-house-sale", type=int, required=True, help="Months until house is sold")
    parser.add_argument("--total-months-after-sale", type=int, required=True, help="Months to simulate after house sale")
    parser.add_argument("--basic-daily-fee", type=float, required=True, help="Basic daily care fee per day ($)")
    parser.add_argument("--means-tested-fee", type=float, required=True, help="Means tested fee per day ($)")
    parser.add_argument("--means-tested-lifetime-limit", type=float, required=True, help="Lifetime cap for means tested fees ($)")
    parser.add_argument("--special-services-fee", type=float, required=True, help="Special services fee per day ($)")
    parser.add_argument("--pension-initial", type=float, required=True, help="Pension per month pre house sale($)")
    parser.add_argument("--pension-final", type=float, required=True, help="Pension per month after house sale($)")
    parser.add_argument("--incidental-expenditure-mthly", type=float, required=True, help="Monthly outgoing living expenses")
    parser.add_argument("--asset-interest-percentage", type=float, required=True, help="The percentage of the asset pool earning interest")
    parser.add_argument("--csv", help="Output results to CSV file")
    parser.add_argument("--excel", help="Output results to Excel file")

    args = parser.parse_args()

    results = simulate_finances(
        initial_assets=args.initial_assets,
        rad=args.rad,
        house_value=args.house_value,
        dap_percentage=args.dap_percentage,
        income_interest_rate=args.income_interest_rate,
        months_till_house_sale=args.months_till_house_sale,
        start_date=args.start_date,
        total_months_after_sale=args.total_months_after_sale,
        basic_daily_fee=args.basic_daily_fee,
        means_tested_fee=args.means_tested_fee,
        means_tested_lifetime_limit=args.means_tested_lifetime_limit,
        special_services_fee=args.special_services_fee,
        pension_initial=args.pension_initial,
        pension_final=args.pension_final,
        incidental_expenditure_mthly=args.incidental_expenditure_mthly,
        asset_interest_percentage=args.asset_interest_percentage,

    )

    print("Month | Year |Assets | Interest | Pension | Fees(total) | DAP fees| MTF fees|Annual MTF Paid|Lifetime Means Paid | House Contribution | RAD Paid")
    print(f"{0:>5} | 0 | {args.initial_assets:>10,.2f} | {0:>8,.2f} | {0:>8,.2f} | {0:>8,.2f} | {0:>8,.2f} | {0:>10,.2f} | {0:>10,.2f}| {0:>10,.2f} | {0:>10,.2f}")

    for r in results:
        print(f"{r['month']:>5} | {r['year']:>5}| {r['assets']:>10,.2f} | {r['interest_income']:>8,.2f} | {r['pension_income']:>8,.2f} | {r['fees_total']:>8,.2f} | {r['dap_fee']:>8,.2f} | {r['annual_mtf_paid']:>8,.2f} |{r['lifetime_means_paid']:>10,.2f} |{r['lifetime_means_paid']:>10,.2f} | {r['house_contribution']:>10,.2f} | {r['rad_paid']:>10,.2f}")

    # Optional outputs
    if args.csv:
        save_csv(args.csv, results)

    if args.excel:
        save_excel(args.excel, results)



if __name__ == "__main__":
    main()
