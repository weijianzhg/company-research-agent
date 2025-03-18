# Company Research Agent 🔍

A Streamlit-based application that uses AI to research and analyze companies. The application can gather information about company profiles, industry sectors, and future objectives using web search and GPT analysis.

## Features

- 🔍 **Single Company Research**: Research individual companies with detailed analysis
- 📊 **Bulk Company Research**: Upload a CSV file to research multiple companies at once
- 📈 **Confidence Scoring**: Each piece of information comes with a confidence score
- 🔗 **Source Tracking**: All information is linked to its source
- 🤖 **AI-Powered Analysis**: Uses GPT-4 for intelligent information extraction
- 📱 **User-Friendly Interface**: Clean and intuitive Streamlit interface

## Prerequisites

- Python 3.11 or higher
- OpenAI API key
- Pipenv (for dependency management)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd company-research-agent
```

2. Install dependencies using Pipenv:
```bash
pipenv install
```

3. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Activate the virtual environment:
```bash
pipenv shell
```

2. Run the application:
```bash
streamlit run app.py --server.port 3444
```

3. Open your browser and navigate to `http://localhost:3444`

## Input Methods

### Single Company Research
1. Select "Single Company" as the input method
2. Enter the company name
3. Click "Research" to start the analysis

### Multiple Companies Research
1. Select "Multiple Companies" as the input method
2. Upload a CSV file containing a 'company_name' column (see example.csv)
3. Click "Research" to analyze all companies
4. Download the results as a CSV file

## Research Information

The application provides main types of information for each company:

1. **Company Profile**: Overview of the company's business and operations
2. **Industry Sector**: Company's sector and business type
3. **2025 Objectives**: Future goals and strategic plans

Each piece of information includes:
- Detailed data
- Confidence score
- Source link

## Development

The project uses:
- Streamlit for the web interface
- DuckDuckGo for web searches
- OpenAI GPT-4 for information analysis
- Pandas for data handling

## License

MIT

