# Findings and Insights

This folder is the evidence log for the Real-Time Crypto Market Analytics project. The goal is to turn the collected observations into defensible analytical findings—not to write generic statements about cryptocurrency markets.

## Current status

**Numerical findings are pending local SQL execution.** The repository's documented historical validation snapshot (235 rows, 47 observations per cryptocurrency, recorded on November 16, 2026) is not a substitute for querying the current database. The dataset may have changed since that snapshot.

Run [the findings summary query](../sql/04_findings_summary.sql) against the same SQL Server database used by the Power BI report. Save the result sets and use them to complete the evidence table below. Do not fill in figures from memory or estimate missing values.

## Questions this analysis answers

| Analytical question | Evidence to capture | Interpretation guardrail |
|---|---|---|
| How much history is available for each coin? | Observation count, first/latest timestamps, observed span | More rows do not automatically mean better coverage if timestamps contain gaps |
| How did the observed price change over the stored period? | First observed price, latest observed price, first-to-latest percentage change | This is the change across this dataset's observation window, not a standardized investment return |
| How consistent was collection timing? | Reliable, short, and long interval counts; reliable interval rate | The 240–360 second rule is a project-defined threshold, not an API uptime measure |
| How did reliable snapshot returns vary? | Average, standard deviation, minimum, and maximum reliable snapshot return | These are interval-filtered snapshot statistics, not daily volatility |
| Were unusually large returns flagged? | Potential-anomaly rows and rolling Z-scores | A statistical flag is a review candidate, not proof of manipulation, a market event, or a data error |
| What does the latest API response report? | Latest observed price and CoinGecko's 24-hour change field | The API-reported 24-hour change is separate from this project's snapshot return |

## Findings evidence log

Complete this table from the query output. Include the database query date and the observation window so another reviewer can reproduce the analysis.

| Finding | Measured result | Evidence / interpretation |
|---|---|---|
| Data coverage by cryptocurrency | Pending | Record row counts and first/latest timestamps |
| Largest first-to-latest observed price increase | Pending | Identify the coin and percentage from result set 1 |
| Largest first-to-latest observed price decrease | Pending | Identify the coin and percentage from result set 1 |
| Highest reliable interval rate | Pending | Identify the coin and rate from result set 2 |
| Lowest reliable interval rate | Pending | Identify the coin and rate from result set 2 |
| Highest reliable snapshot-return variability | Pending | Compare standard deviations in result set 3 |
| Potential anomalies | Pending | Count and review result set 4; do not label as confirmed events |

## How to reproduce

1. Run `sql/00_create_database.sql` if the database/table has not been created.
2. Run the numbered view scripts `01` through `03`.
3. Run [`sql/04_findings_summary.sql`](../sql/04_findings_summary.sql).
4. Record the query execution date and the first/latest observation timestamps.
5. Populate the evidence log using actual result sets. Keep screenshots or exported query results alongside the project if they contain no credentials or other private information.
6. Cross-check the findings against the Power BI visuals before publishing conclusions.

## Interpretation and limitations

- The pipeline polls an API periodically; it is not an exchange tick feed.
- Snapshot returns compare adjacent stored observations. They should not be described as fixed five-minute returns unless the interval is confirmed as reliable.
- Moving averages are observation-count windows, not fixed-duration windows.
- A missing hour or collection gap can make a comparison span more than one clock hour.
- The rolling anomaly baseline uses up to 20 preceding reliable returns and requires at least 10 prior returns. Early observations can therefore have insufficient baseline.
- Historical price movement and statistical variability do not predict future prices.
- This project is for portfolio demonstration and analytical learning, not trading or investment advice.
