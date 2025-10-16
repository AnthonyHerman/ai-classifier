"""
Main orchestration for the AI red-teaming tool.
"""
import asyncio
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

from .config import config_manager
from .dataset_adapters import create_adapter
from .api.target_adapter import TargetAPIAdapter
from .evaluation.claude_evaluator import ClaudeEvaluator
from .reporting import HTMLReportGenerator


class RedTeamingOrchestrator:
    """Main orchestrator for red-teaming operations."""
    
    def __init__(self):
        self.config_manager = config_manager
        self.target_api = None
        self.claude_evaluator = None
        self.report_generator = HTMLReportGenerator()
        self.results = []
    
    async def initialize(self):
        """Initialize the orchestrator with configurations."""
        # Validate environment
        if not self.config_manager.validate_environment():
            raise RuntimeError("Environment validation failed")
        
        # Load target API config
        try:
            api_config = self.config_manager.load_target_api_config()
            self.target_api = TargetAPIAdapter(api_config)
            
            # Initialize Claude evaluator with system context
            system_context = api_config.get(
                'system_context', 
                'Generic AI assistant'
            )
            self.claude_evaluator = ClaudeEvaluator(system_context)
            
            print(f"Initialized with system context: {system_context[:100]}...")
            
        except FileNotFoundError as e:
            print(f"Configuration error: {e}")
            print("Run with --setup to create template configurations")
            raise
    
    async def test_single_prompt(self, prompt: str) -> Dict[str, Any]:
        """Test a single prompt end-to-end."""
        print(f"Testing prompt: {prompt[:50]}...")
        
        # Send to target API
        response, session_id = await self.target_api.send_prompt(prompt)
        if response is None:
            return {
                'prompt': prompt,
                'response': None,
                'evaluation': {'classification': 'ERROR', 'reasoning': 'API request failed'},
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"Got response (session: {session_id}): {response[:100]}...")
        
        # Evaluate with Claude
        evaluation = await self.claude_evaluator.evaluate_response(prompt, response)
        
        result = {
            'prompt': prompt,
            'response': response,
            'evaluation': evaluation,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Classification: {evaluation['classification']}")
        return result
    
    async def test_dataset(
        self, 
        dataset_name: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Test prompts from a dataset."""
        print(f"Loading dataset: {dataset_name}")
        
        # Get dataset config and create adapter
        dataset_config = self.config_manager.get_dataset_config(dataset_name)
        adapter = create_adapter(dataset_name, dataset_config)
        
        # Load prompts
        prompts = list(adapter.load_prompts(limit=limit))
        if not prompts:
            print(f"No prompts loaded from {dataset_name}")
            return []
        
        print(f"Loaded {len(prompts)} prompts from {dataset_name}")
        
        # Test each prompt
        results = []
        for i, prompt_data in enumerate(prompts):
            print(f"Testing prompt {i+1}/{len(prompts)}")
            
            result = await self.test_single_prompt(prompt_data['prompt'])
            result.update({
                'source_dataset': dataset_name,
                'original_label': prompt_data['label'],
                'metadata': prompt_data.get('metadata', {})
            })
            
            results.append(result)
            
            # Small delay to be respectful to APIs
            await asyncio.sleep(0.5)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = None):
        """Save results to JSON file and generate HTML report."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"redteam_results_{timestamp}.json"
        
        results_dir = self.config_manager.project_root / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Save JSON
        json_filepath = results_dir / filename
        with open(json_filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {json_filepath}")
        
        # Generate HTML report
        try:
            html_filepath = self.report_generator.generate_report(json_filepath)
            print(f"HTML report generated: {html_filepath}")
        except Exception as e:
            print(f"Warning: Failed to generate HTML report: {e}")
        
        return json_filepath
    
    def analyze_results(self, results: List[Dict[str, Any]]):
        """Analyze and print summary of results."""
        if not results:
            print("No results to analyze")
            return
        
        total = len(results)
        safe_count = sum(1 for r in results if r['evaluation']['classification'] == 'SAFE')
        unsafe_count = sum(1 for r in results if r['evaluation']['classification'] == 'UNSAFE')
        error_count = sum(1 for r in results if r['evaluation']['classification'] == 'ERROR')
        
        print(f"\n=== RESULTS SUMMARY ===")
        print(f"Total prompts tested: {total}")
        print(f"SAFE responses: {safe_count} ({safe_count/total*100:.1f}%)")
        print(f"UNSAFE responses: {unsafe_count} ({unsafe_count/total*100:.1f}%)")
        print(f"ERROR responses: {error_count} ({error_count/total*100:.1f}%)")
        
        # Show some unsafe examples
        unsafe_examples = [r for r in results if r['evaluation']['classification'] == 'UNSAFE']
        if unsafe_examples:
            print(f"\n=== UNSAFE EXAMPLES ===")
            for i, example in enumerate(unsafe_examples[:3]):
                print(f"\nExample {i+1}:")
                print(f"Prompt: {example['prompt'][:100]}...")
                print(f"Response: {example['response'][:100]}...")
                print(f"Reasoning: {example['evaluation'].get('reasoning', 'N/A')}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Red-Teaming Tool")
    parser.add_argument(
        "--setup", 
        action="store_true", 
        help="Create template configuration files"
    )
    parser.add_argument(
        "--single-prompt", 
        type=str, 
        help="Test a single prompt"
    )
    parser.add_argument(
        "--dataset", 
        type=str, 
        help="Test prompts from a dataset"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Limit number of prompts to test"
    )
    parser.add_argument(
        "--list-datasets", 
        action="store_true", 
        help="List available datasets"
    )
    parser.add_argument(
        "--all-datasets", 
        action="store_true", 
        help="Test all configured datasets"
    )
    parser.add_argument(
        "--generate-report",
        type=str,
        metavar="JSON_FILE",
        help="Generate HTML report from existing JSON results file"
    )
    
    args = parser.parse_args()
    
    if args.setup:
        config_manager.create_local_config_template()
        print("Template configurations created in local/ directory")
        print("Edit local/target_api.yaml and local/system_context.txt before running tests")
        return
    
    if args.list_datasets:
        datasets = config_manager.list_available_datasets()
        print("Available datasets:")
        for dataset in datasets:
            print(f"  - {dataset}")
        return
    
    if args.generate_report:
        # Generate report from existing JSON file
        json_path = Path(args.generate_report)
        if not json_path.exists():
            print(f"Error: File not found: {json_path}")
            sys.exit(1)
        
        generator = HTMLReportGenerator()
        try:
            html_path = generator.generate_report(json_path)
            print(f"HTML report generated: {html_path}")
        except Exception as e:
            print(f"Error generating report: {e}")
            sys.exit(1)
        return
    
    # Initialize orchestrator
    orchestrator = RedTeamingOrchestrator()
    try:
        await orchestrator.initialize()
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)
    
    # Execute requested operation
    results = []
    
    if args.single_prompt:
        result = await orchestrator.test_single_prompt(args.single_prompt)
        results = [result]
    
    elif args.dataset:
        results = await orchestrator.test_dataset(args.dataset, args.limit)
    
    elif args.all_datasets:
        datasets = config_manager.list_available_datasets()
        for dataset in datasets:
            print(f"\n{'='*50}")
            print(f"Testing dataset: {dataset}")
            print(f"{'='*50}")
            dataset_results = await orchestrator.test_dataset(dataset, args.limit)
            results.extend(dataset_results)
    
    else:
        parser.print_help()
        return
    
    # Analyze and save results
    if results:
        orchestrator.analyze_results(results)
        orchestrator.save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
