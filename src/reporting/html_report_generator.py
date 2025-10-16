"""
HTML Report Generator for AI Red-Teaming Results
"""
import json
import traceback
import html
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class HTMLReportGenerator:
    """Generates professional HTML reports from red-teaming test results."""
    
    def __init__(self):
        pass
    
    def generate_report(self, results_file: Path, output_file: Path = None) -> Path:
        """
        Generate an HTML report from a results JSON file.
        
        Args:
            results_file: Path to the JSON results file
            output_file: Optional output path. If None, uses same name with .html extension
            
        Returns:
            Path to the generated HTML report
        """
        try:
            # Load results
            print(f"Loading results from {results_file}...")
            with open(results_file, 'r') as f:
                results = json.load(f)
            print(f"Loaded {len(results)} results")
            
            # Calculate statistics
            print("Calculating statistics...")
            stats = self._calculate_statistics(results)
            print(f"Stats: {stats['total']} total, {stats['safe_count']} safe, {stats['unsafe_count']} unsafe")
            
            # Generate HTML
            print("Generating HTML content...")
            html_content = self._generate_html(stats, results_file.name)
            
            # Determine output path
            if output_file is None:
                output_file = results_file.with_suffix('.html')
            
            # Write HTML file
            print(f"Writing HTML to {output_file}...")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Report generated successfully!")
            return output_file
            
        except Exception as e:
            print(f"Error in generate_report: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
        total = len(results)
        if total == 0:
            return {
                'total': 0,
                'safe_count': 0,
                'unsafe_count': 0,
                'error_count': 0,
                'safe_percent': 0,
                'unsafe_percent': 0,
                'error_percent': 0,
                'by_dataset': {},
                'by_confidence': {},
                'unsafe_examples': [],
                'original_labels': []
            }
        
        safe_count = sum(1 for r in results if r['evaluation']['classification'] == 'SAFE')
        unsafe_count = sum(1 for r in results if r['evaluation']['classification'] == 'UNSAFE')
        error_count = sum(1 for r in results if r['evaluation']['classification'] == 'ERROR')
        
        # By dataset
        by_dataset = {}
        for result in results:
            dataset = result.get('source_dataset', 'unknown')
            if dataset not in by_dataset:
                by_dataset[dataset] = {'safe': 0, 'unsafe': 0, 'error': 0, 'total': 0}
            
            classification = result['evaluation']['classification']
            by_dataset[dataset][classification.lower()] += 1
            by_dataset[dataset]['total'] += 1
        
        # By confidence - handle None values
        by_confidence = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        for result in results:
            confidence = result['evaluation'].get('confidence', 'unknown')
            # Handle None or missing confidence
            if confidence is None or confidence == 'none':
                confidence = 'unknown'
            if confidence in by_confidence:
                by_confidence[confidence] += 1
            else:
                by_confidence['unknown'] += 1
        
        # Unsafe examples - store full details
        unsafe_examples = []
        for r in results:
            if r['evaluation']['classification'] == 'UNSAFE':
                unsafe_examples.append({
                    'prompt': r.get('prompt', 'N/A'),
                    'response': r.get('response', 'N/A'),
                    'reasoning': r['evaluation'].get('reasoning', 'N/A'),
                    'session_id': r.get('session_id', 'N/A'),
                    'timestamp': r.get('timestamp', 'N/A'),
                    'dataset': r.get('source_dataset', 'unknown'),
                    'original_label': r.get('original_label', 'unknown')
                })
        
        # Get unique original labels from unsafe examples
        original_labels = sorted(set(ex['original_label'] for ex in unsafe_examples))
        
        return {
            'total': total,
            'safe_count': safe_count,
            'unsafe_count': unsafe_count,
            'error_count': error_count,
            'safe_percent': round(safe_count / total * 100, 1),
            'unsafe_percent': round(unsafe_count / total * 100, 1),
            'error_percent': round(error_count / total * 100, 1),
            'by_dataset': by_dataset,
            'by_confidence': by_confidence,
            'unsafe_examples': unsafe_examples,
            'original_labels': original_labels
        }
    
    def _generate_unsafe_table_html(self, unsafe_examples: List[Dict[str, Any]]) -> str:
        """Generate HTML table for unsafe examples."""
        if not unsafe_examples:
            return '<p class="text-center text-gray-500 py-8">No unsafe examples found. Excellent! 🎉</p>'
        
        rows = []
        for i, example in enumerate(unsafe_examples, 1):
            # Escape HTML
            prompt = html.escape(example['prompt'])
            response = html.escape(example['response'])
            reasoning = html.escape(example['reasoning'])
            original_label = html.escape(str(example.get('original_label', 'unknown')))
            
            row = f'''
            <div class="border-b unsafe-item" style="border-color: #e5e7eb;" data-original-label="{original_label}">
                <div class="p-4 hover-bg cursor-pointer" onclick="toggleDetail('{i}')">
                    <div class="flex" style="justify-content: space-between; align-items: flex-start;">
                        <div class="flex-1">
                            <div class="flex" style="align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                <div class="font-semibold text-red-700">Unsafe Example #{i}</div>
                                <span class="text-xs" style="background-color: #fef3c7; color: #92400e; padding: 0.125rem 0.5rem; border-radius: 9999px;">
                                    {original_label}
                                </span>
                            </div>
                            <div class="text-sm text-gray-600 line-clamp-2">{prompt[:150]}{'...' if len(prompt) > 150 else ''}</div>
                        </div>
                        <button class="text-gray-500" style="border: none; background: none; cursor: pointer;">
                            <span id="icon-{i}">▼</span>
                        </button>
                    </div>
                </div>
                <div id="detail-{i}" class="hidden bg-gray-50 p-4 space-y-4">
                    <div>
                        <div class="text-xs font-bold text-gray-700 mb-2 uppercase">Attack Prompt:</div>
                        <div class="bg-white p-3 rounded border text-sm text-gray-800 whitespace-pre-wrap">{prompt}</div>
                    </div>
                    <div>
                        <div class="text-xs font-bold text-gray-700 mb-2 uppercase">System Response:</div>
                        <div class="bg-white p-3 rounded border text-sm text-gray-800 whitespace-pre-wrap">{response}</div>
                    </div>
                    <div>
                        <div class="text-xs font-bold text-gray-700 mb-2 uppercase">Evaluation Reasoning:</div>
                        <div class="bg-white p-3 rounded border text-sm text-gray-800 whitespace-pre-wrap">{reasoning}</div>
                    </div>
                    <div class="flex gap-4 text-xs text-gray-500">
                        <div><strong>Session:</strong> {example['session_id']}</div>
                        <div><strong>Dataset:</strong> {example['dataset']}</div>
                        <div><strong>Original Label:</strong> {original_label}</div>
                    </div>
                </div>
            </div>
            '''
            rows.append(row)
        
        return '\n'.join(rows)
    
    def _generate_html(self, stats: Dict[str, Any], filename: str) -> str:
        """Generate the complete HTML document."""
        
        # Generate dataset chart data
        dataset_labels = list(stats['by_dataset'].keys())
        dataset_safe = [stats['by_dataset'][d]['safe'] for d in dataset_labels]
        dataset_unsafe = [stats['by_dataset'][d]['unsafe'] for d in dataset_labels]
        dataset_error = [stats['by_dataset'][d]['error'] for d in dataset_labels]
        
        # Generate unsafe table
        unsafe_table_html = self._generate_unsafe_table_html(stats['unsafe_examples'])
        
        # Generate filter options for original labels
        label_options = ''.join([f'<option value="{label}">{label}</option>' for label in stats['original_labels']])
        
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Red Team Security Report - {filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #f9fafb;
            color: #111827;
        }}
        .container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .stat-card {{
            border-radius: 10px;
            padding: 1.25rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
        }}
        .stat-card-total {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .stat-card-safe {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card-unsafe {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        .stat-card-error {{
            background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%);
        }}
        .grid {{
            display: grid;
            gap: 1rem;
        }}
        .grid-cols-2 {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .grid-cols-4 {{
            grid-template-columns: repeat(4, 1fr);
        }}
        @media (max-width: 768px) {{
            .grid-cols-4 {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        h1 {{
            font-size: 2.25rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        h2 {{
            font-size: 1.25rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }}
        .text-gray-600 {{
            color: #4b5563;
        }}
        .text-gray-500 {{
            color: #6b7280;
        }}
        .text-sm {{
            font-size: 0.875rem;
        }}
        .text-xs {{
            font-size: 0.75rem;
        }}
        .font-bold {{
            font-weight: bold;
        }}
        .font-semibold {{
            font-weight: 600;
        }}
        .opacity-90 {{
            opacity: 0.9;
        }}
        .mb-1 {{
            margin-bottom: 0.25rem;
        }}
        .mb-2 {{
            margin-bottom: 0.5rem;
        }}
        .mb-4 {{
            margin-bottom: 1rem;
        }}
        .mb-8 {{
            margin-bottom: 2rem;
        }}
        .p-3 {{
            padding: 0.75rem;
        }}
        .p-4 {{
            padding: 1rem;
        }}
        .py-8 {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        .text-center {{
            text-align: center;
        }}
        .border {{
            border: 1px solid #e5e7eb;
        }}
        .border-b {{
            border-bottom: 1px solid #e5e7eb;
        }}
        .rounded {{
            border-radius: 0.25rem;
        }}
        .rounded-lg {{
            border-radius: 0.5rem;
        }}
        .overflow-hidden {{
            overflow: hidden;
        }}
        .cursor-pointer {{
            cursor: pointer;
        }}
        .hover-bg:hover {{
            background-color: #f9fafb;
        }}
        .hidden {{
            display: none;
        }}
        .flex {{
            display: flex;
        }}
        .flex-1 {{
            flex: 1;
        }}
        .gap-4 {{
            gap: 1rem;
        }}
        .space-y-4 > * + * {{
            margin-top: 1rem;
        }}
        .text-red-700 {{
            color: #b91c1c;
        }}
        .text-gray-700 {{
            color: #374151;
        }}
        .text-gray-800 {{
            color: #1f2937;
        }}
        .bg-gray-50 {{
            background-color: #f9fafb;
        }}
        .bg-white {{
            background-color: white;
        }}
        .whitespace-pre-wrap {{
            white-space: pre-wrap;
        }}
        .uppercase {{
            text-transform: uppercase;
        }}
        .line-clamp-2 {{
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="mb-8">
            <h1>LLM Security Assessment Report</h1>
            <p class="text-sm text-gray-500">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <!-- Compact Summary Cards -->
        <div class="grid grid-cols-4 mb-8">
            <div class="stat-card stat-card-total">
                <div class="text-sm font-semibold mb-1 opacity-90">Total Tests</div>
                <div style="font-size: 1.875rem; font-weight: bold;">{stats['total']}</div>
            </div>
            <div class="stat-card stat-card-safe">
                <div class="text-sm font-semibold mb-1 opacity-90">Safe Responses</div>
                <div style="font-size: 1.875rem; font-weight: bold;">{stats['safe_count']}</div>
                <div class="text-sm opacity-90">{stats['safe_percent']}%</div>
            </div>
            <div class="stat-card stat-card-unsafe">
                <div class="text-sm font-semibold mb-1 opacity-90">Unsafe Responses</div>
                <div style="font-size: 1.875rem; font-weight: bold;">{stats['unsafe_count']}</div>
                <div class="text-sm opacity-90">{stats['unsafe_percent']}%</div>
            </div>
            <div class="stat-card stat-card-error">
                <div class="text-sm font-semibold mb-1 opacity-90">Errors</div>
                <div style="font-size: 1.875rem; font-weight: bold;">{stats['error_count']}</div>
                <div class="text-sm opacity-90">{stats['error_percent']}%</div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-2 mb-8">
            <!-- Classification Pie Chart -->
            <div class="card">
                <h2>Classification Breakdown</h2>
                <div style="position: relative; height: 300px;">
                    <canvas id="classificationChart"></canvas>
                </div>
            </div>

            <!-- Confidence Distribution -->
            <div class="card">
                <h2>Confidence Distribution</h2>
                <div style="position: relative; height: 300px;">
                    <canvas id="confidenceChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Unsafe Examples Table -->
        <div class="card">
            <div class="flex" style="justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h2 style="margin-bottom: 0;">
                    Unsafe Examples
                    <span class="text-sm font-semibold text-gray-600" style="font-weight: normal;">(<span id="filtered-count">{stats['unsafe_count']}</span> of {stats['unsafe_count']} shown)</span>
                </h2>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <label for="label-filter" class="text-sm text-gray-700">Filter by label:</label>
                    <select id="label-filter" onchange="filterByLabel()" style="padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem;">
                        <option value="all">All Labels</option>
                        {label_options}
                    </select>
                </div>
            </div>
            
            <div class="border rounded-lg overflow-hidden">
                {unsafe_table_html}
            </div>
        </div>
    </div>

    <script>
        // Toggle detail view
        function toggleDetail(id) {{
            const detail = document.getElementById('detail-' + id);
            const icon = document.getElementById('icon-' + id);
            detail.classList.toggle('hidden');
            icon.textContent = detail.classList.contains('hidden') ? '▼' : '▲';
        }}

        // Filter unsafe examples by original label
        function filterByLabel() {{
            const filter = document.getElementById('label-filter').value;
            const items = document.querySelectorAll('.unsafe-item');
            let visibleCount = 0;
            
            items.forEach(item => {{
                const label = item.getAttribute('data-original-label');
                if (filter === 'all' || label === filter) {{
                    item.style.display = 'block';
                    visibleCount++;
                }} else {{
                    item.style.display = 'none';
                }}
            }});
            
            document.getElementById('filtered-count').textContent = visibleCount;
        }}

        // Initialize charts
        function initCharts() {{
            // Classification Pie Chart
            new Chart(document.getElementById('classificationChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Safe', 'Unsafe', 'Error'],
                    datasets: [{{
                        data: [{stats['safe_count']}, {stats['unsafe_count']}, {stats['error_count']}],
                        backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                padding: 15,
                                font: {{
                                    size: 12
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // Confidence Distribution Chart
            new Chart(document.getElementById('confidenceChart'), {{
                type: 'bar',
                data: {{
                    labels: ['High', 'Medium', 'Low', 'Unknown'],
                    datasets: [{{
                        label: 'Evaluations',
                        data: [
                            {stats['by_confidence']['high']},
                            {stats['by_confidence']['medium']},
                            {stats['by_confidence']['low']},
                            {stats['by_confidence']['unknown']}
                        ],
                        backgroundColor: ['#3b82f6', '#6366f1', '#8b5cf6', '#9ca3af'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                stepSize: 1
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initCharts);
    </script>
</body>
</html>"""
        
        return html_doc
