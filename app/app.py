from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session,
    redirect
)

import pandas as pd
import numpy as np
import joblib
import pickle
import json
import os

import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas

# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = "apache_secret_key"

# ==========================================
# LOAD MODELS
# ==========================================

los_model = joblib.load(
    "../models/los_classifier.pkl"
)

mortality_model = joblib.load(
    "../models/mortality_classifier.pkl"
)

# ==========================================
# LOAD FEATURES
# ==========================================

with open("../models/features.pkl", "rb") as f:

    features = pickle.load(f)

# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("login.html")

# ==========================================
# REGISTER PAGE
# ==========================================

@app.route("/register-page")
def register_page():

    return render_template("register.html")

# ==========================================
# REGISTER USER
# ==========================================

@app.route("/register", methods=["POST"])
def register():

    email = request.form["email"]

    password = request.form["password"]

    users = []

    if os.path.exists("users.json"):

        with open("users.json", "r") as f:

            users = json.load(f)

    # CHECK EXISTING USER

    for user in users:

        if user["email"] == email:

            return render_template(

                "login.html",

                error="User Already Exists"

            )

    # ADD USER

    users.append({

        "email": email,

        "password": password

    })

    with open("users.json", "w") as f:

        json.dump(users, f)

    return render_template(

        "login.html",

        error="Registration Successful"

    )

# ==========================================
# LOGIN VALIDATION
# ==========================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]

    password = request.form["password"]

    if not os.path.exists("users.json"):

        return render_template(

            "login.html",

            error="No Registered Users"

        )

    with open("users.json", "r") as f:

        users = json.load(f)

    for user in users:

        if (
            user["email"] == email
            and
            user["password"] == password
        ):

            session["user"] = email

            return render_template(

                "dashboard.html"

            )

    return render_template(

        "login.html",

        error="Invalid Email or Password"

    )

# ==========================================
# FORGOT PASSWORD
# ==========================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = ""

    if request.method == "POST":

        email = request.form["email"]

        old_password = request.form["old_password"]

        new_password = request.form["new_password"]

        if not os.path.exists("users.json"):

            message = "No Users Found"

            return render_template(
                "forgot.html",
                message=message
            )

        with open("users.json", "r") as f:

            users = json.load(f)

        user_found = False

        for user in users:

            if (
                user["email"] == email
                and
                user["password"] == old_password
            ):

                user["password"] = new_password

                user_found = True

                break

        if user_found:

            with open("users.json", "w") as f:

                json.dump(users, f, indent=4)

            message = "Password Updated Successfully"

        else:

            message = "Invalid Email Or Previous Password"

    return render_template(
        "forgot.html",
        message=message
    )
# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")

# ==========================================
# PREDICTION ROUTE
# ==========================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        if "user" not in session:

            return redirect("/")

        input_data = {}

        # ======================================
        # PATIENT DETAILS
        # ======================================

        patient_name = request.form.get(

            "patient_name"

        )

        patient_age = request.form.get(

            "Age"

        )

        # ======================================
        # FEATURES
        # ======================================

        for feature in features:

            value = request.form.get(feature)

            if value is None or value == "":

                value = 0

            input_data[feature] = float(value)

        df = pd.DataFrame([input_data])

        # ======================================
        # LOS
        # ======================================

        los_pred = los_model.predict(df)[0]

        los_prob = float(

            np.max(
                los_model.predict_proba(df)
            ) * 100

        )

        if los_pred == 0:

            los_result = "Low ICU Stay"

        elif los_pred == 1:

            los_result = "Moderate ICU Stay"

        else:

            los_result = "High ICU Stay"

        # ======================================
        # MORTALITY
        # ======================================

        mortality_pred = mortality_model.predict(df)[0]

        mortality_prob = float(

            np.max(
                mortality_model.predict_proba(df)
            ) * 100

        )

        if mortality_pred == 0:

            mortality_result = "Low Risk"

        elif mortality_pred == 1:

            mortality_result = "Moderate Risk"

        else:

            mortality_result = "High Risk"

        # ======================================
        # SAVE SESSION
        # ======================================

        session["patient_name"] = patient_name

        session["patient_age"] = patient_age

        session["patient_values"] = input_data

        session["los_result"] = los_result

        session["mortality_result"] = mortality_result

        session["los_prob"] = round(

            los_prob,

            2

        )

        session["mortality_prob"] = round(

            mortality_prob,

            2

        )

        return render_template(

            "results.html",

            patient_name=patient_name,

            patient_age=patient_age,

            patient_values=input_data,

            los_result=los_result,

            mortality_result=mortality_result,

            los_prob=round(los_prob, 2),

            mortality_prob=round(mortality_prob, 2)

        )


    except Exception as e:

        return str(e)

# ==========================================
# PDF REPORT DOWNLOAD
# ==========================================

@app.route("/download-report")
def download_report():

    if "user" not in session:

        return redirect("/")

    patient_name = session.get(

        "patient_name",

        "Unknown"

    )

    patient_age = session.get(

        "patient_age",

        "0"

    )

    patient_values = session.get(

        "patient_values",

        {}

    )

    los_result = session.get(

        "los_result",

        "Not Available"

    )

    mortality_result = session.get(

        "mortality_result",

        "Not Available"

    )

    los_prob = session.get(

        "los_prob",

        0

    )

    mortality_prob = session.get(

        "mortality_prob",

        0

    )

    # ======================================
    # GRAPH
    # ======================================

    categories = [

        "LOS",

        "Mortality"

    ]

    values = [

        los_prob,

        mortality_prob

    ]

    plt.figure(figsize=(6, 4))

    plt.bar(

        categories,

        values

    )

    plt.ylabel("Confidence %")

    plt.title("Prediction Analysis")

    chart_path = "chart.png"

    plt.savefig(chart_path)

    plt.close()

    # ======================================
    # PDF
    # ======================================

    pdf_path = "patient_report.pdf"

    c = canvas.Canvas(pdf_path)

    # TITLE

    c.setFont(

        "Helvetica-Bold",

        24

    )

    c.drawString(

        150,

        800,

        "ICU Patient Report"

    )

    # ADMIN

    c.setFont(

        "Helvetica",

        12

    )

    c.drawString(

        50,

        770,

        f"Generated By: {session['user']}"

    )

    # PATIENT DETAILS

    c.setFont(

        "Helvetica-Bold",

        16

    )

    c.drawString(

        50,

        730,

        "Patient Details"

    )

    c.setFont(

        "Helvetica",

        13

    )

    c.drawString(

        70,

        700,

        f"Patient Name: {patient_name}"

    )

    c.drawString(

        70,

        675,

        f"Age: {patient_age}"

    )

    # PREDICTIONS

    c.setFont(

        "Helvetica-Bold",

        16

    )

    c.drawString(

        50,

        630,

        "Prediction Summary"

    )

    c.setFont(

        "Helvetica",

        13

    )

    c.drawString(

        70,

        600,

        f"LOS Result: {los_result}"

    )

    c.drawString(

        70,

        575,

        f"LOS Confidence: {los_prob}%"

    )

    c.drawString(

        70,

        545,

        f"Mortality Result: {mortality_result}"

    )

    c.drawString(

        70,

        520,

        f"Mortality Confidence: {mortality_prob}%"

    )

    # GRAPH

    c.drawImage(

        chart_path,

        120,

        280,

        width=350,

        height=200

    )

    # FEATURES

    c.setFont(

        "Helvetica-Bold",

        14

    )

    c.drawString(

        50,

        250,

        "Patient Parameters"
    )

    y = 225

    c.setFont(

        "Helvetica",

        10

    )

    for key, value in patient_values.items():

        c.drawString(

            60,

            y,

            f"{key} : {value}"

        )

        y -= 15

        if y < 40:

            c.showPage()

            y = 800

    # FOOTER

    c.setFont(

        "Helvetica-Oblique",

        11

    )

    c.drawString(

        50,

        20,

        "Generated By Apache ICU Admin Dashboard"

    )

    c.save()

    return send_file(

        pdf_path,

        as_attachment=True

    )

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)