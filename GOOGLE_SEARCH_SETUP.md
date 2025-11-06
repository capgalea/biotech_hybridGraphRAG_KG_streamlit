# Google Search Integration Setup

The application now includes Google Search integration to enhance summaries with external references and additional context.

## Setup Options

### Option 1: Google Custom Search Engine (Recommended)

1. **Create a Google Custom Search Engine:**
   - Go to [Google Custom Search Engine](https://cse.google.com/cse/)
   - Create a new search engine
   - Set it to search the entire web
   - Note your Custom Search Engine ID (CSE ID)

2. **Get Google API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the "Custom Search API"
   - Create an API key
   - Note your API key

3. **Configure in secrets.toml:**
   ```toml
   [google]
   api_key = "your-google-generativeai-api-key-here"
   search_api_key = "your-google-custom-search-api-key-here"
   cse_id = "your-custom-search-engine-id-here"
   ```

### Option 2: SerpAPI (Alternative)

1. **Get SerpAPI Key:**
   - Sign up at [SerpAPI](https://serpapi.com/)
   - Get your API key from the dashboard

2. **Configure in secrets.toml:**
   ```toml
   [serpapi]
   api_key = "your-serpapi-key-here"
   ```

## Features

- **Enhanced Summaries**: LLM-generated summaries now include external references
- **Fallback Integration**: Even basic fallback summaries include web search results
- **Automatic References**: Search results are automatically formatted with clickable links
- **Context Enrichment**: Additional context from web search helps provide more comprehensive insights

## Benefits

1. **Broader Context**: Database results are supplemented with current web information
2. **External Validation**: Cross-reference internal data with external sources
3. **Recent Developments**: Include latest news and research developments
4. **Citation Support**: Proper references with clickable links for further reading

## Usage

Once configured, the Google Search integration works automatically:
- Every summary generation includes relevant web search results
- External references appear in a dedicated "External References" section
- Links are formatted as clickable markdown links
- Search results are limited to 3-5 most relevant items to avoid overwhelming the summary

## Fallback Behavior

If no search API credentials are configured:
- The application continues to work normally
- Summaries are generated without external references
- A warning message is logged (not visible to users)
- No functionality is lost - only the additional context is unavailable