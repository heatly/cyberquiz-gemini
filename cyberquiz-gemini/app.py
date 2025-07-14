from flask import Flask, render_template, request, redirect, session, send_file
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fpdf import FPDF
from io import BytesIO

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = 'quiz-secret'

model = genai.GenerativeModel("gemini-pro")

questions = [
    "Describe your patch management process.",
    "How do you handle incident response?",
    "Explain your user access control strategy.",
    "What is your approach to data encryption?",
    "How do you manage third-party risk?"
]

@app.route('/')
def home():
    return render_template("index.html", questions=questions)

@app.route('/submit', methods=["POST"])
def submit():
    results = []
    total_score = 0

    for i, question in enumerate(questions, start=1):
        user_input = request.form[f"answer{i}"]
        prompt = f"""
        You are a cybersecurity auditor. Analyze the following response:
        "{user_input}"

        - Map it to a NIST CSF category
        - Score from 1 (low) to 5 (excellent)
        - Justify the score
        - Provide 2 recommendations for improvement

        Answer concisely.
        """
        response = model.generate_content(prompt)
        results.append(response.text)

        for line in response.text.splitlines():
            if "score" in line.lower():
                digits = [int(s) for s in line if s.isdigit()]
                if digits:
                    total_score += digits[0]
                    break

    session['results'] = results
    session['score'] = total_score
    return render_template("index.html", questions=questions, results=results)

@app.route('/report')
def report():
    results = session.get('results', [])
    score = session.get('score', 0)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Cybersecurity AI Quiz Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Total Score: {score}/{len(questions)*5}", ln=True, align='C')
    pdf.ln(10)

    for i, res in enumerate(results, start=1):
        pdf.multi_cell(0, 10, f"{i}. {questions[i-1]}\n{res}\n")

    pdf_out = BytesIO()
    pdf.output(pdf_out)
    pdf_out.seek(0)
    return send_file(pdf_out, download_name="CyberQuiz_Report.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)