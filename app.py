from flask import Flask, render_template, request, redirect, session, send_file
from fpdf import FPDF
from io import BytesIO
import os
import requests
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'quiz-secret'

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

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

def analyze_with_groq(question, selected):
    prompt = f"Question: {question}\nAnswer: {selected}\nGive a cybersecurity risk score from 1 to 5 with a short explanation. Start with score:"
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5
        }
        response = requests.post(GROQ_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        score = 1
        for word in content.split():
            if word.strip().isdigit():
                val = int(word)
                if 1 <= val <= 5:
                    score = val
                    break
        return score, content.strip()
    except Exception as e:
        return 1, f"Error analyzing response: {str(e)}"

def email_pdf(to_email, user_name, pdf_data):
    msg = EmailMessage()
    msg['Subject'] = 'Your Cybersecurity GRC Quiz Report'
    msg['From'] = "balajinagarajan6122003@gmail.com"
    msg['To'] = to_email
    msg.set_content(f"""Hi {user_name},

Thank you for completing the Cybersecurity GRC Quiz.
Please find your personalized GRC report attached as a PDF.

If you have questions or need help improving your organization's score,
feel free to contact Digitalxforce.

Regards,
Digitalxforce Team
🔗 https://digitalxforce.com
🔗 https://linkedin.com/company/digitalxforce
""")
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='GRC_Report.pdf')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("balajinagarajan6122003@gmail.com", "jghn jbqq voim hsue")
            smtp.send_message(msg)
    except Exception as e:
        print("❌ Email send error:", e)

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
    score_total = 0
    results = []

    for idx, q in enumerate(questions):
        selected = request.form.getlist(f"q{idx}")
        selected_text = ", ".join(selected)
        score, explanation = analyze_with_groq(q["q"], selected_text)
        score_total += score
        results.append({
            "question": q["q"],
            "selected": selected_text,
            "score": score,
            "explanation": explanation
        })

    session["results"] = results
    session["score"] = score_total
    return redirect("/report")

@app.route('/report')
def report():
    user = session.get("user", {})
    results = session.get("results", [])
    score = session.get("score", 0)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Cybersecurity GRC Quiz Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Name: {user.get('name')} | Position: {user.get('position')}", ln=True)
    pdf.cell(0, 10, f"Company: {user.get('company')} ({user.get('type')})", ln=True)
    pdf.cell(0, 10, f"GRC Score: {score}/15", ln=True)
    pdf.ln(5)

    for r in results:
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"Q: {r['question']}")
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Selected: {r['selected']}")
        pdf.multi_cell(0, 10, f"Score: {r['score']} / 5")
        pdf.multi_cell(0, 10, f"AI Analysis: {r['explanation']}")
        pdf.ln(2)

    pdf.set_font("Arial", "I", 10)
    pdf.ln(10)
    pdf.cell(0, 10, "For cybersecurity consultation, contact Digitalxforce", ln=True)
    pdf.cell(0, 10, "LinkedIn: https://linkedin.com/company/digitalxforce", ln=True)
    pdf.cell(0, 10, "Website: https://digitalxforce.com", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    email_pdf(user.get("email"), user.get("name"), pdf_bytes)

    return send_file(BytesIO(pdf_bytes), download_name="GRC_Report.pdf", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)