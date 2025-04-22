# from flask import Flask, render_template, request

# app = Flask(__name__)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         # Process the image upload and prediction
#         pass
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True)

# from flask import Flask, render_template, request
# import os
# import numpy as np
# from tensorflow.keras.models import load_model
# from werkzeug.utils import secure_filename
# from PIL import Image

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'static/uploads'

# # Load the pre-trained model (make sure 'model.h5' is in your project directory)
# model = load_model('model.h5')

# def prepare_image(img_path):
#     """
#     Open an image file, convert to RGB, resize it to the model's expected input,
#     normalize pixel values, and add a batch dimension.
#     """
#     img = Image.open(img_path).convert('RGB')
#     img = img.resize((224, 224))  # Update the size based on your model's requirements
#     img_array = np.array(img) / 255.0  # Normalize pixel values
#     img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
#     return img_array

# @app.route("/", methods=["GET", "POST"])
# def index():
#     tumor_type = None
#     confidence = None
#     filepath = None

#     if request.method == "POST":
#         # Ensure a file was submitted
#         if 'file' not in request.files or request.files['file'].filename == "":
#             return render_template("index.html", tumor_type=tumor_type, confidence=confidence, filepath=filepath)

#         file = request.files['file']
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         # Process the image and prepare it for prediction
#         img = prepare_image(filepath)

#         # Make prediction using the model
#         prediction = model.predict(img)
#         print("Prediction raw output:", prediction)  # Print raw model output to terminal

#         # For this example, assume a binary classification:
#         # Class 0: No Tumor, Class 1: Tumor Detected
#         class_idx = np.argmax(prediction, axis=1)[0]
#         confidence = float(np.max(prediction)) * 100

#         if class_idx == 1:
#             tumor_type = "Tumor Detected"
#         else:
#             tumor_type = "No Tumor Detected"

#         # Print result in terminal
#         print("Tumor Type:", tumor_type, "with confidence:", round(confidence, 2), "%")

#         # Render the template with results
#         return render_template("index.html", tumor_type=tumor_type, confidence=round(confidence, 2), filepath=filename)
    
#     return render_template("index.html", tumor_type=tumor_type, confidence=confidence, filepath=filepath)

# if __name__ == "__main__":
#     # Create upload folder if it doesn't exist
#     if not os.path.exists(app.config['UPLOAD_FOLDER']):
#         os.makedirs(app.config['UPLOAD_FOLDER'])
#     app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from PIL import Image
import os
import time
import numpy as np
import tensorflow as tf
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Load the pre-trained model
model = tf.keras.models.load_model('model_1_new.h5')

# PostgreSQL database connection
def get_db_connection():
    return psycopg2.connect(
        dbname="brain_tumor",
        user="postgres",
        password="iamadmin",
        host="localhost",
        port="5432"
    )

# Landing page
@app.route("/")
def landing():
    return render_template("landing.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check credentials in the database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))  # Redirect to dashboard
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

#signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already taken. Try a different one.", "danger")
            conn.close()
            return redirect(url_for("signup"))

        # Insert new user into the database
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        conn.close()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Main functionality (model prediction)
@app.route("/predict", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    tumor_type = None
    confidence = None
    filepath = None

    if request.method == "POST":
        if 'file' not in request.files or request.files['file'].filename == "":
            return render_template("index.html", tumor_type=tumor_type, confidence=confidence, filepath=filepath)

        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the image and prepare it for prediction
        img = prepare_image(filepath)

        # Make prediction using the model
        prediction = model.predict(img)
        labels = {0: "No Tumor", 1: "Meningioma", 2: "Pituitary", 3: "Glioma"}
        class_idx = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction)) * 100
        tumor_type = labels.get(class_idx, "Unknown")

        return render_template("index.html", tumor_type=tumor_type, confidence=round(confidence, 2), filepath=filename)

    return render_template("index.html", tumor_type=tumor_type, confidence=confidence, filepath=filepath)

TARGET_SIZE = (224, 224)
CLASS_LABELS = ['glioma', 'meningioma', 'notumor', 'pituitary']  # match model's training order


def prepare_image(img_path):
    """Preprocess the image for model prediction."""
    with Image.open(img_path).convert("RGB") as img:
        img = img.resize(TARGET_SIZE)
        img_array = np.array(img) / 255.0
        return np.expand_dims(img_array, axis=0)

from datetime import datetime

@app.route("/save_result", methods=["POST"])
def save_result():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get data from the form
    tumor_type = request.form.get("tumor_type")
    confidence = request.form.get("confidence")
    filepath = request.form.get("filepath")
    user_id = session["user_id"]

    # Save the result to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_history (user_id, prediction, confidence, image_path)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, tumor_type, confidence, filepath)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/history", methods=["GET"])
def show_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch user history from the database
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT prediction, confidence, datetime, image_path
        FROM user_history
        WHERE user_id = %s
        ORDER BY datetime DESC
        """,
        (user_id,)
    )
    history = cursor.fetchall()
    conn.close()

    return render_template("history.html", history=history)


# <---- apis ------> #

from flask import jsonify

@app.route("/api/getuser",methods=['GET'])
def getuser():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return {
        "username":session['username'],
        "user_id":session['user_id']
    }

@app.route("/api/history", methods=["GET"])
def history_api():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT prediction, confidence, datetime, image_path
        FROM user_history
        WHERE user_id = %s
        ORDER BY datetime DESC
        """,
        (user_id,)
    )
    history = cursor.fetchall()
    conn.close()

    return jsonify(history=history)

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

genai_api_key = os.getenv("GENAI_API_KEY")

import google.generativeai as genai

genai.configure(api_key=genai_api_key)

from PIL import Image
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
def is_brain_mri(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        prompt = "Is this image a brain MRI scan? Answer 'yes' or 'no'."
        response = gemini_model.generate_content([prompt, img], stream=False)
        img.close()  # manually close to avoid file lock on Windows
        result = response.text.strip().lower()
        return result.startswith("yes")
    except Exception as e:
        print(f"[MRI Verification Error] {e}")
        return False

def safe_delete(filepath):
    try:
        time.sleep(0.1)  # slight delay helps on Windows
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[Cleanup Error] Could not delete file: {e}")

@app.route('/model-info')
def model_info():
    return render_template('model_info.html')

#main functionality but an api.
@app.route("/api/predict", methods=["POST"])
def predict_api():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files or request.files['file'].filename == "":
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    if not is_brain_mri(filepath):
        safe_delete(filepath)
        return jsonify({"error": "The uploaded image is not a brain MRI scan."}), 400

    try:
        img_array = prepare_image(filepath)
        prediction = model.predict(img_array)
        
        predicted_class_idx = np.argmax(prediction, axis=1)[0]
        tumor_type = CLASS_LABELS[predicted_class_idx]
        confidence = round(float(np.max(prediction)) * 100, 2)

        return jsonify({
            "tumor_type": tumor_type,
            "confidence": confidence,
            "filepath": filename
        })

    except Exception as e:
        print(f"[Prediction Error] {e}")
        return jsonify({"error": "Prediction failed"}), 500

    finally:
        safe_delete(filepath)


#bulk scan
@app.route("/api/bulk_predict", methods=["POST"])
def bulk_predict():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    results = []

    for file in files:
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            if not is_brain_mri(filepath):
                results.append({
                    "filename": filename,
                    "tumor_type": "Not a Brain MRI",
                    "confidence": 0,
                    "filepath": filename
                })
                safe_delete(filepath)
                continue

            try:
                img_array = prepare_image(filepath)
                prediction = model.predict(img_array)
                predicted_class_idx = np.argmax(prediction, axis=1)[0]
                tumor_type = CLASS_LABELS[predicted_class_idx]
                confidence = round(float(np.max(prediction)) * 100, 2)

                results.append({
                    "filename": filename,
                    "tumor_type": tumor_type,
                    "confidence": confidence,
                    "filepath": filename
                })

            except Exception as e:
                print(f"[Prediction Error] {filename}: {e}")
                results.append({
                    "filename": filename,
                    "tumor_type": "Prediction Failed",
                    "confidence": 0,
                    "filepath": filename
                })

            finally:
                safe_delete(filepath)

    return jsonify({"results": results})

#save result api
@app.route("/api/save_result", methods=["POST"])
def save_result_api():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    tumor_type = data.get("tumor_type")
    confidence = data.get("confidence")
    filepath = data.get("filepath")
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_history (user_id, prediction, confidence, image_path)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, tumor_type, confidence, filepath)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Result saved successfully."})

#deleting an image from history
@app.route("/api/delete_history", methods=["POST"])
def delete_history_entry():
    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    image_path = data.get("image_path")
    user_id = session["user_id"]

    if not image_path:
        return jsonify({"message": "Image path required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_history WHERE user_id = %s AND image_path = %s",
        (user_id, image_path)
    )
    conn.commit()
    conn.close()

    # Optional: Delete actual file
    # try:
    #     os.remove(os.path.join("static", "uploads", image_path))
    # except FileNotFoundError:
    #     pass

    return jsonify({"message": f"{image_path} deleted successfully."})


import pandas as pd
from io import BytesIO
from flask import send_file, jsonify, session
from psycopg2.extras import RealDictCursor

@app.route("/api/export_results", methods=["GET"])
def export_results():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT prediction, confidence, datetime, image_path
        FROM user_history
        WHERE user_id = %s
        ORDER BY datetime DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"message": "No data found to export."})

    df = pd.DataFrame(rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Prediction_History')

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="prediction_history.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



# <------main------> #

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

    
