import sys
from pathlib import Path
from streamlit.web import cli as stcli

def main():
    """
    Hyper-RMA Portable Launcher
    Launch the Streamlit application directly from the executable.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller mode: Application root is in _internal or temp
        # We need to find where main.py is bundled.
        # In one-dir mode, src/main.py should be collected into the dist/src folder
        app_path = Path(sys.executable).parent / "src" / "main.py"
        
        # Ensure we can find packages
        sys.path.append(str(Path(sys.executable).parent))
    else:
        # Dev mode
        app_path = Path(__file__).parent / "main.py"

    # Configure sys.argv to emulate "streamlit run src/main.py --global.developmentMode=false"
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.headless=true",  # Prevent browser auto-spawn issues in some envs, but we usually want it.
        # Let's keep browser on for better UX, user can close it. 
        # Actually, user wants it "packagable".
        "--theme.base=dark",
        "--browser.gatherUsageStats=false" 
    ]
    
    # Run Streamlit
    print(f"Launching Hyper-RMA from: {app_path}")
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
