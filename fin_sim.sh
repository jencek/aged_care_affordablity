#!/bin/bash

python -m aged_care_calcs.agedcare_sim \
    --initial-assets 140000 \
    --rad 800000 \
    --house-value 1000000 \
    --dap-percentage 7 \
    --income-interest-rate 4 \
    --start-date 2025-11-04 \
    --months-till-house-sale 6 \
    --total-months-after-sale 120 \
    --basic-daily-fee 63.82 \
    --means-tested-fee 25 \
    --means-tested-lifetime-limit 82347 \
    --special-services-fee 70 \
    --pension-initial 2200 \
    --pension-final 2200 \
    --incidental-expenditure-mthly 400 \
    --asset-interest-percentage 70 \
    --csv out.csv \
    --excel out.xlsx


