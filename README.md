# Anomaly-detection in Factory production report

## Information flow in the factory

```mermaid
flowchart TD
    A([📧 Customer Order<br>received via Email]) --> B

    subgraph BLR["🏢 Bangalore Office"]
        B[Order entered<br>into OurSys]
    end

    B --> C

    subgraph HSN["🏭 Hassan Factory — Planning"]
        C[APS Gantt:<br>schedule & feasibility check]
        C -->|Fits schedule| D[Order approved]
        C -->|Doesn't fit| Z([🔴 Renegotiate /<br>Reject Order])
    end

    D --> E

    subgraph OUR1["⚙️ OurSys — Order Management"]
        E[Job Order created<br>in OurSys]
        E --> F[Raw Material<br>Purchase Order raised]
    end

    E --> G
    E --> H

    subgraph APS["📋 APS — Preact"]
        G[Job-Order Form<br>printed & attached<br>to physical job]
        H[Today's Production Form<br>generated from APS +<br>previous day's pending qty]
    end

    G --> I
    H --> I

    subgraph SHOP["🔧 Shop Floor — CNC Operations"]
        I[/Operator enters on keypad:<br>Job Order No. · Operator Code · Process Code/]
        I --> J[CNC machining<br>in progress]
        J --> P[/Operator enters downtime breaks/]
        I --> K[/Accepted & Rejected qty<br>filled into Production Form<br>by hand at end of shift/]
        P --> L[CNC reports counts<br>& downtime to TPM-trak]
    end

    K --> M
    L --> N

    subgraph BACK["📊 Data Entry & Reporting"]
        M[/Production Form data<br>entered into OurSys/]
        N[/TPM-trak data<br>consolidated into<br>Daily Report/]
    end

    N --> O([👔 Management<br>Review])
    M --> O
```

See samples [pictures here](https://drive.google.com/drive/folders/1_-o4STkU5P5QI7CZnIuod8hs3zJ_awhd?usp=sharing)

## Expected data-flow

1. Data entry (out of scope)
1. Factory employee exports Excel files: planning + production
1. Factory employee uploads Excel files to Google Drive after the night shift
1. Schedule the script to run at 8am:
    1. Download Excel files from Google Drive
    1. Clean the data to a standard schema
    1. Detect anomalies
    1. Create report
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
