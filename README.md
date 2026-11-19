# Housing Pulse

[Open Housing Pulse](https://coolcode.ca/housing-pulse/)

<!-- coolcode:guide -->
Compare Halifax and Vancouver for a two-bedroom apartment in the second quarter of 2026. Average asking rents were $2,400 and $3,030, while average paid rents were $1,770 and $2,470. Switch to rental housing starts to explore a different source and monthly reporting period.
<!-- /coolcode:guide -->

Choose the measure first. The other selectors follow the source’s coverage. Compare monthly starts, completions, historical units under construction, starts by intended market, absorptions and unabsorbed inventory. Annual rental vacancy and quarterly asking and paid rent estimates have their own reporting calendars. The browser lets you change dwelling type, the pair of markets and the end of the comparison window, inspect a chart, open exact values and follow the underlying table.

Construction and vacancy use Canada Mortgage and Housing Corporation surveys. Table 34-10-0143 includes national and provincial estimates and selected metropolitan areas. Its provincial series cover centres of 10,000 people or more. Table 34-10-0148 covers additional cities including Halifax. Use its intended-market filter to compare rental starts. Vacancy includes privately initiated row and apartment structures of three units or more. Inventory and under-construction counts represent stocks, while starts and completions count activity during the selected month. The construction table begins in 1948. Its under-construction series ends in June 2002, and the monthly completions end in December 2025 in the launch edition. Each measure has its own latest period. Other tables begin in 2010 or their later first available year. Comparison gaps are raw units or percentage points. The app preserves missing values, source geography labels, and published quality flags.

Statistics Canada quarterly asking rent describes the advertised market. Paid rent measures a different population of units. Their difference alone cannot predict an individual tenant’s increase. CMAs with the same city name in different surveys may reflect different boundary vintages. Each chart compares markets within a single source series.

Sources: [Starts, completions and construction](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014301), [Starts by dwelling and market](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014801), [Absorptions and inventory](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014901), [Vacancy rates](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410013001), [Quarterly rent statistics](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610009201).

Adapted from Canada Mortgage and Housing Corporation, Starts and Completions Survey, Market Absorption Survey and Rental Market Survey, source records beginning in 1948. This does not constitute an endorsement by Canada Mortgage and Housing Corporation of this product. CMHC information is provided under the [CMHC Licence Agreement for the Use of Data](https://www.statcan.gc.ca/en/reference/agreement_CMHC). The Statistics Canada rent table is provided under the [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).

## Refresh and development

The committed edition builds offline. The scheduled workflow downloads the official archives, validates the edition, runs the browser checks, then commits the refreshed snapshot and deploys it. Source retrieval dates are separate from the observation periods. A failed refresh leaves the last published edition available.

Run `python3 scripts/refresh.py` to retrieve current source files, `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests` and `python3 scripts/build.py` to check and build. Preview using `python3 -m http.server --directory dist`. The interactive browser check is `python3 tests/browser_smoke.py` after installing the test-only Playwright dependency and its Chromium browser.
