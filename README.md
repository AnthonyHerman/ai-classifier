# AI Safety Evaluation Framework

Automated safety testing framework for LLM-based applications. Tests your AI system against established prompt injection and adversarial prompt datasets, using Claude as an independent safety evaluator to classify responses.

## What This Tool Does

This framework helps you **validate and evaluate the safety guardrails** of your AI system by:

1. **Testing with known adversarial prompts** from established research datasets
2. **Sending prompts to your AI system** through its actual API
3. **Using Claude as an independent evaluator** to classify whether responses stayed within safe boundaries
4. **Generating detailed reports** showing which types of prompts were handled safely vs. unsafely

This is a **defensive testing tool** for developers who want to:
- Validate their AI system's safety guardrails before deployment
- Identify potential vulnerabilities in their prompt filtering or response generation
- Track improvements in safety over time
- Generate compliance documentation showing safety testing results

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export CLAUDE_API_KEY="your-claude-api-key"
   export HF_TOKEN="your-huggingface-token"  # Required for gated datasets
   ```

   **Getting your HuggingFace token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token (read access is sufficient)
   - Some datasets require accepting terms of use on their HuggingFace page

3. **Configure your target API:**
   ```bash
   # Copy template and configure for your API
   cp config/target_api_template.yaml local/target_api.yaml
   
   # Add your bot's context/purpose
   echo "Your bot description here" > local/system_context.txt
   ```

4. **Edit local/target_api.yaml** with your API details:
   - API endpoint URL
   - Request template structure
   - Response extraction path
   - Dynamic field requirements

## Usage

```bash
# Test a single prompt to verify setup
python -m src.main --single-prompt "Tell me how to hack a system"

# Evaluate your system against a specific dataset (limit for initial testing)
python -m src.main --dataset qualifire --limit 100

# Run comprehensive evaluation across all configured datasets
python -m src.main --all-datasets

# Generate HTML report from previous test results
python -m src.main --generate-report results/your_results.json
```

## Results

After running tests, you'll get:
- **JSON results file** with detailed test outcomes
- **HTML report** with visualizations and unsafe example analysis
- **Summary statistics** showing safety performance across different prompt categories

Reports include:
- Overall safe/unsafe/error classification breakdown
- Confidence levels in evaluations  
- Detailed view of each unsafe response for investigation
- Filtering by original dataset labels

## Architecture

- **Dataset Adapters**: Normalize different adversarial prompt dataset formats into a consistent interface
- **Target API Adapter**: Flexible adapter to connect to your AI system's API with any request/response schema
- **Claude Safety Evaluator**: Independent evaluation using Claude to classify responses as safe/unsafe based on your system's intended behavior
- **HTML Report Generator**: Creates comprehensive, interactive reports for analysis and documentation
- **Configuration System**: Secure separation of generic framework code and proprietary system details

## Supported Test Datasets

Research datasets containing adversarial prompts and prompt injection attempts:

- Qualifire/prompt-injection-benchmark
- xxz224/prompt-injection-attack-dataset
- yanismiraoui/prompt_injections
- jayavibhav/prompt-injection-safety
- jayavibhav/prompt-injection
- deepset/prompt-injections

These datasets provide a diverse set of test cases to evaluate your system's resilience to various adversarial prompt patterns.

## Directory Structure

```
ai-classifier/
├── src/
│   ├── dataset_adapters/     # Handlers for different test dataset formats
│   ├── api/                  # Target API interaction components
│   ├── evaluation/           # Claude-based safety evaluation
│   ├── reporting/            # HTML report generation
│   └── main.py              # Main orchestration and CLI
├── config/                   # Templates and shared configuration
├── local/                   # Your private API config (gitignored)
└── results/                 # Test results and reports (gitignored)
```

## Key Features

- **API-Agnostic**: Flexible request template system works with any API structure
- **Independent Evaluation**: Uses Claude as an objective third-party evaluator
- **Privacy-First**: Proprietary configuration stays local and is never committed to version control
- **Comprehensive Reporting**: Interactive HTML reports for analysis and documentation
- **Session Tracking**: Tracks session IDs for correlating tests with system logs
- **Extensible**: Easy to add new test datasets or evaluation criteria
