# main.py
import os
from pyngrok import ngrok
from app import app  # Import your actual app with routes and models

if __name__ == "__main__":
    # Start ngrok only once with Flask's reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Optional: disconnect any leftover tunnels
        for tunnel in ngrok.get_tunnels():
            ngrok.disconnect(tunnel.public_url)

        # Start ngrok tunnel
        public_url = ngrok.connect(5000, proto="http")
        print(f"ngrok tunnel running at: {public_url}")
        print("Open this URL in your browser to access the Help Ticket System externally.")

    # Run Flask app on all interfaces
    app.run(host="0.0.0.0", port=5000, debug=True)
