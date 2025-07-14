from flask import Flask, render_template, request, redirect, session, send_file
import google.generativeai as genai
from fpdf import FPDF
from io import BytesIO
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'quiz-secret'

# 🔐 Hardcoded Gemini API key (safe only in private/development)
genai.configure(api_key="AIzaSyAK4b3JlZQNZOOdR6jpJiyFakan5YUNcBY")
model = genai.GenerativeModel("gemini-1.5-flash-latest")

questions = [
    {
        "q": "How do you manage patching of critical systems?",
        "options": [
            "Automated within 24 hours",
            "Manual, within a week",
            "Only for major issues",
            "Not sure / No process"
        ]
    },
    {
        "q": "What is your incident response strategy?",
        "options": [
            "Documented & tested regularly",
            "Documented but untested",
            "Only handled ad hoc",
            "No process exists"
        ]
    },
    {
        "q": "What kind of access control do you use?",
        "options": [
            "RBAC with MFA for all users",
            "MFA only for admins",
            "Basic username/password",
            "No formal control"
        ]
    }
]

@app.route('/')
def home():
    return render_template("info.html")

@app.route('/start', methods=["POST"])
def start_quiz():
    session['user'] = {
        "name": request.form["name"],
        "position": request.form["position"],
        "company": request.form["company"],
        "type": request.form["type"],
        "email": request.form["email"]
    }
    return render_template("quiz.html", questions=questions)

@app.route('/submit', methods=["POST"])
def submit():
    results = []
    score_total = 0
    score_details = []

    for idx, q in enumerate(questions):
        selected = request.form.get(f"q{idx}")
        prompt = f"""
        You are a cybersecurity auditor. Analyze this answer:
        Question: {q["q"]}
        Selected: {selected}

        Give a GRC score from 1 (bad) to 5 (excellent), justify the score, map to NIST CSF category, and give 2 improvement suggestions.
        """
        try:
            response = model.generate_content(prompt).text
        except Exception as e:
            print("❌ Gemini API Error:", str(e))
            response = "Error analyzing response. Please check API key or input."

        results.append(response)

        score = 0
        for line in response.splitlines():
            if "score" in line.lower():
                digits = [int(s) for s in line if s.isdigit()]
                if digits:
                    score = digits[0]
                    break
        score_total += score
        score_details.append((q["q"], selected, response))

    session['results'] = results
    session['score'] = score_total
    session['score_details'] = score_details
    return redirect("/report")

@app.route('/report')
def report():
    user = session.get("user", {})
    score = session.get("score", 0)
    score_details = session.get("score_details", [])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Cybersecurity GRC Quiz Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Name: {user.get('name')} | Position: {user.get('position')}", ln=True)
    pdf.cell(0, 10, f"Company: {user.get('company')} ({user.get('type')})", ln=True)
    pdf.cell(0, 10, f"GRC Score: {score}/{len(questions)*5}", ln=True)
    pdf.ln(5)

    for q_text, selected, analysis in score_details:
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"Q: {q_text}")
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Selected: {selected}")
        pdf.multi_cell(0, 10, f"AI Analysis:\n{analysis}\n")
        pdf.ln(2)

    pdf.set_font("Arial", "I", 10)
    pdf.ln(10)
    pdf.cell(0, 10, "For cybersecurity consultation, contact Digitalxforce", ln=True)
    pdf.cell(0, 10, "LinkedIn: https://linkedin.com/company/digitalxforce", ln=True)
    pdf.cell(0, 10, "Website: https://digitalxforce.com", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')

    try:
        email_pdf(user.get('email'), pdf_bytes)
    except Exception as e:
        print("❌ Email failed:", str(e))

    return send_file(BytesIO(pdf_bytes), download_name="GRC_Report.pdf", as_attachment=True)

def email_pdf(to_email, pdf_data):
    msg = EmailMessage()
    msg['Subject'] = 'Your Cybersecurity GRC Quiz Report'
    msg['From'] = "balajinagarajan6122003@gmail.com"
    msg['To'] = to_email
    msg.set_content("Hello,\n\nAttached is your cybersecurity GRC score report.\n\nRegards,\nDigitalxforce")

    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='GRC_Report.pdf')

    # Replace with real credentials and SMTP server
    with smtplib.SMTP_SSL('smtp.example.com', 465) as smtp:
        smtp.login("balajinagarajan6122003@gmail.com", "jghn jbqq voim hsue")
        smtp.send_message(msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
