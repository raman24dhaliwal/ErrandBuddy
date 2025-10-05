from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow requests from Kivy frontend

# temporary demo "users database"
users = {
    "raman": "1234",
    "laiba": "abcd"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "ErrandBuddy API is running!"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # check if user exists and password matches
    if username in users and users[username] == password:
        return jsonify({"status": "success", "message": "Login successful!"})
    else:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

if __name__ == "__main__":
    app.run(debug=True)
