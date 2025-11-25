import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from io import BytesIO
import pdfkit
import tempfile
import json

# Optional OpenAI usage
try:
    import openai
except Exception:
    openai = None

# Config
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-this")

from markupsafe import Markup
@app.template_filter('nl2br')
def nl2br(value):
    return Markup('<br>'.join(Markup.escape(value).splitlines()))


# OpenAI config (optional)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", None)
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # optional; change if needed
if openai and OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# pdfkit/wkhtmltopdf config:
# If wkhtmltopdf is not in PATH, set path here or set wkhtmltopdf in system PATH
WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", None)
if WKHTMLTOPDF_PATH:
    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
else:
    # lets pdfkit try to find wkhtmltopdf in PATH
    config = None

def ai_enhance_text(prompt_text: str, role_hint="You are an expert resume writer.") -> str:
    """
    Enhance text using OpenAI if available. If OpenAI not configured, do a small local fallback.
    """
    if openai and OPENAI_KEY:
        try:
            # Using ChatCompletion-like interface -- adapt if your openai package differs
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": role_hint},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=400,
                temperature=0.2,
            )
            # adapt parsing based on response structure
            content = response["choices"][0]["message"]["content"].strip()
            return content
        except Exception as e:
            # don't fail the whole request; fallback to simple cleaning
            print("OpenAI call failed:", e)
            pass

    # Local fallback: basic cleanup + sentence improvements (simple heuristics)
    s = " ".join(prompt_text.split())  # collapse whitespace
    # Ensure sentences end with periods
    if not s.endswith((".", "?", "!")):
        s += "."
    # Capitalize first letter
    s = s[0].upper() + s[1:]
    return s

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Collect form data
        data = {
            "full_name": request.form.get("full_name", "").strip(),
            "title": request.form.get("title", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "summary": request.form.get("summary", "").strip(),
            "experience": request.form.get("experience", "").strip(),
            "education": request.form.get("education", "").strip(),
            "skills": request.form.get("skills", "").strip()
        }

        # If user asked for AI enhancement checkbox is on
        enhance = request.form.get("enhance_ai", "off") == "on"

        # Enhance summary and experience if requested
        if enhance:
            # Enhance professional summary
            if data["summary"]:
                prompt = f"Rewrite the following professional summary to be clearer, concise, and resume-ready:\n\n{data['summary']}"
                data["summary_enhanced"] = ai_enhance_text(prompt, role_hint="You are a helpful professional resume writer. Give a polished single-paragraph summary.")
            else:
                data["summary_enhanced"] = ""

            # Enhance experience -> convert lines into strong bullet points
            if data["experience"]:
                # Ask AI to convert the experience block (user can paste multiple jobs) into bullet points
                prompt = (
                    "Convert the following experience entries into 4-6 concise resume bullet points per job. "
                    "Keep numbers where possible and use action verbs. Input:\n\n" + data["experience"]
                )
                data["experience_enhanced"] = ai_enhance_text(prompt, role_hint="You are an expert resume bullet point writer.")
            else:
                data["experience_enhanced"] = ""
        else:
            # No AI: keep original text; also create simple bullets from experience by splitting lines
            data["summary_enhanced"] = data["summary"]
            if data["experience"]:
                bullets = []
                for line in data["experience"].splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if not line.endswith("."):
                        line = line + "."
                    bullets.append(line)
                data["experience_enhanced"] = "\n".join(bullets)
            else:
                data["experience_enhanced"] = ""

        # Save data temporarily in session-like way by encoding in JSON and passing through query or hidden form
        # Here we'll render preview and offer download
        return render_template("resume.html", data=data)

    return render_template("form.html")

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    """
    Expect a POST with hidden fields containing the resume JSON string or form fields.
    We'll render the resume HTML and convert to PDF using pdfkit.
    """
    # Get posted fields (we recommend sending the same fields as used in preview)
    data = {
        "full_name": request.form.get("full_name", "").strip(),
        "title": request.form.get("title", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "summary_enhanced": request.form.get("summary_enhanced", "").strip(),
        "experience_enhanced": request.form.get("experience_enhanced", "").strip(),
        "education": request.form.get("education", "").strip(),
        "skills": request.form.get("skills", "").strip()
    }

    # Render the resume HTML
    rendered = render_template("resume.html", data=data, for_pdf=True)

    # Try pdfkit conversion
    try:
        # You can tune pdf options here
        options = {
            "page-size": "A4",
            "encoding": "UTF-8",
            "margin-top": "12mm",
            "margin-bottom": "12mm",
            "margin-left": "12mm",
            "margin-right": "12mm",
        }
        pdf_bytes = pdfkit.from_string(rendered, False, options=options, configuration=config)
        return send_file(BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=f"{data.get('full_name','resume')}.pdf")
    except Exception as e:
        print("PDF generation failed:", e)
        # Fallback: return HTML so user can use browser Print->Save as PDF
        flash("Server couldn't generate PDF automatically. Use browser Print -> Save as PDF (or install wkhtmltopdf).")
        return rendered

if __name__ == "__main__":
    # debug=True for development only
    app.run(host="0.0.0.0", port=5000, debug=True)
