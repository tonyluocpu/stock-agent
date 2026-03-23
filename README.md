# Stock Agent Chatbot

This is a command-line stock assistant that can:

- download historical stock data and save it as CSV files
- run a second pass of data checks on the files it creates
- answer stock questions in plain language
- generate a simple financial analysis report from company statements

This README covers the tracked, public version of the repo: the CLI workflow in this folder.

## What you get in this repo

- `comprehensive_stock_chatbot.py` - the main chatbot entry point
- `evaluation_module.py` - file validation for downloaded data
- `financial_analysis_module.py` - financial statement analysis
- `api_config_template.py` - config template for your API key
- `setup.py` - creates the expected data folders

## Before you start

You will need:

- Python 3.10 or newer
- an OpenRouter API key
- internet access for OpenRouter, Yahoo Finance, and InvestPy lookups

## Quick start

1. Clone the repo and enter the project folder.

```bash
git clone <your-repo-url>
cd stock-agent
```

2. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create your local API config.

```bash
cp api_config_template.py api_config.py
```

Open `api_config.py`, paste your OpenRouter key, and save it.

`api_config.py` is ignored by git, so your key should stay local.

5. Create the data folders.

```bash
python3 setup.py
```

6. Start the chatbot.

```bash
python3 comprehensive_stock_chatbot.py --chat
```

## First commands to try

Historical data:

```text
Apple weekly data from 2020 to 2024
Microsoft and Google daily 2023 and 2024
NVDA from IPO to today
```

Stock questions:

```text
How is Tesla performing?
Compare Apple and Microsoft
```

Financial analysis:

```text
stock analysis of nvidia
should i buy tesla
financial analysis of microsoft
```

## One-shot mode

If you want one command instead of chat mode:

```bash
python3 comprehensive_stock_chatbot.py --request "AAPL weekly 2024"
```

In one-shot mode, the script auto-confirms the request, writes the CSV files, runs the built-in file checks, and skips prompt-driven web validation.

## Where files go

Downloaded files are written under `data/`, grouped by frequency and type.

Examples:

- `data/weekly/opening/AAPL/AAPL_WEEKLY_2024.csv`
- `data/weekly/closing/AAPL/AAPL_WEEKLY_2024.csv`

Validation reports are saved next to the CSV files.

## What the validation step checks

After a file is written, the app checks:

- basic price logic
- expected frequency spacing
- file-level issues worth flagging before you use the data

If you are in chat mode, some web-based validation steps may ask whether you want to continue when an external source disagrees or rate-limits.

## Common problems

`No LLM configuration found`

- make sure `api_config.py` exists in the project folder
- make sure the API key in that file is real and in quotes

`That doesn't appear to be a stock data request`

- use a clearer request with a ticker or company name, a frequency, and a date range
- example: `AAPL weekly 2024`

`No data found`

- try a different ticker or a wider date range
- minute and hourly data are usually limited to recent history

Validation or web lookup failures

- external providers can rate-limit or change behavior
- rerun the request later, or use chat mode if you want to respond to prompts manually

## A practical starting workflow

If you are new to the repo, do this:

1. Run `python3 comprehensive_stock_chatbot.py --chat`
2. Ask for one historical download such as `Apple weekly data from 2020 to 2024`
3. Open the generated CSV in `data/`
4. Try one financial prompt such as `stock analysis of nvidia`

That is enough to confirm the main loop is working on your machine.
