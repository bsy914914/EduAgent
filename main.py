"""
University AI Lesson Planner - Main Entry Point

This is the main launcher for the University AI Lesson Planning System.
It initializes and starts the Gradio web interface.

Usage:
    python main.py [--port PORT] [--share]

Examples:
    python main.py                  # Run on default port 7860
    python main.py --port 8080      # Run on custom port
    python main.py --share          # Create public link
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from interface.gradio_app import create_app


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="University AI Lesson Planning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Run with default settings
  python main.py --port 8080        Run on custom port
  python main.py --share            Create public share link
  python main.py --debug            Enable debug mode
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=7861,
        help='Port to run the server on (default: 7860)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default="0.0.0.0",
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create a public share link'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--no-queue',
        action='store_true',
        help='Disable request queueing'
    )
    
    return parser.parse_args()


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = {
        'gradio': 'gradio',
        'langchain': 'langchain',
        'dashscope': 'dashscope',
    }
    
    optional_packages = {
        'docx': 'python-docx (for Word export)',
        'PIL': 'Pillow (for image processing)',
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_required.append(package_name)
    
    # Check optional packages
    for module_name, package_name in optional_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_optional.append(package_name)
    
    # Report missing packages
    if missing_required:
        print("❌ Missing required packages:")
        for pkg in missing_required:
            print(f"   - {pkg}")
        print("\nInstall with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print("⚠️  Optional packages not installed:")
        for pkg in missing_optional:
            print(f"   - {pkg}")
        print("\nInstall with: pip install " + " ".join([p.split()[0] for p in missing_optional]))
        print("Note: System will work without these, but some features may be limited.\n")
    
    return True


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          🎓 大学AI教案生成系统                                  ║
    ║          University AI Lesson Planning System                 ║
    ║                                                               ║
    ║          基于 LangGraph + 通义千问                             ║
    ║          Powered by LangGraph & Qwen                          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point"""
    # Print banner
    print_banner()
    
    # Parse arguments
    args = parse_args()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        sys.exit(1)
    
    print("✅ All required dependencies are installed.\n")
    
    # Create application
    print("🚀 Starting application...")
    try:
        app = create_app()
        
        # Configure queue
        if not args.no_queue:
            app.queue()
        
        # Launch application
        print(f"\n{'='*60}")
        print(f"Server starting on http://{args.host}:{args.port}")
        if args.share:
            print("Creating public share link...")
        print(f"{'='*60}\n")
        
        app.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            debug=args.debug,
            show_error=True,
            quiet=False
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()