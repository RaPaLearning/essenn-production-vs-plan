# Anomaly-detection in Factory production report

## Expected data-flow

1. Data entry (out of scope)
1. Factory employee exports Excel files: planning + production
1. Factory employee uploads Excel files to Google Drive after the night shift
1. Schedule the script to run at 8am
    1. Download Excel files from Google Drive
    1. Clean the data to a standard schema
    1. Detect anomalies
    1. Send report to supervisor in email + agent to summarize
    1. Clean-up and shut down

## Enhancements to the report

[6a] Classify the anomaly based on clustering / downtime -- pinpoint the problem

## Long-term optimization

- Productivity patterns
- Mistake patterns

## Setup

Install [uv](https://pypi.org/project/uv/) on the host

Install python dependencies:

```bash
uv sync
```
