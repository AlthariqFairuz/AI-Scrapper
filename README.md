# AI Scrapper

A Python web scraper for the AMGR with natural language processing capabilities.

## Features

- **Web Scraping**: Scrapes the AMGR website with support for state, member, and breed filters
- **Pagination Support**: Automatically handles paginated results across multiple pages
- **Natural Language Processing**: Uses OpenRouter API to parse natural language commands into search parameters
- **Interactive Mode**: Command-line interface with interactive search capabilities
- **CLI Support**: Direct command-line arguments for programmatic usage
- **Regex Pattern Matching**: String matching with regex support for flexible searches

## Prerequisites

- Python 3.9+
- OpenRouter API key (for natural language processing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AlthariqFairuz/AI-Scrapper.git
cd MrScrapper
```

2. Install required dependencies:
```bash
pip install-r requirements.txt
```

3. Create a `.env` file and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

### Command Line Arguments

Search by specific parameters:
```bash
python scraper.py --state Kansas --member "Dwight Elmore"
python scraper.py --breed "(AR) - American Red"
```

### Natural Language Commands

Use natural language to describe your search:
```bash
python scraper.py --natural "Find members in Kansas with American Red breed"
```

### Interactive Mode

Start an interactive session:
```bash
python scraper.py --interactive
```

In interactive mode, you can enter natural language commands:
```
> Find members in Texas
> Show all breeders with Angus cattle
> quit
```

## Options

- `--state`: Filter by state name
- `--member`: Filter by member name  
- `--breed`: Filter by breed
- `--natural`: Natural language command
- `--interactive`: Start interactive mode

## Output

Results are displayed in a formatted table.

## Rate Limiting

The scraper includes a 1-second delay between page requests to avoid overwhelming the target server.

## Model Used

This project uses the DeepSeek: R1 Distill Llama 70B model from OpenRouter for natural language processing.
