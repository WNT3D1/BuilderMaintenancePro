from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class MaintenanceLogForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    lot_number = StringField('Lot Number', validators=[DataRequired(), Length(max=50)])
    contact_details = StringField('Contact Details', validators=[DataRequired(), Length(max=255)])
    maintenance_class = SelectField('Maintenance Class', choices=[
        ('3MTR', '3MTR'),
        ('IAS', 'IAS'),
        ('Supplier', 'Supplier')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    allocation = StringField('Allocation', validators=[DataRequired(), Length(max=100)])

class WorkOrderForm(FlaskForm):
    maintenance_log_id = SelectField('Maintenance Log', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    assigned_to = StringField('Assigned To', validators=[DataRequired(), Length(max=100)])
    scheduled_date = DateField('Scheduled Date', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], validators=[DataRequired()])
    is_critical = BooleanField('Critical Task')

class CompanySetupForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    logo_url = StringField('Logo URL', validators=[Length(max=255)])
    contact_info = TextAreaField('Contact Information')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
