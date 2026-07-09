"""
CLI entry point for codesearch.
"""

import sys
import argparse
import json
from pathlib import Path

from .storage.db import Database
from .config import get_db_path
from .indexer.indexer import Indexer
from .query.search import SearchEngine
from .log import logger


def format_result_human(result, index: int):
    """Format a single result for human-readable output with enhanced display."""
    output = []

    # Header with file, line, score, and match type
    header_parts = [f"{result.file_path}:{result.line_number}"]

    if result.language:
        header_parts.append(f"[{result.language}]")

    header_parts.append(f"(score={result.score:.1f})")

    if result.match_type != "text":
        header_parts.append(f"[{result.match_type}]")

    output.append(f"\n{index}. " + " ".join(header_parts))

    # Add symbol metadata if available
    if result.symbol_name:
        symbol_info = f"   ├─ Symbol: {result.symbol_name}"
        if result.symbol_kind:
            symbol_info += f" ({result.symbol_kind})"
        output.append(symbol_info)

    # Add snippet with better formatting
    if result.context_lines:
        # Enhanced snippet with context
        output.append("   └─ Code:")
        for line in result.context_lines:
            output.append(f"      {line}")
    else:
        # Simple snippet
        output.append("   └─ Snippet:")
        for line in result.snippet.splitlines():
            output.append(f"      {line}")

    return "\n".join(output)


def command_index(args):
    """Handle the index command."""
    repo_path = Path(args.repo_path)

    if not repo_path.exists():
        print(f"Error: Repository not found: {repo_path}", file=sys.stderr)
        return 1

    print(f"🔍 Indexing repository: {repo_path}")

    # Initialize database
    db_path = get_db_path()
    db = Database(db_path)
    db.connect()
    db.initialize_schema()

    # Create indexer and run
    indexer = Indexer(db)

    try:
        stats = indexer.index_repository(
            repo_path, force=args.force if hasattr(args, "force") else False
        )

        # Display results with detailed incremental stats
        print("\n✅ Indexing complete!")
        print(f"   Files scanned: {stats['files_scanned']}")

        # Show detailed breakdown if we have the new stats format
        if "files_new" in stats or "files_updated" in stats:
            print(f"   Files new: {stats.get('files_new', 0)}")
            print(f"   Files updated: {stats.get('files_updated', 0)}")
            print(f"   Files unchanged: {stats.get('files_unchanged', 0)}")
            if stats.get("files_deleted", 0) > 0:
                print(f"   Files deleted: {stats.get('files_deleted', 0)}")
        else:
            # Fallback for old stats format
            print(f"   Files indexed: {stats.get('files_indexed', 0)}")

        print(f"   Files skipped: {stats['files_skipped']}")
        if stats.get("files_failed", 0) > 0:
            print(f"   Files failed: {stats['files_failed']}")
        print(f"   Chunks created: {stats['chunks_created']}")
        if stats.get("symbols_extracted", 0) > 0:
            print(f"   Symbols extracted: {stats['symbols_extracted']}")
        print(f"   Duration: {stats['duration_seconds']}s")

        # Get and display database size
        db_stats = db.get_stats()
        total_size_mb = db_stats["db_size_bytes"] / (1024 * 1024)
        print(
            f"   Total in DB: {db_stats['total_files']} files, "
            f"{db_stats['total_symbols']} symbols, {total_size_mb:.2f} MB"
        )
        print(f"   Database: {db_path}")

        return 0

    except Exception as e:
        print(f"❌ Indexing failed: {e}", file=sys.stderr)
        logger.error(f"Indexing error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


def command_query(args):
    """Handle the query command."""
    query_str = args.query

    # Initialize database
    db_path = get_db_path()
    if not db_path.exists():
        print("❌ No index found. Run 'codesearch index <repo>' first.", file=sys.stderr)
        return 1

    db = Database(db_path)
    db.connect()

    # Create search engine
    search = SearchEngine(db.conn)

    try:
        results = search.search(query_str, topk=args.topk)

        # Enhance results with context if requested
        if args.context and not args.json:
            for result in results:
                snippet, context = search.get_enhanced_snippet(
                    result.file_path, result.line_number, context_lines=args.context
                )
                if context:
                    result.context_lines = context

        if args.json:
            # JSON output
            output = {
                "query": query_str,
                "total_results": len(results),
                "results": [r.to_dict() for r in results],
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            if not results:
                print(f"No results found for: {query_str}")
            else:
                print(f"\n🔍 Search results for: {query_str}")
                print(f"Found {len(results)} results:\n")
                print("=" * 80)

                for i, result in enumerate(results, 1):
                    print(format_result_human(result, i))

                print("\n" + "=" * 80)

        return 0

    except Exception as e:
        print(f"❌ Search failed: {e}", file=sys.stderr)
        logger.error(f"Search error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


def command_stats(args):
    """Handle the stats command."""
    db_path = get_db_path()

    if not db_path.exists():
        print("❌ No index found. Run 'codesearch index <repo>' first.", file=sys.stderr)
        return 1

    db = Database(db_path)
    db.connect()

    try:
        stats = db.get_stats()

        print("\n📊 Index Statistics")
        print("=" * 60)
        print(f"\nDatabase: {db_path}")
        print(f"Size: {stats['db_size_bytes'] / 1024 / 1024:.2f} MB")

        print("\n📁 Files:")
        print(f"   Total: {stats['total_files']}")

        if stats["files_by_language"]:
            print("\n   By language:")
            for lang, count in sorted(
                stats["files_by_language"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"      {lang}: {count}")

        print("\n🏷️  Symbols:")
        print(f"   Total: {stats['total_symbols']}")

        if stats["symbols_by_kind"]:
            print("\n   By kind:")
            for kind, count in sorted(
                stats["symbols_by_kind"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"      {kind}: {count}")

        if stats.get("metadata"):
            print("\n⚙️  Metadata:")
            for key, value in stats["metadata"].items():
                print(f"   {key}: {value}")

        print("\n" + "=" * 60)

        return 0

    except Exception as e:
        print(f"❌ Failed to get stats: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def command_purge(args):
    """Handle the purge command."""
    db_path = get_db_path()

    if not db_path.exists():
        print("No index found.")
        return 0

    # Ask for confirmation
    if not args.yes:
        response = input(f"⚠️  Are you sure you want to delete the index at {db_path}? (y/N): ")
        if response.lower() != "y":
            print("Cancelled.")
            return 0

    try:
        db_path.unlink()
        print(f"✅ Index deleted: {db_path}")
        return 0
    except Exception as e:
        print(f"❌ Failed to delete index: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="codesearch",
        description="Local GitHub-scale code search engine with symbol awareness",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index a repository")
    index_parser.add_argument("repo_path", type=str, help="Path to repository to index")
    index_parser.add_argument("--force", action="store_true", help="Force re-index all files")

    # Query command
    query_parser = subparsers.add_parser("query", help="Search indexed code")
    query_parser.add_argument("query", type=str, help="Search query")
    query_parser.add_argument("--json", action="store_true", help="Output as JSON")
    query_parser.add_argument("--topk", type=int, default=10, help="Number of results to return")
    query_parser.add_argument(
        "--context",
        type=int,
        default=0,
        help="Number of context lines to show around matches (0=disabled)",
    )

    # Stats command
    subparsers.add_parser("stats", help="Show index statistics")

    # Purge command
    purge_parser = subparsers.add_parser("purge", help="Delete the index")
    purge_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command handlers
    if args.command == "index":
        return command_index(args)
    elif args.command == "query":
        return command_query(args)
    elif args.command == "stats":
        return command_stats(args)
    elif args.command == "purge":
        return command_purge(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
