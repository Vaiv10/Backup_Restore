from flask import Flask, render_template, request, jsonify
import os
import subprocess
import shutil
import tarfile
import stat

app = Flask(__name__)

# Function to remove read-only files
def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Backup repository function
def backup_repository(repo_url, backup_dir):
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    temp_clone_dir = os.path.join(backup_dir, repo_name + "_temp")

    try:
        if os.path.exists(temp_clone_dir):
            subprocess.run(["git", "-C", temp_clone_dir, "pull"], check=True)
        else:
            subprocess.run(["git", "clone", repo_url, temp_clone_dir], check=True)

        archive_path = os.path.join(backup_dir, f"{repo_name}.tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(temp_clone_dir, arcname=repo_name)

        return f"Backup completed: {archive_path}"
    finally:
        if os.path.exists(temp_clone_dir):
            shutil.rmtree(temp_clone_dir, onerror=remove_readonly)

# Restore repository function
def restore_repository(backup_file, restore_dir):
    if not os.path.exists(backup_file):
        return f"Error: Backup file {backup_file} does not exist."

    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(path=restore_dir)

    return f"Restore completed. Repository available in {restore_dir}."

# Flask route to serve the homepage
@app.route("/")
def home():
    return render_template("index.html")

# Flask route to handle backup
@app.route("/backup", methods=["POST"])
def backup():
    data = request.json
    repo_url = data.get("repo_url")
    backup_dir = data.get("backup_dir")
    if not repo_url or not backup_dir:
        return jsonify({"error": "Repository URL and Backup Directory are required!"}), 400

    try:
        result = backup_repository(repo_url, backup_dir)
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask route to handle restore
@app.route("/restore", methods=["POST"])
def restore():
    data = request.json
    backup_file = data.get("backup_file")
    restore_dir = data.get("restore_dir")
    if not backup_file or not restore_dir:
        return jsonify({"error": "Backup File and Restore Directory are required!"}), 400

    try:
        result = restore_repository(backup_file, restore_dir)
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
