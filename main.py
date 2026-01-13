# main.py
import os
from pyngrok import ngrok
from app import app  # Import your actual app with routes and models

if __name__ == "__main__":
    app.run(debug=True)

#from pyngrok import ngrok
#if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
 #   try:        
  #      ngrok.kill()
   #     print("Cleaned up existing ngrok tunnels")
    #except Exception as e:
     #   print(f"Note: {e}")
    
    #try:
     #   public_url = ngrok.connect(5000, proto="http")
      #  print(f"ngrok tunnel running at: {public_url}")
       # print("Open this URL in your browser to access the Help Ticket System externally.")
    #except Exception as e:
     #   print(f"Warning: Could not start ngrok tunnel: {e}")
      #  print("Running Flask locally only...")
      # Run Flask app on all interfaces
    #app.run(host="0.0.0.0", port=5000, debug=True)