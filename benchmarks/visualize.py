"""
Generate visualization graphs from benchmark results.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib not installed. Install with: pip install matplotlib")


def load_benchmark_results(results_file: Path) -> List[Dict]:
    """Load benchmark results from JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)


def create_indexing_speed_chart(results: List[Dict], output_file: Path):
    """Create chart showing indexing speed vs repo size."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    repo_names = [r['repo_name'][:20] for r in results]  # Truncate long names
    locs = [r['repo_size_loc'] for r in results]
    times = [r['index_time_seconds'] for r in results]
    speeds = [loc / time if time > 0 else 0 for loc, time in zip(locs, times)]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Chart 1: Indexing time vs LOC
    ax1.bar(repo_names, times, color='steelblue', alpha=0.7)
    ax1.set_xlabel('Repository', fontweight='bold')
    ax1.set_ylabel('Indexing Time (seconds)', fontweight='bold')
    ax1.set_title('Indexing Time by Repository', fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, (time, loc) in enumerate(zip(times, locs)):
        ax1.text(i, time, f'{time:.2f}s\n{loc:,} LOC', 
                ha='center', va='bottom', fontsize=9)
    
    # Chart 2: Indexing speed (LOC/s)
    ax2.bar(repo_names, speeds, color='forestgreen', alpha=0.7)
    ax2.set_xlabel('Repository', fontweight='bold')
    ax2.set_ylabel('Speed (LOC/second)', fontweight='bold')
    ax2.set_title('Indexing Speed (Higher is Better)', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, speed in enumerate(speeds):
        ax2.text(i, speed, f'{speed:,.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Created: {output_file}")
    plt.close()


def create_query_latency_chart(results: List[Dict], output_file: Path):
    """Create chart showing query latencies."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    repo_names = [r['repo_name'][:20] for r in results]
    p50s = [r['query_p50_ms'] for r in results]
    p95s = [r['query_p95_ms'] for r in results]
    p99s = [r['query_p99_ms'] for r in results]
    
    x = range(len(repo_names))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.bar([i - width for i in x], p50s, width, label='p50', 
           color='lightgreen', alpha=0.8)
    ax.bar([i for i in x], p95s, width, label='p95', 
           color='orange', alpha=0.8)
    ax.bar([i + width for i in x], p99s, width, label='p99', 
           color='red', alpha=0.8)
    
    ax.set_xlabel('Repository', fontweight='bold')
    ax.set_ylabel('Latency (milliseconds)', fontweight='bold')
    ax.set_title('Query Latency by Percentile', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(repo_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add target line at 100ms (good performance threshold)
    ax.axhline(y=100, color='blue', linestyle='--', alpha=0.5, 
               label='Target (100ms)')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Created: {output_file}")
    plt.close()


def create_comparison_chart(results: List[Dict], output_file: Path):
    """Create comprehensive comparison chart."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    repo_names = [r['repo_name'][:20] for r in results]
    files = [r['file_count'] for r in results]
    symbols = [r['symbol_count'] for r in results]
    index_sizes = [r['index_size_mb'] for r in results]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Chart 1: File count
    ax1.bar(repo_names, files, color='steelblue', alpha=0.7)
    ax1.set_ylabel('File Count', fontweight='bold')
    ax1.set_title('Files Indexed', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)
    for i, f in enumerate(files):
        ax1.text(i, f, f'{f:,}', ha='center', va='bottom', fontsize=9)
    
    # Chart 2: Symbol count
    ax2.bar(repo_names, symbols, color='forestgreen', alpha=0.7)
    ax2.set_ylabel('Symbol Count', fontweight='bold')
    ax2.set_title('Symbols Extracted', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(axis='y', alpha=0.3)
    for i, s in enumerate(symbols):
        ax2.text(i, s, f'{s:,}', ha='center', va='bottom', fontsize=9)
    
    # Chart 3: Index size
    ax3.bar(repo_names, index_sizes, color='purple', alpha=0.7)
    ax3.set_ylabel('Size (MB)', fontweight='bold')
    ax3.set_title('Index Size', fontsize=12, fontweight='bold')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(axis='y', alpha=0.3)
    for i, size in enumerate(index_sizes):
        ax3.text(i, size, f'{size:.2f}', ha='center', va='bottom', fontsize=9)
    
    # Chart 4: Symbols per file
    symbols_per_file = [s/f if f > 0 else 0 for s, f in zip(symbols, files)]
    ax4.bar(repo_names, symbols_per_file, color='darkorange', alpha=0.7)
    ax4.set_ylabel('Symbols/File', fontweight='bold')
    ax4.set_title('Average Symbols per File', fontsize=12, fontweight='bold')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    for i, spf in enumerate(symbols_per_file):
        ax4.text(i, spf, f'{spf:.1f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Created: {output_file}")
    plt.close()


def generate_markdown_table(results: List[Dict]) -> str:
    """Generate a markdown table from benchmark results."""
    lines = [
        "## Benchmark Results\n",
        "| Repository | LOC | Files | Symbols | Index Time | Index Size | p50 Latency | p95 Latency |",
        "|-----------|-----|-------|---------|------------|------------|-------------|-------------|",
    ]
    
    for r in results:
        lines.append(
            f"| {r['repo_name']} | {r['repo_size_loc']:,} | {r['file_count']:,} | "
            f"{r['symbol_count']:,} | {r['index_time_seconds']:.2f}s | "
            f"{r['index_size_mb']:.2f} MB | {r['query_p50_ms']:.2f} ms | "
            f"{r['query_p95_ms']:.2f} ms |"
        )
    
    # Add averages if multiple repos
    if len(results) > 1:
        avg_loc = sum(r['repo_size_loc'] for r in results) / len(results)
        avg_files = sum(r['file_count'] for r in results) / len(results)
        avg_symbols = sum(r['symbol_count'] for r in results) / len(results)
        avg_time = sum(r['index_time_seconds'] for r in results) / len(results)
        avg_size = sum(r['index_size_mb'] for r in results) / len(results)
        avg_p50 = sum(r['query_p50_ms'] for r in results) / len(results)
        avg_p95 = sum(r['query_p95_ms'] for r in results) / len(results)
        
        lines.append(
            f"| **AVERAGE** | **{avg_loc:,.0f}** | **{avg_files:,.0f}** | "
            f"**{avg_symbols:,.0f}** | **{avg_time:.2f}s** | "
            f"**{avg_size:.2f} MB** | **{avg_p50:.2f} ms** | "
            f"**{avg_p95:.2f} ms** |"
        )
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate benchmark visualizations")
    parser.add_argument("results_file", help="JSON file with benchmark results")
    parser.add_argument("--output-dir", "-o", default="benchmarks", 
                       help="Output directory for graphs")
    parser.add_argument("--no-graphs", action="store_true",
                       help="Skip graph generation (table only)")
    
    args = parser.parse_args()
    
    results_file = Path(args.results_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        sys.exit(1)
    
    print(f"📊 Loading benchmark results from {results_file}")
    results = load_benchmark_results(results_file)
    
    if not results:
        print("❌ No benchmark results found")
        sys.exit(1)
    
    print(f"✅ Loaded {len(results)} benchmark result(s)")
    
    # Generate markdown table
    print("\n📝 Generating markdown table...")
    markdown_table = generate_markdown_table(results)
    print(markdown_table)
    
    table_file = output_dir / "benchmark_table.md"
    with open(table_file, 'w') as f:
        f.write(markdown_table)
    print(f"\n✅ Saved table to: {table_file}")
    
    # Generate graphs
    if not args.no_graphs:
        if not MATPLOTLIB_AVAILABLE:
            print("\n⚠️  Skipping graphs (matplotlib not installed)")
            print("   Install with: pip install matplotlib")
        else:
            print("\n📈 Generating graphs...")
            create_indexing_speed_chart(results, output_dir / "indexing_speed.png")
            create_query_latency_chart(results, output_dir / "query_latency.png")
            create_comparison_chart(results, output_dir / "comparison.png")
            print("\n✅ All graphs generated")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
