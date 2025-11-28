import os
import re
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from io import BytesIO

# imports extra
try:
    import pdfkit
except Exception:
    pdfkit = None

try:
    from llama_index.llms.gemini import Gemini
except Exception:
    Gemini = None

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CSS_FILE = os.path.join(STATIC_DIR, "style.css")
DB_FILE = os.path.join(BASE_DIR, "resumes.db")

WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", None)
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize Gemini LLM
llm = None
if GEMINI_API_KEY and Gemini:
    try:
        llm = Gemini(api_key=GEMINI_API_KEY, model="gemini-flash-latest")
        print("✓ Gemini LLM initialized successfully")
    except Exception as e:
        print("Failed to init Gemini LLM:", e)
        llm = None

# CSS 
CSS_CONTENT = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');
*{
    font-family: "Outfit", sans-serif;
}
body { font-family: Arial, Helvetica, sans-serif; background:#f6f7fb; color:#111; margin:0; padding:0; }
.container { max-width:960px; margin:30px auto; padding:18px; }
.app{display:flex;justify-content: center; align-items:center; }
.header{ padding: 10px; border-radius: 10px; margin-bottom: -10px;}
.a{display: flex;justify-content: end; margin-bottom: 10px;}
.head{display:flex; flex-direction:column; justify-content: center; align-items:center;}
.app { margin:10px; font-size:35px; color:#100303; }
.headm{
  display: flex; justify-content:center; align-items: center;
}
.headb p {font-weight: 500; }
.headb{margin-top: 25px;
  display: flex; justify-content: space-between;
}
.form-card, .preview-card { background:white; border-radius:8px; padding:18px; box-shadow:0 4px 12px rgba(15,23,42,0.06); }
label { display:block; margin-top:10px; font-weight:600; }
input[type="text"], input[type="email"], textarea, select {
  width:100%; padding:10px; margin-top:6px; border:1px solid #e6e9ef; border-radius:6px; box-sizing:border-box;
}
textarea { min-height:100px; resize:vertical; }
.row { display:flex; gap:12px; }
.col { flex:1; }
.button { background:#2563eb; color:#fff; padding:10px 14px; border-radius:6px; border:none; cursor:pointer; font-weight:600; }
.small { color:#6b7280; font-size:13px; margin-top:10px; }
.template-pills { display:flex; gap:8px; margin-top:8px; }
.pill { padding:8px 10px; border:1px solid #e6e9ef; border-radius:999px; cursor:pointer; }
.pill:hover{background:#2563eb; color: #fff;}
.pill{text-decoration: none;}
.download-btn { display:inline-block; margin-top:12px; background:#059669; padding:8px 12px; color:#fff; border-radius:6px; text-decoration:none; }
.error { color: #dc2626; background: #fee2e2; padding: 10px; border-radius: 6px; margin-bottom: 10px; }
.info { color: #059669; background: #d1fae5; padding: 8px; border-radius: 6px; margin-top: 6px; font-size: 13px; }
@media (max-width:800px){ .row { flex-direction:column; } .container { padding:12px; } }
"""

# Write CSS file if missing / different
write_css = True
if os.path.exists(CSS_FILE):
    try:
        with open(CSS_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing.strip() == CSS_CONTENT.strip():
            write_css = False
    except Exception:
        write_css = True

if write_css:
    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(CSS_CONTENT)

# base.html
BASE_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{{ title or 'Resume Builder' }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="headm">
        <img src="{{ url_for('static', filename='p.png') }}"alt="Resume" width="100" height="auto">
        <div class="head">
        <h1 class="app">Resume Builder </h1>
      </div>
    </div>
    <div class="headb">
      <p> Enter the details to generate a Resume </p>
      <span class="a">
        <a href="{{ url_for('index') }}" class="pill">Create new</a>
      </span>
    </div>
    </div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="error">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
</body>
</html>
"""

# form.html
FORM_HTML = """{% extends "base.html" %}
{% block content %}
<div class="form-card">
  <form method="post" action="{{ url_for('submit_form') }}">
    <div class="row">
      <div class="col">
        <label>Full Name</label>
        <input required name="full_name" type="text" placeholder="Name" value="{{ form_data.full_name or '' }}">
      </div>
      <div class="col">
        <label>Job Title</label>
        <input name="title" type="text" placeholder="Software Engineer" value="{{ form_data.title or '' }}">
      </div>
    </div>
    <div class="row">
      <div class="col">
        <label>Email</label>
        <input name="email" type="email" placeholder="you@example.com" value="{{ form_data.email or '' }}">
      </div>
      <div class="col">
        <label>Phone (at least 10 digits)</label>
        <input name="phone" type="text" placeholder="+91-6006868686" value="{{ form_data.phone or '' }}">
      </div>
    </div>
    <label>LinkedIn / Portfolio URL</label>
    <input name="profile_link" type="text" placeholder="https://www.linkedin.com" value="{{ form_data.profile_link or '' }}">
    <label>Professional Summary (minimum 30 words)</label>
    <textarea name="summary" placeholder="Short paragraph about yourself">{{ form_data.summary or '' }}</textarea>
    <label>Experience (paste each job, or bullets)</label>
    <textarea name="experience" placeholder="Company — Role — Achievements">{{ form_data.experience or '' }}</textarea>
    <label>Education</label>
    <textarea name="education">{{ form_data.education or '' }}</textarea>
    <label>Projects (optional)</label>
    <textarea name="projects">{{ form_data.projects or '' }}</textarea>
    <label>Skills (comma separated)</label>
    <input name="skills" type="text" placeholder="Python, Flask, SQL, ..." value="{{ form_data.skills or '' }}">
    <label>Select Template</label>
    <select name="template">
      <option value="template1" {% if form_data.template == 'template1' %}selected{% endif %}>Professional Modern</option>
      <option value="template2" {% if form_data.template == 'template2' %}selected{% endif %}>Two-Column Elegant</option>
      <option value="template3" {% if form_data.template == 'template3' %}selected{% endif %}>Tech Developer</option>
    </select>
    
    {% if ai_available %}
    <label style="margin-top:12px;">
      <input type="checkbox" name="enhance_ai" {% if form_data.enhance_ai %}checked{% endif %}>
      Enhance summary with AI (Gemini)
    </label>
    <p class="info">✨ AI will rewrite your summary to be more professional and ATS-friendly</p>
    {% endif %}
    
    <div style="margin-top:14px;">
      <button class="button" type="submit">Preview Resume</button>
    </div>
  </form>
  <p class="small">After preview you can download PDF.</p>
</div>
{% endblock %}
"""

# Preview 
PREVIEW_HTML = """{% extends "base.html" %}
{% block content %}
<div class="preview-card">
  <h2>Preview — {{ data.full_name }}</h2>
  <div>
    <!-- include the selected template body -->
    {% include template_file %}
  </div>
  <form method="post" action="{{ url_for('download_pdf', resume_id=data.id) }}">
    <!-- include hidden fields so download uses same data -->
    <input type="hidden" name="resume_id" value="{{ data.id }}">
    <button class="button" type="submit">Download as PDF</button>
  </form>
  <p class="small">You can come back to this page to re-download the resume.</p>
</div>
{% endblock %}
"""

# Templates
TEMPLATE_1 = """<div class="resume">
  <h1 style="margin:0; font-size:26px;">{{ data.full_name }}</h1>
  <div style="color:#374151; margin-top:6px;">{{ data.title }} {% if data.profile_link %} • <a href="{{ data.profile_link }}">{{ data.profile_link }}</a>{% endif %}</div>
  {% if data.summary %}
    <h2 style="margin-top:14px;">Summary</h2>
    <p>{{ data.summary | nl2br }}</p>
  {% endif %}
  {% if data.experience %}
    <h2>Experience</h2>
    {% for line in data.experience.splitlines() %}
      <p>&#9679; {{ line }}</p>
    {% endfor %}
  {% endif %}
  {% if data.education %}
    <h2>Education</h2>
    <p>{{ data.education | nl2br }}</p>
  {% endif %}
  {% if data.projects %}
    <h2>Projects</h2>
    <p>{{ data.projects | nl2br }}</p>
  {% endif %}
  {% if data.skills %}
    <h2>Skills</h2>
    <p>{{ data.skills }}</p>
  {% endif %}
</div>
"""

TEMPLATE_2 = """<div style="display:flex; gap:20px;">
  <div style="flex:2;">
    <h1 style="margin:0;">{{ data.full_name }}</h1>
    <div style="color:#374151;">{{ data.title }}</div>
    {% if data.summary %}
      <h2 style="margin-top:12px;">Summary</h2>
      <p>{{ data.summary | nl2br }}</p>
    {% endif %}
    {% if data.experience %}
      <h2>Experience</h2>
      {% for line in data.experience.splitlines() %}
        <p>&#9679; {{ line }}</p>
      {% endfor %}
    {% endif %}
    {% if data.projects %}
      <h2>Projects</h2>
      <p>{{ data.projects | nl2br }}</p>
    {% endif %}
  </div>
  <div style="flex:1; background:#f8fafc; padding:12px; border-radius:8px;">
    {% if data.profile_link %}
      <h3>Profile</h3>
      <p><a href="{{ data.profile_link }}">{{ data.profile_link }}</a></p>
    {% endif %}
    {% if data.education %}
      <h3>Education</h3>
      <p>{{ data.education | nl2br }}</p>
    {% endif %}
    {% if data.skills %}
      <h3>Skills</h3>
      <p>{{ data.skills }}</p>
    {% endif %}
  </div>
</div>
"""

TEMPLATE_3 = """<div class="resume" style="font-family:Segoe UI, Roboto, Arial;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <h1 style="margin:0;">{{ data.full_name }}</h1>
      <div style="color:#374151;">{{ data.title }}</div>
    </div>
    <div style="text-align:right; color:#6b7280;">
      {% if data.email %}{{ data.email }}<br>{% endif %}
      {% if data.phone %}{{ data.phone }}<br>{% endif %}
      {% if data.profile_link %}<a href="{{ data.profile_link }}">{{ data.profile_link }}</a>{% endif %}
    </div>
  </div>
  {% if data.summary %}
    <h2 style="margin-top:12px;">Summary</h2>
    <p>{{ data.summary | nl2br }}</p>
  {% endif %}
  <h2>Experience</h2>
  {% for line in data.experience.splitlines() %}
    <p>&#9679; {{ line }}</p>
  {% endfor %}
  <div style="margin-top:10px;">
    <strong>Skills:</strong> {{ data.skills }}
  </div>
</div>
"""

# map the files
WRITE_FILES = {
    os.path.join(TEMPLATES_DIR, "base.html"): BASE_HTML,
    os.path.join(TEMPLATES_DIR, "form.html"): FORM_HTML,
    os.path.join(TEMPLATES_DIR, "preview.html"): PREVIEW_HTML,
    os.path.join(TEMPLATES_DIR, "resume_template1.html"): TEMPLATE_1,
    os.path.join(TEMPLATES_DIR, "resume_template2.html"): TEMPLATE_2,
    os.path.join(TEMPLATES_DIR, "resume_template3.html"): TEMPLATE_3,
}

for path, contents in WRITE_FILES.items():
    write = True
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                if f.read().strip() == contents.strip():
                    write = False
        except Exception:
            write = True
    if write:
        with open(path, "w", encoding="utf-8") as f:
            f.write(contents)

# Flask app
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-this")

db = SQLAlchemy(app)

# ---------- Validation Functions ----------
def validate_phone(phone):
    """Check if phone has at least 10 digits"""
    if not phone:
        return True  # Optional field
    digits = re.sub(r'\D', '', phone)  # Remove non-digit characters
    return len(digits) >= 10

def validate_url(url):
    """Check if URL is valid"""
    if not url:
        return True  # Optional field
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([a-zA-Z0-9-]+\.)*'  # subdomain
        r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'  # domain
        r'(/.*)?$'  # path
    )
    return bool(url_pattern.match(url))

def count_words(text):
    """Count words in text"""
    if not text:
        return 0
    return len(text.split())

def enhance_summary_with_ai(raw_summary: str) -> str:
    if not raw_summary or not llm:
        return raw_summary

    prompt = (
        "Rewrite the following professional summary to be concise, clear, "
        "impactful, and ATS-friendly. Keep it between 40-80 words, remove first person pronouns, "
        "and focus on achievements and skills. Make it suitable for a resume:\n\n"
        f"{raw_summary}"
    )
    try:
        resp = llm.complete(prompt)
        text = resp.text.strip()
        return text or raw_summary
    except Exception as e:
        print("Gemini enhancement failed:", e)
        return raw_summary


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250))
    email = db.Column(db.String(250))
    phone = db.Column(db.String(100))
    profile_link = db.Column(db.String(500))
    summary = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    projects = db.Column(db.Text)
    skills = db.Column(db.Text)
    template = db.Column(db.String(80), default="template1")

    def to_dictionary(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "profile_link": self.profile_link,
            "summary": self.summary or "",
            "experience": self.experience or "",
            "education": self.education or "",
            "projects": self.projects or "",
            "skills": self.skills or "",
            "template": self.template or "template1",
        }

with app.app_context():
    db.create_all()

@app.template_filter("nl2br")
def nl2br(value):
    if not value:
        return ""
    return Markup("<br>".join(Markup.escape(str(value)).splitlines()))

pdf_config = None
if pdfkit and WKHTMLTOPDF_PATH:
    try:
        pdf_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    except Exception as e:
        print("pdfkit configuration error:", e)
        pdf_config = None


@app.route("/", methods=["GET"])
def index():
    return render_template("form.html", title="Create Resume", form_data={}, ai_available=bool(llm))

@app.route("/submit", methods=["POST"])
def submit_form():
    # Collect data
    data = {k: request.form.get(k, "").strip() for k in ("full_name","title","email","phone","profile_link","summary","experience","education","projects","skills")}
    chosen_template = request.form.get("template", "template1")
    use_ai = request.form.get("enhance_ai", "") == "on"
    data["template"] = chosen_template
    data["enhance_ai"] = use_ai
    

    errors = []
    

    if data["phone"] and not validate_phone(data["phone"]):
        errors.append("Phone number must contain at least 10 digits.")
    
  
    if data["profile_link"] and not validate_url(data["profile_link"]):
        errors.append("Please enter a valid LinkedIn/Portfolio URL (e.g., https://linkedin.com/in/yourname).")
    
  
    if data["summary"]:
        word_count = count_words(data["summary"])
        if word_count < 30:
            errors.append(f"Professional summary must be at least 30 words long. Current count: {word_count} words.")
    

    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template("form.html", title="Create Resume", form_data=data, ai_available=bool(llm))
    

    if use_ai and llm and data["summary"]:
        print("Enhancing summary with Gemini...")
        data["summary"] = enhance_summary_with_ai(data["summary"])
    
    resume = Resume(
        full_name=data["full_name"] or "Unnamed",
        title=data["title"],
        email=data["email"],
        phone=data["phone"],
        profile_link=data["profile_link"],
        summary=data["summary"],
        experience=data["experience"],
        education=data["education"],
        projects=data["projects"],
        skills=data["skills"],
        template=chosen_template
    )
    db.session.add(resume)
    db.session.commit()
    return redirect(url_for("preview_resume", resume_id=resume.id))

@app.route("/resume/<int:resume_id>", methods=["GET"])
def preview_resume(resume_id):
    r = Resume.query.get_or_404(resume_id)
    data = r.to_dictionary()
    template_file = f"resume_{r.template}.html"
    return render_template("preview.html", data=data, template_file=template_file, title="Preview")

@app.route("/download/<int:resume_id>", methods=["POST"])
def download_pdf(resume_id):
    r = Resume.query.get_or_404(resume_id)
    data = r.to_dictionary()
    template_name = f"resume_{r.template}.html"
    html = render_template(template_name, data=data, for_pdf=True)
    full_html = (
        "<html><head><meta charset='utf-8'><style>"
        + CSS_CONTENT
        + "</style></head><body>"
        + html
        + "</body></html>"
    ).encode("utf-8")

    if pdfkit and (pdf_config or WKHTMLTOPDF_PATH is not None):
        try:
            options = {"page-size":"A4", "encoding":"UTF-8", "margin-top":"12mm","margin-bottom":"12mm","margin-left":"12mm","margin-right":"12mm"}
            pdf_bytes = pdfkit.from_string(full_html.decode("utf-8"), False, options=options, configuration=pdf_config)
            return send_file(BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=f"{r.full_name}_resume.pdf")
        except Exception as e:
            print("pdfkit failed:", e)
            flash("Use your browser Print -> Save as PDF.")
            return render_template("preview.html", data=data, template_file=template_name, title="Preview")
    else:
        flash("Use browser Print -> Save as PDF.")
        return render_template("preview.html", data=data, template_file=template_name, title="Preview")


if __name__ == "__main__":
    print("Starting Resume Builder app...")
    if llm:
        print("✓ Gemini AI enhancements enabled")
    else:
        print("✗ Gemini API key not found — AI enhancements disabled")
    if pdfkit:
        print("✓ pdfkit available; wkhtmltopdf path:", WKHTMLTOPDF_PATH or "(auto)")
    else:
        print("✗ pdfkit not installed — server PDF generation disabled; browser fallback only")
    app.run(debug=True)
