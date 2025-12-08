#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse

PORT = 5000
IMGBB_KEY = os.environ.get('IMGBB_KEY', '')

if not IMGBB_KEY:
    print("WARNING: IMGBB_KEY environment variable is not set!")
    print("   The ImgBB upload feature will not work without it.")
    print("   Get a free API key at imgbb.com and set it in your Replit secrets.")
    print()

def validate_cookie(cookie):
    """Validate Roblox cookie and fetch user data from official Roblox APIs"""
    result = {
        "success": False,
        "user": "Unknown",
        "display": "Unknown",
        "userid": 0,
        "robux": 0,
        "premium": "No",
        "headshot": ""
    }
    
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "Accept": "application/json"
    }
    
    try:
        # Step 1: Get authenticated user info (username, display name, user ID)
        req = urllib.request.Request(
            "https://users.roblox.com/v1/users/authenticated",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            user_data = json.loads(response.read().decode())
            result["userid"] = user_data.get("id", 0)
            result["user"] = user_data.get("name", "Unknown")
            result["display"] = user_data.get("displayName", result["user"])
            result["success"] = True
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return result
    
    user_id = result["userid"]
    if not user_id:
        return result
    
    # Step 2: Get Robux balance
    try:
        req = urllib.request.Request(
            f"https://economy.roblox.com/v1/users/{user_id}/currency",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            robux_data = json.loads(response.read().decode())
            result["robux"] = robux_data.get("robux", 0)
    except Exception as e:
        print(f"Error fetching robux: {e}")
    
    # Step 3: Get Premium status
    try:
        req = urllib.request.Request(
            f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            premium_data = json.loads(response.read().decode())
            result["premium"] = "Yes" if premium_data else "No"
    except Exception as e:
        print(f"Error fetching premium status: {e}")
    
    # Step 4: Get headshot thumbnail
    try:
        req = urllib.request.Request(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png",
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            thumb_data = json.loads(response.read().decode())
            if thumb_data.get("data") and len(thumb_data["data"]) > 0:
                result["headshot"] = thumb_data["data"][0].get("imageUrl", "")
    except Exception as e:
        print(f"Error fetching headshot: {e}")
    
    return result


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open('index.html', 'r') as f:
                content = f.read()
            
            content = content.replace(
                'const IMGBB_KEY = "YOUR_IMGBB_KEY_HERE";',
                f'const IMGBB_KEY = "{IMGBB_KEY}";'
            )
            
            self.wfile.write(content.encode())
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/validate-cookie':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                cookie = data.get('cookie', '')
                
                if not cookie:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No cookie provided"}).encode())
                    return
                
                result = validate_cookie(cookie)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Server running at http://0.0.0.0:{PORT}/")
    print(f"API endpoint: POST /api/validate-cookie")
    httpd.serve_forever()
