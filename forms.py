from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Length

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

class CompanySetupForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    logo_url = StringField('Logo URL', validators=[Length(max=255)])
    contact_info = TextAreaField('Contact Information')
