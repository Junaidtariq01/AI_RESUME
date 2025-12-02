from flask import Flask, render_template
from Flask_wtf  import FlaskForm

app=Flask(__name__)

class Register(FlaskForm):
    name=stringField("name",validators=[DataRequired()])
    email=stringField("email",validators=[DataRequired() ])
@app.route('/')
def index():
    return render_template("base.html")
   
@app.route('/register')
def register():
    form = Register()
    if form.validate_on_submit():
        name=form.name.data
        email=form.email.data
        hashed_pass= bcrypt
if __name__=="__main__":
    app.run(debug=True) 