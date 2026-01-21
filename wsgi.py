"""
WSGI entry point for production deployment (Gunicorn/Render)
"""

from app.dashboard import app

if __name__ == "__main__":
    app.run()
