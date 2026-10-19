"""
WTForms definitions for Smart Campus Navigator.
Provides form validation and CSRF protection for authentication and building management.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    IntegerField,
    FloatField,
    SelectField,
    SubmitField
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    Regexp
)


class LoginForm(FlaskForm):
    """Secure administrator login form with length and presence validation."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters.")
        ],
        render_kw={"placeholder": "Enter admin username", "autocomplete": "username", "autofocus": True}
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Password is required.")
        ],
        render_kw={"placeholder": "Enter password", "autocomplete": "current-password"}
    )
    submit = SubmitField('Sign In to Admin Portal')


class BuildingForm(FlaskForm):
    """Comprehensive building creation and update form with strict field validations."""
    name = StringField(
        'Building Name',
        validators=[
            DataRequired(message="Building name is required."),
            Length(min=2, max=150, message="Building name must be between 2 and 150 characters.")
        ],
        render_kw={"placeholder": "e.g., Ada Lovelace Computational Science Center"}
    )
    code = StringField(
        'Building Code',
        validators=[
            DataRequired(message="Building code is required."),
            Length(min=2, max=10, message="Building code must be between 2 and 10 characters."),
            Regexp(r'^[A-Za-z0-9_-]+$', message="Code must contain only letters, numbers, hyphens or underscores.")
        ],
        render_kw={"placeholder": "e.g., ALC (Uppercase recommended)"}
    )
    category = SelectField(
        'Campus Category',
        choices=[
            ('Academic', 'Academic - Classrooms & Laboratories'),
            ('Library', 'Library - Study & Research Collections'),
            ('Administrative', 'Administrative - Executive & Services'),
            ('Student Life', 'Student Life - Recreation & Activities'),
            ('Sports', 'Sports - Athletics & Fitness'),
            ('Residential', 'Residential - Student Living'),
            ('Dining', 'Dining - Food Courts & Cafes'),
            ('Services', 'Services - Health, IT & Maintenance'),
            ('Other', 'Other - Campus Landmark')
        ],
        validators=[DataRequired(message="Please select a valid category.")],
        default='Academic'
    )
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=1000, message="Description must not exceed 1000 characters.")
        ],
        render_kw={"placeholder": "Overview of facilities, academic departments, and services housed here...", "rows": 4}
    )
    floors = IntegerField(
        'Floors Count',
        validators=[
            DataRequired(message="Number of floors is required."),
            NumberRange(min=1, max=100, message="Floors must be between 1 and 100.")
        ],
        default=1,
        render_kw={"min": 1, "max": 100}
    )
    total_rooms = IntegerField(
        'Total Rooms',
        validators=[
            DataRequired(message="Total rooms count is required."),
            NumberRange(min=1, max=5000, message="Total rooms must be between 1 and 5000.")
        ],
        default=10,
        render_kw={"min": 1, "max": 5000}
    )
    opening_hours = StringField(
        'Opening Hours',
        validators=[
            Optional(),
            Length(max=120, message="Opening hours must not exceed 120 characters.")
        ],
        default='08:00 AM - 08:00 PM (Daily)',
        render_kw={"placeholder": "e.g., 07:30 AM - 10:00 PM (Mon-Sat)"}
    )
    latitude = FloatField(
        'Latitude Coordinate',
        validators=[
            Optional(),
            NumberRange(min=-90.0, max=90.0, message="Latitude must be between -90 and 90 degrees.")
        ],
        render_kw={"placeholder": "e.g., 37.4278", "step": "any"}
    )
    longitude = FloatField(
        'Longitude Coordinate',
        validators=[
            Optional(),
            NumberRange(min=-180.0, max=180.0, message="Longitude must be between -180 and 180 degrees.")
        ],
        render_kw={"placeholder": "e.g., -122.1690", "step": "any"}
    )
    badge_color = SelectField(
        'Badge Color Accent',
        choices=[
            ('indigo', 'Indigo (Primary Academic)'),
            ('emerald', 'Emerald (Science & Green Spaces)'),
            ('amber', 'Amber (Library & Dining)'),
            ('slate', 'Slate (Administrative & Security)'),
            ('rose', 'Rose (Residential & Health)'),
            ('sky', 'Sky (Student Centers)'),
            ('purple', 'Purple (Arts & Auditorium)'),
            ('teal', 'Teal (Innovation & Technology)')
        ],
        default='indigo'
    )
    icon = StringField(
        'FontAwesome Icon Class',
        validators=[
            Optional(),
            Length(max=50, message="Icon class must not exceed 50 characters.")
        ],
        default='fa-building',
        render_kw={"placeholder": "fa-building, fa-laptop-code, fa-flask, fa-landmark..."}
    )
    submit = SubmitField('Save Building')


class DeleteBuildingForm(FlaskForm):
    """CSRF-protected form for safe building deletion."""
    submit = SubmitField('Delete Building')
