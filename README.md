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
<img width="1451" height="263" alt="image" src="https://github.com/user-attachments/assets/5a291dc7-0e55-45bd-a428-18036fcaca00" />
<img width="1458" height="275" alt="image" src="https://github.com/user-attachments/assets/6e4f5a4f-0ae9-4fc6-95f1-608da7282b2d" />
<img width="1124" height="104" alt="image" src="https://github.com/user-attachments/assets/45a0655f-a3fe-4199-b489-637223d0d11a" />
<img width="1083" height="260" alt="image" src="https://github.com/user-attachments/assets/e43f0df7-2462-40e0-ae83-177f53ce8c96" />

## Rate Limiting

The scraper includes a 1-second delay between page requests to avoid overwhelming the target server.

## Model Used

This project uses the DeepSeek: R1 Distill Llama 70B model from OpenRouter for natural language processing.
