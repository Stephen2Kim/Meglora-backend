from flask import Blueprint, request, jsonify
from app.models import Patient, Appointment, Doctor, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from datetime import datetime

bp = Blueprint('patient_routes', __name__, url_prefix='/patients')


# Register a new patient
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Ensure all required fields are provided
    required_fields = ['first_name', 'last_name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing field: {field}"}), 400

    # Use a default role if none is provided
    role = data.get('role', 'patient')  # Default to 'patient' if no role is given

    # Create user object
    user = User(first_name=data['first_name'], last_name=data['last_name'],
                email=data['email'], password=data['password'], role=role)
    
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201


# Patient login
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    patient = Patient.query.filter_by(email=email).first()

    if not patient or not patient.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = patient.get_access_token()
    return jsonify({"access_token": access_token}), 200

# Example of a protected route
@bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"user": current_user}), 200

# Create Appointment
@bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    # Get the logged-in user's ID
    user = get_jwt_identity()
    if user['role'] != 'patient':
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()

    # Validate input
    required_fields = ['doctor_id', 'full_name', 'address', 'date_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        # Parse date and time
        date_time = datetime.strptime(data['date_time'], '%Y-%m-%d %H:%M:%S')

        # Check if doctor exists
        doctor = Doctor.query.get(data['doctor_id'])
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        # Create appointment
        appointment = Appointment(
            patient_id=user['id'],
            doctor_id=data['doctor_id'],
            full_name=data['full_name'],
            address=data['address'],
            date_time=date_time
        )

        db.session.add(appointment)
        db.session.commit()

        return jsonify({"message": "Appointment created successfully", "appointment": {
            "id": appointment.id,
            "doctor_id": appointment.doctor_id,
            "full_name": appointment.full_name,
            "address": appointment.address,
            "date_time": appointment.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }}), 201

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}), 400


# View Appointments
@bp.route('/appointments', methods=['GET'])
@jwt_required()
def view_appointments():
    # Get the logged-in user's ID
    user = get_jwt_identity()

    if user['role'] == 'patient':
        # Get appointments for the patient
        appointments = Appointment.query.filter_by(patient_id=user['id']).all()
    elif user['role'] == 'doctor':
        # Get appointments for the doctor
        appointments = Appointment.query.filter_by(doctor_id=user['id']).all()
    else:
        return jsonify({"error": "Unauthorized access"}), 403

    # Serialize data
    appointments_data = [{
        "id": appt.id,
        "full_name": appt.full_name,
        "address": appt.address,
        "date_time": appt.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        "doctor_id": appt.doctor_id,
        "patient_id": appt.patient_id
    } for appt in appointments]

    return jsonify({"appointments": appointments_data}), 200

# Update Appointment
@bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    # Get the logged-in user's ID
    user = get_jwt_identity()
    if user['role'] != 'patient':
        return jsonify({"error": "Unauthorized access"}), 403

    # Fetch the appointment
    appointment = Appointment.query.get(appointment_id)
    if not appointment or appointment.patient_id != user['id']:
        return jsonify({"error": "Appointment not found or unauthorized access"}), 404

    data = request.get_json()

    # Validate input
    if 'doctor_id' in data:
        doctor = Doctor.query.get(data['doctor_id'])
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404
        appointment.doctor_id = data['doctor_id']

    if 'date_time' in data:
        try:
            appointment.date_time = datetime.strptime(data['date_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}), 400

    # Save changes
    db.session.commit()

    return jsonify({"message": "Appointment updated successfully", "appointment": {
        "id": appointment.id,
        "doctor_id": appointment.doctor_id,
        "full_name": appointment.full_name,
        "address": appointment.address,
        "date_time": appointment.date_time.strftime('%Y-%m-%d %H:%M:%S')
    }}), 200

# patient_routes.py

# Route for viewing a patient's medical history (appointments and diagnoses)
@bp.route('/history', methods=['GET'])
@jwt_required()
def view_medical_history():
    current_user_id = get_jwt_identity()  # Get patient ID from the JWT token
    patient = Patient.query.get(current_user_id)

    if not patient:
        return jsonify({"message": "Patient not found"}), 404

    # Fetch appointments and associated medical records
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    history = []

    for appointment in appointments:
        medical_record = appointment.medical_record
        history.append({
            "appointment_id": appointment.id,
            "doctor": f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            "date_time": appointment.date_time,
            "medical_record": {
                "age": medical_record.age,
                "height": medical_record.height,
                "blood_pressure": medical_record.blood_pressure,
                "oxygen_level": medical_record.oxygen_level,
                "symptoms": medical_record.symptoms,
                "diagnosis": medical_record.diagnosis,
                "prescription": medical_record.prescription
            } if medical_record else None
        })

    return jsonify(history), 200
