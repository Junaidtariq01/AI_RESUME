import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

class ResumeBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Resume Builder")
        self.root.geometry("800x900")
        self.root.configure(bg='#ecf0f1')
        
        # Create main container with scrollbar
        main_container = tk.Frame(root, bg='#ecf0f1')
        main_container.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)
        
        # Canvas for scrolling
        canvas = tk.Canvas(main_container, bg='#ecf0f1', highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Content frame
        self.content_frame = tk.Frame(canvas, bg='#ecf0f1')
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        self.photo_path = None
        self.create_widgets()
        
    def create_widgets(self):
        row = 0
        
        # Main Title
        title_frame = tk.Frame(self.content_frame, bg='#2c3e50', padx=20, pady=15)
        title_frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 20))
        
        title = tk.Label(title_frame, text="📄 Professional Resume Builder", 
                        font=("Arial", 26, "bold"), bg='#2c3e50', fg='white')
        title.pack()
        subtitle = tk.Label(title_frame, text="Create your professional resume in minutes", 
                           font=("Arial", 11), bg='#2c3e50', fg='#ecf0f1')
        subtitle.pack()
        
        row += 1
        
        # Personal Information Section
        self.add_section_header("👤 Personal Information", row)
        row += 1
        
        self.name_entry = self.add_field("Full Name *:", row)
        row += 1
        self.email_entry = self.add_field("Email Address *:", row)
        row += 1
        self.phone_entry = self.add_field("Phone Number *:", row)
        row += 1
        self.location_entry = self.add_field("Location (City, Country):", row)
        row += 1
        self.linkedin_entry = self.add_field("LinkedIn URL:", row)
        row += 1
        self.github_entry = self.add_field("GitHub URL:", row)
        row += 1
        self.portfolio_entry = self.add_field("Portfolio Website:", row)
        row += 1
        
        # Photo Upload
        photo_label = tk.Label(self.content_frame, text="Profile Photo (optional):", 
                              font=("Arial", 10, "bold"), bg='#ecf0f1')
        photo_label.grid(row=row, column=0, sticky='w', padx=20, pady=5)
        
        photo_btn = tk.Button(self.content_frame, text="Choose Photo", 
                             command=self.choose_photo, bg='#95a5a6', fg='white',
                             font=("Arial", 9), padx=10, pady=5, cursor='hand2')
        photo_btn.grid(row=row, column=1, sticky='w', padx=20, pady=5)
        
        self.photo_label = tk.Label(self.content_frame, text="No photo selected", 
                                    font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d')
        self.photo_label.grid(row=row, column=1, sticky='e', padx=20, pady=5)
        row += 1
        
        # Professional Summary
        self.add_section_header("📝 Professional Summary", row)
        row += 1
        self.summary_text = self.add_text_field("Write a brief professional summary (2-3 sentences):", 
                                                row, height=4)
        row += 1
        
        # Education
        self.add_section_header("🎓 Education", row)
        row += 1
        instruction = tk.Label(self.content_frame, 
                              text="Format: Degree | Institution | Year | GPA (one per line)\nExample: B.Tech Computer Science | IUST | 2021-2025 | 8.5 CGPA",
                              font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        instruction.grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 5))
        row += 1
        self.education_text = self.add_text_field("", row, height=5)
        row += 1
        
        # Work Experience
        self.add_section_header("💼 Work Experience", row)
        row += 1
        instruction = tk.Label(self.content_frame,
                              text="Format: Job Title | Company | Duration | Description (one entry per line)\nExample: Software Engineer | Tech Corp | Jun 2024-Present | Developed web applications",
                              font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        instruction.grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 5))
        row += 1
        self.experience_text = self.add_text_field("", row, height=6)
        row += 1
        
        # Projects
        self.add_section_header("🚀 Projects", row)
        row += 1
        instruction = tk.Label(self.content_frame,
                              text="Format: Project Name | Technologies | Description | Link (one per line)\nExample: E-Commerce Site | Node.js, MongoDB | Built full-stack app | github.com/user/project",
                              font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        instruction.grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 5))
        row += 1
        self.projects_text = self.add_text_field("", row, height=6)
        row += 1
        
        # Skills
        self.add_section_header("💻 Technical Skills", row)
        row += 1
        self.languages_entry = self.add_field("Programming Languages (comma-separated):", row)
        row += 1
        self.frameworks_entry = self.add_field("Frameworks & Libraries:", row)
        row += 1
        self.tools_entry = self.add_field("Tools & Technologies:", row)
        row += 1
        self.databases_entry = self.add_field("Databases:", row)
        row += 1
        
        # Certifications
        self.add_section_header("🏆 Certifications", row)
        row += 1
        instruction = tk.Label(self.content_frame,
                              text="One certification per line",
                              font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        instruction.grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 5))
        row += 1
        self.certifications_text = self.add_text_field("", row, height=4)
        row += 1
        
        # Achievements
        self.add_section_header("⭐ Achievements", row)
        row += 1
        instruction = tk.Label(self.content_frame,
                              text="One achievement per line",
                              font=("Arial", 9, "italic"), bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        instruction.grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=(0, 5))
        row += 1
        self.achievements_text = self.add_text_field("", row, height=4)
        row += 1
        
        # Output filename
        self.add_section_header("💾 Output Settings", row)
        row += 1
        self.filename_entry = self.add_field("Output Filename (without .pdf):", row)
        self.filename_entry.insert(0, "my_resume")
        row += 1
        
        # Generate Button
        button_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        button_frame.grid(row=row, column=0, columnspan=2, pady=30)
        
        generate_btn = tk.Button(button_frame, text="🎯 Generate Resume PDF", 
                                command=self.generate_resume,
                                bg='#27ae60', fg='white', font=("Arial", 16, "bold"),
                                padx=40, pady=15, cursor='hand2', relief=tk.RAISED,
                                borderwidth=3)
        generate_btn.pack(side=tk.LEFT, padx=10)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear All", 
                             command=self.clear_all,
                             bg='#e74c3c', fg='white', font=("Arial", 12, "bold"),
                             padx=20, pady=15, cursor='hand2', relief=tk.RAISED,
                             borderwidth=3)
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # Footer
        footer = tk.Label(self.content_frame, 
                         text="© 2025 Resume Builder | All fields marked with * are required",
                         font=("Arial", 9), bg='#ecf0f1', fg='#95a5a6')
        footer.grid(row=row+1, column=0, columnspan=2, pady=10)
        
    def add_section_header(self, text, row):
        header_frame = tk.Frame(self.content_frame, bg='#3498db', padx=15, pady=10)
        header_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(15, 10), padx=20)
        
        header = tk.Label(header_frame, text=text, font=("Arial", 13, "bold"), 
                         bg='#3498db', fg='white')
        header.pack(anchor='w')
        
    def add_field(self, label_text, row):
        label = tk.Label(self.content_frame, text=label_text, 
                        font=("Arial", 10, "bold"), bg='#ecf0f1', fg='#2c3e50')
        label.grid(row=row, column=0, sticky='w', padx=20, pady=8)
        
        entry = tk.Entry(self.content_frame, font=("Arial", 10), width=55, 
                        relief=tk.SOLID, borderwidth=1)
        entry.grid(row=row, column=1, padx=20, pady=8, sticky='ew')
        return entry
    
    def add_text_field(self, label_text, row, height=5):
        if label_text:
            label = tk.Label(self.content_frame, text=label_text, 
                            font=("Arial", 10, "bold"), bg='#ecf0f1', fg='#2c3e50')
            label.grid(row=row, column=0, sticky='nw', padx=20, pady=8)
        
        text_widget = scrolledtext.ScrolledText(self.content_frame, font=("Arial", 10), 
                                                width=55, height=height, wrap=tk.WORD,
                                                relief=tk.SOLID, borderwidth=1)
        text_widget.grid(row=row, column=1, padx=20, pady=8, sticky='ew')
        return text_widget
    
    def choose_photo(self):
        filename = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        if filename:
            self.photo_path = filename
            self.photo_label.config(text=os.path.basename(filename), fg='#27ae60')
    
    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all fields?"):
            # Clear all entry fields
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.location_entry.delete(0, tk.END)
            self.linkedin_entry.delete(0, tk.END)
            self.github_entry.delete(0, tk.END)
            self.portfolio_entry.delete(0, tk.END)
            
            # Clear text fields
            self.summary_text.delete("1.0", tk.END)
            self.education_text.delete("1.0", tk.END)
            self.experience_text.delete("1.0", tk.END)
            self.projects_text.delete("1.0", tk.END)
            self.certifications_text.delete("1.0", tk.END)
            self.achievements_text.delete("1.0", tk.END)
            
            # Clear skills
            self.languages_entry.delete(0, tk.END)
            self.frameworks_entry.delete(0, tk.END)
            self.tools_entry.delete(0, tk.END)
            self.databases_entry.delete(0, tk.END)
            
            # Reset photo
            self.photo_path = None
            self.photo_label.config(text="No photo selected", fg='#7f8c8d')
            
            messagebox.showinfo("Success", "All fields cleared!")
    
    def generate_resume(self):
        # Validate required fields
        if not self.name_entry.get().strip():
            messagebox.showerror("Validation Error", "Please enter your Full Name!")
            return
        if not self.email_entry.get().strip():
            messagebox.showerror("Validation Error", "Please enter your Email Address!")
            return
        if not self.phone_entry.get().strip():
            messagebox.showerror("Validation Error", "Please enter your Phone Number!")
            return
        
        # Collect data
        data = {
            'name': self.name_entry.get().strip(),
            'email': self.email_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'location': self.location_entry.get().strip(),
            'linkedin': self.linkedin_entry.get().strip(),
            'github': self.github_entry.get().strip(),
            'portfolio': self.portfolio_entry.get().strip(),
            'summary': self.summary_text.get("1.0", tk.END).strip(),
            'education': [e.strip() for e in self.education_text.get("1.0", tk.END).strip().split('\n') if e.strip()],
            'experience': [e.strip() for e in self.experience_text.get("1.0", tk.END).strip().split('\n') if e.strip()],
            'projects': [p.strip() for p in self.projects_text.get("1.0", tk.END).strip().split('\n') if p.strip()],
            'languages': self.languages_entry.get().strip(),
            'frameworks': self.frameworks_entry.get().strip(),
            'tools': self.tools_entry.get().strip(),
            'databases': self.databases_entry.get().strip(),
            'certifications': [c.strip() for c in self.certifications_text.get("1.0", tk.END).strip().split('\n') if c.strip()],
            'achievements': [a.strip() for a in self.achievements_text.get("1.0", tk.END).strip().split('\n') if a.strip()],
            'photo': self.photo_path
        }
        
        # Get filename
        filename = self.filename_entry.get().strip()
        if not filename:
            filename = "my_resume"
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Generate PDF
        try:
            self.create_pdf(data, filename)
            messagebox.showinfo("Success", f"✓ Resume generated successfully!\n\nSaved as: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
    
    def create_pdf(self, data, filename):
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=26, alignment=TA_CENTER,
                                     textColor=colors.HexColor('#1a1a1a'),
                                     spaceAfter=8, fontName='Helvetica-Bold')
        
        contact_style = ParagraphStyle('Contact', parent=styles['Normal'],
                                       fontSize=9, alignment=TA_CENTER,
                                       textColor=colors.HexColor('#555555'),
                                       spaceAfter=4)
        
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                       fontSize=13, textColor=colors.HexColor('#2c3e50'),
                                       spaceAfter=10, spaceBefore=12,
                                       fontName='Helvetica-Bold',
                                       borderWidth=1, borderColor=colors.HexColor('#3498db'),
                                       borderPadding=4, backColor=colors.HexColor('#ecf0f1'))
        
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                      fontSize=10, leading=14,
                                      textColor=colors.HexColor('#2c3e50'))
        
        bold_style = ParagraphStyle('Bold', parent=normal_style,
                                    fontName='Helvetica-Bold', fontSize=10)
        
        # Name
        story.append(Paragraph(data['name'], title_style))
        
        # Contact Info
        contact_parts = [data['email'], data['phone']]
        if data['location']:
            contact_parts.append(data['location'])
        story.append(Paragraph(' | '.join(contact_parts), contact_style))
        
        # Links
        links = []
        if data['linkedin']:
            links.append(f"LinkedIn: {data['linkedin']}")
        if data['github']:
            links.append(f"GitHub: {data['github']}")
        if data['portfolio']:
            links.append(f"Portfolio: {data['portfolio']}")
        
        if links:
            story.append(Paragraph(' | '.join(links), contact_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Professional Summary
        if data['summary']:
            story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
            story.append(Paragraph(data['summary'], normal_style))
            story.append(Spacer(1, 0.15*inch))
        
        # Education
        if data['education']:
            story.append(Paragraph("EDUCATION", heading_style))
            for edu in data['education']:
                parts = edu.split('|')
                if len(parts) >= 3:
                    edu_text = f"<b>{parts[0].strip()}</b><br/>{parts[1].strip()} | {parts[2].strip()}"
                    if len(parts) >= 4:
                        edu_text += f" | {parts[3].strip()}"
                else:
                    edu_text = edu
                story.append(Paragraph(edu_text, normal_style))
                story.append(Spacer(1, 0.08*inch))
        
        # Work Experience
        if data['experience']:
            story.append(Paragraph("WORK EXPERIENCE", heading_style))
            for exp in data['experience']:
                parts = exp.split('|')
                if len(parts) >= 3:
                    story.append(Paragraph(f"<b>{parts[0].strip()}</b> - {parts[1].strip()}", normal_style))
                    story.append(Paragraph(f"<i>{parts[2].strip()}</i>", normal_style))
                    if len(parts) >= 4:
                        story.append(Paragraph(f"• {parts[3].strip()}", normal_style))
                else:
                    story.append(Paragraph(f"• {exp}", normal_style))
                story.append(Spacer(1, 0.08*inch))
        
        # Projects
        if data['projects']:
            story.append(Paragraph("PROJECTS", heading_style))
            for proj in data['projects']:
                parts = proj.split('|')
                if len(parts) >= 2:
                    proj_header = f"<b>{parts[0].strip()}</b> | <i>{parts[1].strip()}</i>"
                    story.append(Paragraph(proj_header, normal_style))
                    if len(parts) >= 3:
                        story.append(Paragraph(f"• {parts[2].strip()}", normal_style))
                    if len(parts) >= 4:
                        story.append(Paragraph(f"Link: {parts[3].strip()}", 
                                             ParagraphStyle('Link', parent=normal_style, fontSize=8)))
                else:
                    story.append(Paragraph(f"• {proj}", normal_style))
                story.append(Spacer(1, 0.08*inch))
        
        # Technical Skills
        if any([data['languages'], data['frameworks'], data['tools'], data['databases']]):
            story.append(Paragraph("TECHNICAL SKILLS", heading_style))
            if data['languages']:
                story.append(Paragraph(f"<b>Programming Languages:</b> {data['languages']}", normal_style))
            if data['frameworks']:
                story.append(Paragraph(f"<b>Frameworks & Libraries:</b> {data['frameworks']}", normal_style))
            if data['tools']:
                story.append(Paragraph(f"<b>Tools & Technologies:</b> {data['tools']}", normal_style))
            if data['databases']:
                story.append(Paragraph(f"<b>Databases:</b> {data['databases']}", normal_style))
            story.append(Spacer(1, 0.12*inch))
        
        # Certifications
        if data['certifications']:
            story.append(Paragraph("CERTIFICATIONS", heading_style))
            for cert in data['certifications']:
                story.append(Paragraph(f"• {cert}", normal_style))
            story.append(Spacer(1, 0.12*inch))
        
        # Achievements
        if data['achievements']:
            story.append(Paragraph("ACHIEVEMENTS", heading_style))
            for achievement in data['achievements']:
                story.append(Paragraph(f"• {achievement}", normal_style))
        
        # Build PDF
        doc.build(story)

if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeBuilderGUI(root)
    root.mainloop()
     