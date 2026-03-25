# Anomaly-detection in Factory production report

## Setup

Install [uv](https://pypi.org/project/uv/) on the host

Install python dependencies:

```bash
uv sync
```

## Expected data-flow

1. Data entry (out of scope)
2. Factory employee exports excels: planning + production
3. Factory employee uploads excels to google drive after the night shift
4. 8am: schedule our program to run - download excels from google drive
5. program cleans the data to a standard schema
6. detects anomalies
7. sends report to supervisor in email + agent to summarize
8. clean-up and shut down

## Enhancements to the report

[6a] Classify the anomaly based on clustering / downtime -- pinpoint the problem

## Long-term optimization

- Productivity patterns
- Mistake patterns
