"""
main.py — CardioShield AI entry point.

Usage:
  python main.py --train    # Train all models (required first step)
  python main.py --server   # Start Flask server
  python main.py            # Train + start server
"""
import sys, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src", "data"))


def train():
    from src.train_models import run as train_run
    metrics = train_run()

    # Copy report PNGs to static/images for web access
    import shutil
    reports = os.path.join(BASE_DIR, "reports")
    static_img = os.path.join(BASE_DIR, "app", "frontend", "static", "images")
    os.makedirs(static_img, exist_ok=True)
    for fname in os.listdir(reports):
        if fname.endswith(".png"):
            shutil.copy(os.path.join(reports, fname), os.path.join(static_img, fname))
    print("[main] Report images copied → static/images/")
    return metrics


def serve():
    from app.backend.app import create_app
    app = create_app()
    host  = os.environ.get("FLASK_HOST", "127.0.0.1")
    port  = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    print(f"\n  CardioShield AI — http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--train" in args:
        train()
    elif "--server" in args:
        serve()
    else:
        # Default: train then serve
        train()
        serve()
