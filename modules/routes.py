from flask import render_template, jsonify, request, redirect, url_for, flash, session, send_file, abort
import joblib
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
from .chatbot import predict_disease, get_recommendations
from .database import get_faqs, get_emergency, check_user, add_user, get_user_by_id

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.graph_objs import Layout


def init_routes(app):

    # Kidney prediction model
    kidney_model = joblib.load(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\model\kidney_prediciton.pkl')

    # Diabetes prediction model
    diabetes_model = joblib.load(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\model\diabetes_prediciton.pkl')

    #liver model
    liver_model = joblib.load(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\model\liver_prediction.pkl')

    df_diabetes = pd.read_csv(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\Data_Charts\diabetes.csv')
    df_liver = pd.read_csv(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\Data_Charts\liver.csv')
    df_kidney = pd.read_csv(r'C:\Users\phewp\Desktop\New folder\MDS_6th_sem\backend\Data_Charts\kidney.csv')


    # Kidney model categorical mappings
    cat_mappings = {
        'red_blood_cells': {'normal': 1, 'abnormal': 0},
        'pus_cell': {'normal': 1, 'abnormal': 0},
        'pus_cell_clumps': {'present': 1, 'notpresent': 0},
        'bacteria': {'present': 1, 'notpresent': 0},
        'hypertension': {'yes': 1, 'no': 0},
        'diabetes_mellitus': {'yes': 1, 'no': 0},
        'coronary_artery_disease': {'yes': 1, 'no': 0},
        'appetite': {'good': 1, 'poor': 0},
        'peda_edema': {'yes': 1, 'no': 0},
        'aanemia': {'yes': 1, 'no': 0}
    }

    @app.route('/chatbot', methods=['POST'])
    def chatbot_reply():
        data = request.get_json()
        print("Received data:", data)

        user_input = data.get("message")
        if not user_input:
            return jsonify({"error": "No input provided."}), 400

        prediction, accuracy = predict_disease(user_input)
        reply = {
            "diagnosis": prediction,
            "confidence": f"{accuracy:.2f}",
            "recommendations": get_recommendations(prediction)
        }
        return jsonify(reply)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/faq')
    def faq():
        faqs = get_faqs()
        return render_template('faq.html', faqs=faqs)

    @app.route('/emergency')
    def emergency():
        emergency = get_emergency()
        return render_template("emergency.html", emergency=emergency)

    @app.route('/prediction')
    def prediction():
        return render_template("prediction.html")
    
    @app.route("/kidney_form")
    def kidney_form():
        return render_template("kidney_form.html")

    @app.route("/liver_form")
    def liver_form():
        return render_template("liver_form.html")

    @app.route("/diabetes_form")
    def diabetes_form():
        return render_template("diabetes_form.html")
    

    @app.route('/diabetes_predict', methods=['POST'])
    def diabetes_predict():
        try:
            form_data = request.form.to_dict()
            # Extract diabetes form
            features = [
                float(form_data.get('pregnancies', 0)),
                float(form_data.get('glucose', 0)),
                float(form_data.get('blood_pressure', 0)),
                float(form_data.get('skin_thickness', 0)),
                float(form_data.get('insulin', 0)),
                float(form_data.get('bmi', 0)),
                float(form_data.get('diabetes_pedigree_function', 0)),
                float(form_data.get('age', 0))
            ]
            
            #  prediction model 
            prediction = diabetes_model.predict([features])[0]
            probabilities = diabetes_model.predict_proba([features])[0]
            prob = probabilities[prediction]

            result = "Diabetes detected" if prediction == 1 else "No diabetes detected"
            confidence = f"{(prob * 100):.2f}%"

            user_id = session.get('user_id')
            if user_id:
                conn = sqlite3.connect('medical_db.db')
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO DiabetesRecord (user_id, pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                float(form_data.get('pregnancies', 0)),
                float(form_data.get('glucose', 0)),
                float(form_data.get('blood_pressure', 0)),
                float(form_data.get('skin_thickness', 0)),
                float(form_data.get('insulin', 0)),
                float(form_data.get('bmi', 0)),
                float(form_data.get('diabetes_pedigree_function', 0)),
                float(form_data.get('age', 0))
            ))
            conn.commit()
            diabetes_record_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO predictionreport (prediction_result, disease_type, patient_id, diabetes_record_id)
                VALUES (?, ?, ?, ?)
            ''', (
                result,
                'Diabetes',
                user_id,
                diabetes_record_id
            ))
            conn.commit()
            cursor.close()
            conn.close()


            return render_template('diabetes_result.html', result=result, confidence=confidence, form_data=form_data)
        except Exception as e:
            flash(f"Error in prediction: {str(e)}", 'danger')
            return redirect(url_for('diabetes_form'))

    # Login/Signup route
    @app.route('/login_register', methods=['GET', 'POST'])
    def login_register():
        if request.method == 'POST':
            if 'login' in request.form:
                email = request.form['email']
                password = request.form['password']
                user = check_user(email, password)

                if user:
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]
                    flash('Login successful!', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Invalid credentials', 'danger')

            elif 'signup' in request.form:
                name = request.form['name']
                email = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']
                contact = request.form['contact']
                gender = request.form['gender']
                if password != confirm_password:
                    flash("Passwords don't match", 'danger')
                else:
                    add_user(name, email, password, contact, gender)
                    flash('Account created successfully! Please login.', 'success')
                    return redirect(url_for('login_register'))
        return render_template('login_register.html')

    @app.route('/profile')
    def profile():
        if 'user_id' in session:
            user_id = session['user_id']
            user = get_user_by_id(session['user_id'])
            conn = sqlite3.connect('medical_db.db')
            cursor = conn.cursor()
            cursor.execute('''
            SELECT report_id, prediction_result, disease_type, patient_id
            FROM predictionreport
            WHERE patient_id = ?
        ''', (user_id,))
            reports = cursor.fetchall()
            cursor.close()
            conn.close()


            return render_template('profile.html', user=user, reports=reports)
        else:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login_register'))

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))


    @app.route('/liver_predict', methods=['POST'])
    def liver_predict():
        try:
            form_data = request.form.to_dict()

            print("Received form data:", form_data)

            features = []
            required_fields = [
                'age', 'gender', 'total_bilirubin', 'direct_bilirubin', 'alkaline_phosphatase', 
                'alamine_aminotransferase', 'aspartate_aminotransferase', 'total_proteins', 'albumin', 
                'albumin_and_globulin_ratio'
            ]

            for field in required_fields:
                value = form_data.get(field)
                if value:
                    try:
                        features.append(float(value))  
                    except ValueError:
                        raise ValueError(f"Invalid value for {field}: {value}")
                else:
                    raise ValueError(f"Missing value for {field}")

            print("Prepared features:", features)

            prediction = liver_model.predict([features])[0]
            probabilities = liver_model.predict_proba([features])[0]
            prob = probabilities[prediction]

            result = "Liver disease detected" if prediction == 1 else "No liver disease detected"
            confidence = f"{(prob * 100):.2f}%"
            user_id = session.get('user_id')

            if user_id:
                conn = sqlite3.connect('medical_db.db')
                cursor = conn.cursor()
                cursor.execute(''' 
                    INSERT INTO LiverRecord (user_id, age, gender, total_bilirubin, direct_bilirubin, 
                                             alkaline_phosphatase, alamine_aminotransferase, 
                                             aspartate_aminotransferase, total_proteins, albumin, 
                                             albumin_and_globulin_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                ''', (
                    user_id,
                    float(form_data.get('age', 0)),
                    float(form_data.get('gender', 0)),
                    float(form_data.get('total_bilirubin', 0)),
                    float(form_data.get('direct_bilirubin', 0)),
                    float(form_data.get('alkaline_phosphatase', 0)),
                    float(form_data.get('alamine_aminotransferase', 0)),
                    float(form_data.get('aspartate_aminotransferase', 0)),
                    float(form_data.get('total_proteins', 0)),
                    float(form_data.get('albumin', 0)),
                    float(form_data.get('albumin_and_globulin_ratio', 0))
                ))

                conn.commit()
                liver_record_id = cursor.lastrowid

                cursor.execute('''
                    INSERT INTO predictionreport (prediction_result, disease_type, patient_id, liver_record_id)
                    VALUES (?, ?, ?, ?)
                ''', (
                    result,
                    'Liver Disease',
                    user_id,
                    liver_record_id
                ))
                conn.commit()

                cursor.close()
                conn.close()

            return render_template('liver_result.html', result=result, confidence=confidence, form_data=form_data)

        except Exception as e:
            print(f"Error in liver_predict: {e}")
            flash(f"Error in prediction: {str(e)}", 'danger')

            return redirect(url_for('liver_form'))

# REPORT GENERATION

    @app.route('/download_report/<int:report_id>')
    def download_report(report_id):
        conn = sqlite3.connect('medical_db.db') 
        cursor = conn.cursor()

        cursor.execute('''
            SELECT pr.prediction_result, pr.disease_type, u.name, u.email, u.gender,
                   pr.kideny_record_id, pr.liver_record_id, pr.diabetes_record_id
            FROM predictionreport pr
            JOIN userbase u ON pr.patient_id = u.userid
            WHERE pr.report_id = ?
        ''', (report_id,))

        report = cursor.fetchone()
        if not report:
            abort(404, 'Report not found.')

        prediction_result, disease_type, name, email, gender, kidney_id, liver_id, diabetes_id = report

        # Setup PDF 
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 60

        # Add logo 
        try:
            logo_path = "C:/Users/Acer/Desktop/Coding/MDS_6th_sem/backend/static/images/diagn-sys-high-resolution-logo.png"
            p.drawImage(logo_path, 50, y - 50, width=100, height=100, preserveAspectRatio=True)
        except Exception as e:
            print(f"Logo error: {e}")

        y -= 80
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2, y, "Diagnosis Report")
        y -= 40

        def section_title(title):
            nonlocal y
            y -= 10
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, title)
            y -= 5
            p.setStrokeColor(colors.grey)
            p.line(50, y, width - 50, y)
            y -= 20

        def write_line(label, value):
            nonlocal y
            p.setFont("Helvetica", 11)
            p.drawString(60, y, f"{label}: {value}")
            y -= 16

        def add_record_section(title, data_dict):
            nonlocal y
            section_title(title)
            for key, value in data_dict.items():
                write_line(key, value)
                if y < 100:
                    p.showPage()
                    y = height - 50

        section_title("Patient Information")
        write_line("Name", name)
        write_line("Email", email)
        write_line("Gender", gender)
        section_title("Prediction Summary")
        write_line("Disease Type", disease_type)
        write_line("Prediction Result", prediction_result)

        # fetch disease data
        if kidney_id:
            cursor.execute('''
                SELECT age, blood_pressure, specific_gravity, albumin, sugar,
                       red_blood_cells, pus_cell, pus_cell_clumps, bacteria,
                       blood_glucose_random, blood_urea, serum_creatinine, sodium,
                       potassium, haemoglobin, packed_cell_volume, white_blood_cell_count,
                       red_blood_cell_count, hypertension, diabetes_mellitus,
                       coronary_artery_disease, appetite, peda_edema, anemia
                FROM KidneyRecord
                WHERE Kidney_Record_ID = ?
            ''', (kidney_id,))
            record = cursor.fetchone()
            if record:
                fields = [
                    "Age", "Blood Pressure", "Specific Gravity", "Albumin", "Sugar",
                    "Red Blood Cells", "Pus Cell", "Pus Cell Clumps", "Bacteria",
                    "Blood Glucose Random", "Blood Urea", "Serum Creatinine", "Sodium",
                    "Potassium", "Haemoglobin", "Packed Cell Volume", "WBC Count",
                    "RBC Count", "Hypertension", "Diabetes Mellitus", "CAD",
                    "Appetite", "Pedal Edema", "Anemia"
                ]
                data = dict(zip(fields, record))
                add_record_section("Kidney Disease Record", data)

        if liver_id:
            cursor.execute('''
                SELECT age, gender, total_bilirubin, direct_bilirubin,
                       alkaline_phosphatase, alamine_aminotransferase,
                       aspartate_aminotransferase, total_proteins, albumin,
                       albumin_and_globulin_ratio
                FROM LiverRecord
                WHERE Liver_Record_ID = ?
            ''', (liver_id,))
            record = cursor.fetchone()
            if record:
                fields = [
                    "Age", "Gender (0=Male, 1=Female)", "Total Bilirubin",
                    "Direct Bilirubin", "Alkaline Phosphatase",
                    "Alamine Aminotransferase", "Aspartate Aminotransferase",
                    "Total Proteins", "Albumin", "Albumin/Globulin Ratio"
                ]
                data = dict(zip(fields, record))
                add_record_section("Liver Disease Record", data)

        if diabetes_id:
            cursor.execute('''
                SELECT pregnancies, glucose, blood_pressure, skin_thickness,
                       insulin, bmi, diabetes_pedigree_function, age
                FROM DiabetesRecord
                WHERE Diabetes_Record_ID = ?
            ''', (diabetes_id,))
            record = cursor.fetchone()
            if record:
                fields = [
                    "Pregnancies", "Glucose", "Blood Pressure", "Skin Thickness",
                    "Insulin", "BMI", "Diabetes Pedigree Function", "Age"
                ]
                data = dict(zip(fields, record))
                add_record_section("Diabetes Record", data)
        

        p.setFont("Helvetica-Oblique", 9)
        p.setFillColor(colors.grey)
        p.drawString(50, 30, "Disclaimer: This report is generated using AI-based prediction models. It may not be 100% accurate.")
        p.drawString(50, 18, "Always consult a licensed medical professional for diagnosis and treatment.")
        p.setFillColor(colors.black)

        p.showPage()
        p.save()
        buffer.seek(0)
        conn.close()

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"report_{report_id}.pdf",
            mimetype='application/pdf'
        )


    @app.route('/kidney_predict', methods=['POST'])
    def kidney_predict():
        try:
            form_data = request.form.to_dict()

            def map_cat(field):
                val = form_data.get(field, '').strip().lower()
                return cat_mappings.get(field, {}).get(val, 0)

            features = [
                float(form_data.get('age', 0)),
                float(form_data.get('blood_pressure', 0)),
                float(form_data.get('specific_gravity', 0)),
                int(form_data.get('albumin', 0)),
                int(form_data.get('sugar', 0)),
                map_cat('red_blood_cells'),
                map_cat('pus_cell'),
                map_cat('pus_cell_clumps'),
                map_cat('bacteria'),
                float(form_data.get('blood_glucose_random', 0)),
                float(form_data.get('blood_urea', 0)),
                float(form_data.get('serum_creatinine', 0)),
                float(form_data.get('sodium', 0)),
                float(form_data.get('potassium', 0)),
                float(form_data.get('haemoglobin', 0)),
                float(form_data.get('packed_cell_volume', 0)),
                float(form_data.get('white_blood_cell_count', 0)),
                float(form_data.get('red_blood_cell_count', 0)),
                map_cat('hypertension'),
                map_cat('diabetes_mellitus'),
                map_cat('coronary_artery_disease'),
                map_cat('appetite'),
                map_cat('peda_edema'),
                map_cat('aanemia'),
            ]

            # Predict
            prediction = kidney_model.predict([features])[0]
            probabilities = kidney_model.predict_proba([features])[0]
            prob = probabilities[prediction]
            result = "Kidney disease detected" if prediction == 0 else "No kidney disease detected"
            confidence = f"{(prob * 100):.2f}"

            # Insert into DB if logged in
            user_id = session.get('user_id')
            if user_id:
                conn = sqlite3.connect('medical_db.db')
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO KidneyRecord (
                        user_id, age, blood_pressure, specific_gravity, albumin, sugar,
                        red_blood_cells, pus_cell, pus_cell_clumps, bacteria,
                        blood_glucose_random, blood_urea, serum_creatinine, sodium, potassium,
                        haemoglobin, packed_cell_volume, white_blood_cell_count, red_blood_cell_count,
                        hypertension, diabetes_mellitus, coronary_artery_disease, appetite, peda_edema, anemia
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    float(form_data.get('age', 0)),
                    float(form_data.get('blood_pressure', 0)),
                    float(form_data.get('specific_gravity', 0)),
                    int(form_data.get('albumin', 0)),
                    int(form_data.get('sugar', 0)),
                    map_cat('red_blood_cells'),
                    map_cat('pus_cell'),
                    map_cat('pus_cell_clumps'),
                    map_cat('bacteria'),
                    float(form_data.get('blood_glucose_random', 0)),
                    float(form_data.get('blood_urea', 0)),
                    float(form_data.get('serum_creatinine', 0)),
                    float(form_data.get('sodium', 0)),
                    float(form_data.get('potassium', 0)),
                    float(form_data.get('haemoglobin', 0)),
                    float(form_data.get('packed_cell_volume', 0)),
                    float(form_data.get('white_blood_cell_count', 0)),
                    float(form_data.get('red_blood_cell_count', 0)),
                    map_cat('hypertension'),
                    map_cat('diabetes_mellitus'),
                    map_cat('coronary_artery_disease'),
                    map_cat('appetite'),
                    map_cat('peda_edema'),
                    map_cat('aanemia')
                ))

                conn.commit()
                kidney_record_id = cursor.lastrowid

                cursor.execute('''
                    INSERT INTO predictionreport (prediction_result, disease_type, patient_id, kideny_record_id)
                    VALUES (?, ?, ?, ?)
                ''', (
                    result,
                    'Kidney',
                    user_id,
                    kidney_record_id
                ))
                conn.commit()
                cursor.close()
                conn.close()

            return render_template('kidney_result.html', result=result, confidence=confidence, form_data=form_data)

        except Exception as e:
            flash(f"Error in prediction: {str(e)}", 'danger')
            return redirect(url_for('kidney_form'))




#prepare data to make into graphs
    df_liver['Gender'] = df_liver['Gender'].map({'Female': 0, 'Male': 1})
    df_liver = df_liver.apply(pd.to_numeric, errors='coerce')
    df_kidney = df_kidney.apply(pd.to_numeric, errors='coerce')
    df_liver = df_liver.dropna()
    df_kidney = df_kidney.dropna()

    @app.route('/insights')
    def insights():
        # Diabetes Insights
        fig_age = px.histogram(df_diabetes, x='Age', title='Distribution of Age (Diabetes)', nbins=20)
        fig_age.update_layout(bargap=0.1)

        fig_bmi_glucose = px.scatter(df_diabetes, x='BMI', y='Glucose', color='Outcome', 
                                     title="BMI vs Glucose Levels (Diabetes Outcome)", 
                                     labels={'Outcome': 'Diabetes Outcome (0 = No, 1 = Yes)'})

        fig_bp_outcome = px.box(df_diabetes, x='Outcome', y='BloodPressure', title='Blood Pressure Distribution by Diabetes Outcome')

        corr_diabetes = df_diabetes.corr()
        fig_corr_diabetes = px.imshow(corr_diabetes, text_auto=True, title='Correlation Heatmap (Diabetes)')

        # Liver Insights
        fig_liver_age = px.histogram(df_liver, x='Age', title='Distribution of Age (Liver)', nbins=20)

        fig_bilirubin_alp = px.scatter(df_liver, x='Total_Bilirubin', y='Alkaline_Phosphotase', 
                                       title="Total Bilirubin vs ALP Levels (Liver)")

        fig_ag_ratio = px.box(df_liver, x='Albumin_and_Globulin_Ratio', title='A/G Ratio Distribution (Liver)')

        corr_liver = df_liver.corr()
        fig_corr_liver = px.imshow(corr_liver, text_auto=True, title='Correlation Heatmap (Liver)')

        graph_age = pio.to_html(fig_age, full_html=False)
        graph_bmi_glucose = pio.to_html(fig_bmi_glucose, full_html=False)
        graph_bp_outcome = pio.to_html(fig_bp_outcome, full_html=False)
        graph_corr_diabetes = pio.to_html(fig_corr_diabetes, full_html=False)

        graph_liver_age = pio.to_html(fig_liver_age, full_html=False)
        graph_bilirubin_alp = pio.to_html(fig_bilirubin_alp, full_html=False)
        graph_ag_ratio = pio.to_html(fig_ag_ratio, full_html=False)
        graph_corr_liver = pio.to_html(fig_corr_liver, full_html=False)

        return render_template("insights.html", 
                               graph_age=graph_age, graph_bmi_glucose=graph_bmi_glucose, 
                               graph_bp_outcome=graph_bp_outcome, graph_corr_diabetes=graph_corr_diabetes,
                               graph_liver_age=graph_liver_age, graph_bilirubin_alp=graph_bilirubin_alp,
                               graph_ag_ratio=graph_ag_ratio, graph_corr_liver=graph_corr_liver)
