from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
import json, os

app = Flask(__name__)
CORS(app)

# 🔹 Get MongoDB URI from environment variable (Render/Atlas)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client["RailwaySystem"]
    collection = db["Trains"]
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST", "OPTIONS", "GET"])
def run_command():
    if request.method == "GET":
        return jsonify({"status": "error", "result": "Use POST to execute commands."})
    
    try:
        command = request.form.get("command", "").strip()
        if not command:
            return jsonify({"status": "error", "result": "No command provided."})

        cmd_lower = command.lower()

        # ✅ Insert One
        if "insertone" in cmd_lower:
            json_str = command[command.index("{"):command.rindex("}")+1]
            data = json.loads(json_str)
            result = collection.insert_one(data)
            return jsonify({"status": "success", "result": f"Inserted ID: {str(result.inserted_id)}"})

        # ✅ Insert Many
        elif "insertmany" in cmd_lower:
            json_str = command[command.index("["):command.rindex("]")+1]
            data = json.loads(json_str)
            result = collection.insert_many(data)
            return jsonify({"status": "success", "result": f"Inserted {len(result.inserted_ids)} documents"})

        # ✅ Find
        elif "find" in cmd_lower:
            if "{" in command:
                json_str = command[command.index("{"):command.rindex("}")+1]
                query = json.loads(json_str)
                docs = list(collection.find(query, {"_id": 0}))
            else:
                docs = list(collection.find({}, {"_id": 0}))
            return jsonify({"status": "success", "result": docs})

        # ✅ Update One
        elif "updateone" in cmd_lower:
            cleaned = command.replace("\n", " ").replace("(", " ").replace(")", " ").strip()
            json_blocks, brace_stack, start_idx = [], [], None

            for i, ch in enumerate(cleaned):
                if ch == "{":
                    if not brace_stack:
                        start_idx = i
                    brace_stack.append("{")
                elif ch == "}":
                    if brace_stack:
                        brace_stack.pop()
                        if not brace_stack and start_idx is not None:
                            json_blocks.append(cleaned[start_idx:i+1])
                            start_idx = None

            if len(json_blocks) < 2:
                return jsonify({"status": "error", "result": f"Could not find two JSON blocks in: {cleaned}"})

            filter_data = json.loads(json_blocks[0])
            update_data = json.loads(json_blocks[1])

            res = collection.update_one(filter_data, update_data)
            return jsonify({
                "status": "success",
                "result": f"Matched: {res.matched_count}, Modified: {res.modified_count}"
            })

        # ✅ Delete Many
        elif "deletemany" in cmd_lower:
            json_str = command[command.index("{"):command.rindex("}")+1]
            query = json.loads(json_str)
            res = collection.delete_many(query)
            return jsonify({"status": "success", "result": f"Deleted {res.deleted_count} documents"})

        # ✅ Delete One
        elif "deleteone" in cmd_lower:
            json_str = command[command.index("{"):command.rindex("}")+1]
            query = json.loads(json_str)
            res = collection.delete_one(query)
            return jsonify({"status": "success", "result": f"Deleted {res.deleted_count} document"})

        # ✅ Count
        elif "countdocuments" in cmd_lower:
            count = collection.count_documents({})
            return jsonify({"status": "success", "result": f"Total documents: {count}"})

        # ✅ Sort
        elif "sort" in cmd_lower:
            field = command[command.index("{")+1:command.rindex("}")].split(":")[0].strip().replace('"', "")
            docs = list(collection.find({}, {"_id": 0}).sort(field, 1))
            return jsonify({"status": "success", "result": docs})

        else:
            return jsonify({"status": "error", "result": "Unsupported or invalid command!"})

    except Exception as e:
        return jsonify({"status": "error", "result": str(e)})

if __name__ == "__main__":
    # Render provides PORT automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
