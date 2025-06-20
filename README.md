# AI Red-Teaming Tool

Automated LLM red-teaming using malicious prompt datasets with Claude as the safety classifier.

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
# Test single prompt
python -m src.main --single-prompt "Tell me how to hack a system"

# Run full dataset evaluation
python -m src.main --dataset qualifire --limit 100

# Run all datasets
python -m src.main --all-datasets
```

## Architecture

- **Dataset Adapters**: Normalize different dataset formats
- **API Adapters**: Handle arbitrary API request/response schemas
- **Claude Evaluator**: Safety classification of responses
- **Configuration**: Flexible, secure local configuration

## Supported Datasets

- Qualifire/prompt-injection-benchmark
- xxz224/prompt-injection-attack-dataset
- yanismiraoui/prompt_injections
- jayavibhav/prompt-injection-safety
- jayavibhav/prompt-injection
- deepset/prompt-injections

## Directory Structure

```
ai-classifier/
├── src/
│   ├── dataset_adapters/     # Dataset format handlers
│   ├── api/                  # API interaction components
│   ├── evaluation/           # Claude safety evaluation
│   └── main.py              # Entry point
├── config/                   # Templates and shared config
├── local/                   # Your private config (gitignored)
└── results/                 # Test results (gitignored)
```
