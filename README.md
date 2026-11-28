# Housing Pulse

[Open Housing Pulse](https://coolcode.ca/housing-pulse/)

<!-- coolcode:guide -->
Compare Halifax and Vancouver for a two-bedroom apartment in the second quarter of 2026. Average asking rents were $2,400 and $3,030, while average paid rents were $1,770 and $2,470. Switch to rental housing starts to explore a different source and monthly reporting period.
A separate province-matched panel compares rent CPI, average weekly earnings and all-area housing completions over the same complete calendar years. Use the latest-common-years button for a fully numeric three-way comparison; newer unavailable completions remain gaps.
Each metro report compares unit types in one quarter, shows available asking and paid rents side by side, and opens the matching selection in the chart. Provincial reports compare complete rent-index and earnings years and date the latest published completion count separately.
<!-- /coolcode:guide -->

[Browse metro rent and provincial housing reports](https://coolcode.ca/housing-pulse/records/).

Choose the measure first. The other selectors follow the source’s coverage. Compare monthly starts, completions, historical units under construction, starts by intended market, absorptions and unabsorbed inventory. Annual rental vacancy and quarterly asking and paid rent estimates have their own reporting calendars. The browser lets you change dwelling type, the pair of markets and the end of the comparison window, inspect a chart, open exact values and follow the underlying table.

Construction and vacancy use Canada Mortgage and Housing Corporation surveys. Table 34-10-0143 includes national and provincial estimates and selected metropolitan areas. Its provincial series cover centres of 10,000 people or more. Table 34-10-0148 covers additional cities including Halifax. Use its intended-market filter to compare rental starts. Vacancy includes privately initiated row and apartment structures of three units or more. Inventory and under-construction counts represent stocks, while starts and completions count activity during the selected month. The construction table begins in 1948. Its under-construction series ends in June 2002, and its final numeric completions are for December 2022. Later completion rows through December 2025 carry an unavailable symbol in the launch edition. Each measure has its own latest period. A fresh selection opens on the latest mutually available value when possible; the full picker includes missing periods. Other tables begin in 2010 or their later first available year. Comparison gaps are raw units or percentage points. The app preserves missing values, source geography labels, and published quality flags.

Statistics Canada quarterly asking rent describes the advertised market. Paid rent measures a different population of units. Their difference alone cannot predict an individual tenant’s increase. CMAs with the same city name in different surveys may reflect different boundary vintages. Each chart compares markets within a single source series.

Sources: [Starts, completions and construction](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014301), [Starts by dwelling and market](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014801), [Absorptions and inventory](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410014901), [Vacancy rates](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410013001), [Quarterly rent statistics](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610009201).

Adapted from Canada Mortgage and Housing Corporation, Starts and Completions Survey, Market Absorption Survey and Rental Market Survey, source records beginning in 1948. This does not constitute an endorsement by Canada Mortgage and Housing Corporation of this product. CMHC information is provided under the [CMHC Licence Agreement for the Use of Data](https://www.statcan.gc.ca/en/reference/agreement_CMHC). The Statistics Canada rent table is provided under the [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).

## Refresh and development

The committed edition builds offline. The scheduled workflow downloads the official archives, validates the edition, runs the browser checks, then commits the refreshed snapshot and deploys it. Source retrieval dates are separate from the observation periods. A failed refresh leaves the last published edition available.

Run `python3 scripts/refresh.py` to retrieve current source files, `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests` and `python3 scripts/build.py` to check and build. Preview using `python3 -m http.server --directory dist`. The interactive browser check is `python3 tests/browser_smoke.py` after installing the test-only Playwright dependency and its Chromium browser.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. The independent watchdog uses the centrally maintained [scheduler registry](https://github.com/jsdyer/jsdyer.github.io/tree/main/data/operations). An installed watchdog automatically downloads registry updates; its deployment and runtime health must be checked separately. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->

## Comparable rent, earnings and completions

The added panel uses Canada and the ten exact provinces. Rent CPI is table 18-10-0004-01, Rent, not seasonally adjusted (2002=100). Earnings are table 14-10-0223-01, average weekly earnings including overtime, industrial aggregate excluding unclassified businesses, seasonally adjusted. For each, the app takes an unweighted arithmetic mean only when all 12 months have numeric values. These are our annual summaries, not a separate published annual table. Completions are published annual all-area total-unit figures from table 34-10-0126-01, so a city or urban-only survey is never joined to provincial wages. Missing/source-flagged values remain visible in JSON.

The current completion file has numeric values only through 2022. This is also true in its official 2026 release; we do not invent newer values. The default recent five-year comparison shows that gap, and **Use latest years with all three measures** selects a real common historical window. Rent CPI measures price change, not dollar rent; differences between rent and earnings growth are percentage points, not affordability ratios or causal claims. Census geography vintages and the populations of the three surveys differ and are disclosed.

Edit `config/context.json` for exact published geographies and first year, then run `python scripts/refresh_context.py`. The monthly workflow runs it after the original collection. Output `web/data/context.json` has independent successful `checked_at`, source table/vector references and full annual values. Failed downloads/parsing leave the old file and stop publication. Optional `--source-dir /path` reads the exact three official ZIP files for reproducible validation. Run existing tests/build, commit and inspect Pages. No keys or private inputs are required.
