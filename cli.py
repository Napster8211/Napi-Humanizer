"""Command Line Interface for NapsterTec Text Intelligence Engine."""

import sys
import argparse
from typing import Optional

from core.config import get_config
from core.schemas import RewriteRequest, AnalysisRequest, EditingMode, EditingIntensity
from core.orchestrator import get_orchestrator
from core.analyzer import get_analyzer
from editing.modes import MODE_METADATA, INTENSITY_METADATA


def _read_input(args_text: Optional[str], file_path: Optional[str]) -> str:
    """Read text from file, command argument, or standard input."""
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    if args_text:
        return args_text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Error: No text provided. Pass text as argument, --file, or pipe via stdin.", file=sys.stderr)
    sys.exit(1)


def cmd_rewrite(args: argparse.Namespace):
    """Handle text rewrite command."""
    text = _read_input(args.text, args.file)

    mode_val = EditingMode(args.mode.lower())
    intensity_val = EditingIntensity(args.intensity.lower())

    req = RewriteRequest(
        text=text,
        mode=mode_val,
        intensity=intensity_val,
        tone=args.tone,
        audience=args.audience,
        instructions=args.instructions,
        fallback_to_local=not args.no_fallback,
    )

    orchestrator = get_orchestrator()
    try:
        response = orchestrator.rewrite(req)
    except Exception as exc:
        print(f"Error during rewrite: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(response.revised_text)
        print(f"Revised text saved to {args.output}")
    else:
        print(response.revised_text)

    if args.verbose:
        print("\n--- Diagnostic Metadata ---", file=sys.stderr)
        print(f"Request ID: {response.request_id}", file=sys.stderr)
        print(f"Provider: {response.provider} ({response.model})", file=sys.stderr)
        print(f"Duration: {response.duration_ms} ms", file=sys.stderr)
        if response.is_fallback:
            print("Notice: Fallback to local polish was triggered.", file=sys.stderr)
        if response.warnings:
            print(f"Warnings ({len(response.warnings)}):", file=sys.stderr)
            for w in response.warnings:
                print(f" - {w}", file=sys.stderr)
        if response.change_summary:
            cs = response.change_summary
            print(f"Changes: +{cs.added_words} / -{cs.removed_words} words (net {cs.net_word_change})", file=sys.stderr)


def cmd_analyze(args: argparse.Namespace):
    """Handle text analysis command."""
    text = _read_input(args.text, args.file)
    analyzer = get_analyzer()
    res = analyzer.analyze(text)
    m = res.metrics

    print("=== Text Intelligence Analysis ===")
    print(f"Characters: {m.char_count} | Words: {m.word_count} | Sentences: {m.sentence_count} | Paragraphs: {m.paragraph_count}")
    print(f"Flesch Reading Ease: {m.flesch_reading_ease} (Higher is easier)")
    print(f"Flesch-Kincaid Grade: {m.flesch_kincaid_grade}")
    print(f"Lexical Diversity: {m.lexical_diversity}")
    print(f"Estimated Reading Time: {m.reading_time_minutes} minutes")
    print(f"\nProtected Entities ({len(res.protected_spans)}):")
    for s in res.protected_spans[:10]:
        print(f" - [{s.span_type.upper()}] {s.text}")
    if len(res.protected_spans) > 10:
        print(f"   ... and {len(res.protected_spans) - 10} more.")
    print(f"\nNote: {m.metric_notice}")


def cmd_modes(args: argparse.Namespace):
    """List supported editing modes and intensities."""
    print("=== Supported Editing Modes ===")
    for mode, meta in MODE_METADATA.items():
        print(f"\n- {meta['title']} (`{mode.value}`):")
        print(f"  {meta['description']}")

    print("\n=== Editing Intensities ===")
    for intensity, meta in INTENSITY_METADATA.items():
        print(f"- {meta['title']} (`{intensity.value}`): {meta['guidance']}")


def cmd_serve(args: argparse.Namespace):
    """Launch web UI service."""
    cfg = get_config()
    host = args.host or cfg.host
    port = args.port or cfg.port

    if args.prod:
        from waitress import serve
        from web_ui import create_app
        print(f"Starting Waitress production server on http://{host}:{port}")
        serve(create_app(), host=host, port=port, threads=4)
    else:
        from web_ui import create_app
        print(f"Starting development server on http://{host}:{port}")
        app = create_app()
        app.run(host=host, port=port, debug=cfg.debug)


def main():
    """Main CLI parser."""
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="NapsterTec Text Intelligence Engine — Modular Writing and Text Refinement CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to execute")

    # Rewrite subcommand
    p_rewrite = subparsers.add_parser("rewrite", help="Rewrite and polish text")
    p_rewrite.add_argument("text", nargs="?", help="Input text string")
    p_rewrite.add_argument("-f", "--file", help="Path to input text file")
    p_rewrite.add_argument("-o", "--output", help="Path to save revised text output")
    p_rewrite.add_argument("-m", "--mode", default="proofread", choices=[m.value for m in EditingMode], help="Editing mode")
    p_rewrite.add_argument("-i", "--intensity", default="balanced", choices=[i.value for i in EditingIntensity], help="Editing intensity")
    p_rewrite.add_argument("--tone", help="Target tone (e.g. authoritative, empathetic)")
    p_rewrite.add_argument("--audience", help="Target audience (e.g. executives, general public)")
    p_rewrite.add_argument("--instructions", help="Custom refinement instructions")
    p_rewrite.add_argument("--no-fallback", action="store_true", help="Fail instead of falling back to local polish on provider error")
    p_rewrite.add_argument("-v", "--verbose", action="store_true", help="Show diagnostic warnings and metrics")

    # Analyze subcommand
    p_analyze = subparsers.add_parser("analyze", help="Analyze structural metrics and protected entities")
    p_analyze.add_argument("text", nargs="?", help="Input text string")
    p_analyze.add_argument("-f", "--file", help="Path to input text file")

    # Modes subcommand
    subparsers.add_parser("modes", help="Display available editing modes and intensity levels")

    # Serve subcommand
    p_serve = subparsers.add_parser("serve", help="Launch web UI workspace")
    p_serve.add_argument("--host", default=None, help="Host address to bind")
    p_serve.add_argument("-p", "--port", type=int, default=None, help="Port to bind")
    p_serve.add_argument("--prod", action="store_true", help="Use Waitress production WSGI server")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "rewrite": cmd_rewrite,
        "analyze": cmd_analyze,
        "modes": cmd_modes,
        "serve": cmd_serve,
    }
    dispatch[args.subcommand](args)


if __name__ == "__main__":
    main()
