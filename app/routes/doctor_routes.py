from flask import Blueprint, request, jsonify
from app import db
from app.models import Doctor, Appointment, MedicalRecord  # Ensure necessary models are imported
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token

bp = Blueprint('doctor_routes', __name__, url_prefix='/doctors')

# Register a new doctor
@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    if Doctor.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    new_doctor = Doctor(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=email,
        specialization=data.get('specialization'),
    )
    new_doctor.set_password(data.get('password'))
    db.session.add(new_doctor)
    db.session.commit()

    return jsonify({"message": "Doctor registered successfully!"}), 201

# Doctor login
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    doctor = Doctor.query.filter_by(email=email).first()

    if not doctor or not doctor.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT token
    access_token = create_access_token(identity={"id": doctor.id, "role": "doctor"})
    return jsonify({"access_token": access_token}), 200

# View Assigned Appointments
@bp.route('/appointments', methods=['GET'])
@jwt_required()
def view_appointments():
    # Get the logged-in doctor's ID
    user = get_jwt_identity()
    if user['role'] != 'doctor':
        return jsonify({"error": "Unauthorized access"}), 403

    doctor_id = user['id']

    # Fetch appointments for the logged-in doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()

    # Return the appointments as JSON
    return jsonify([{
        "id": appointment.id,
        "patient_name": appointment.full_name,
        "address": appointment.address,
        "date_time": appointment.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        "patient_id": appointment.patient_id
    } for appointment in appointments]), 200

# Provide Diagnosis
@bp.route('/diagnosis', methods=['POST'])
@jwt_required()
def provide_diagnosis():
    # Get the logged-in doctor's ID
    user = get_jwt_identity()
    if user['role'] != 'doctor':
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()

    # Validate input
    required_fields = ["appointment_id", "age", "height", "blood_pressure", "oxygen_level", "symptoms", "diagnosis", "prescription"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    appointment = Appointment.query.get(data['appointment_id'])

    if not appointment or appointment.doctor_id != user['id']:
        return jsonify({"error": "Invalid or unauthorized appointment"}), 404

    # Create a new MedicalRecord
    medical_record = MedicalRecord(
        appointment_id=data['appointment_id'],
        age=data['age'],
        height=data['height'],
        blood_pressure=data['blood_pressure'],
        oxygen_level=data['oxygen_level'],
        symptoms=data['symptoms'],
        diagnosis=data['diagnosis'],
        prescription=data['prescription']
    )

    # Save to database
    db.session.add(medical_record)
    db.session.commit()

    return jsonify({"message": "Diagnosis and prescription saved successfully"}), 201

# View Past Diagnoses
@bp.route('/diagnoses', methods=['GET'])
@jwt_required()
def view_past_diagnoses():
    # Get the logged-in doctor's ID
    user = get_jwt_identity()
    if user['role'] != 'doctor':
        return jsonify({"error": "Unauthorized access"}), 403

    doctor_id = user['id']

    # Fetch past medical records for the logged-in doctor
    medical_records = MedicalRecord.query.join(Appointment).filter(Appointment.doctor_id == doctor_id).all()

    if not medical_records:
        return jsonify({"message": "No past diagnoses found."}), 404

    # Return the medical records as JSON
    return jsonify([{
        "appointment_id": record.appointment_id,
        "patient_name": record.appointment.full_name,
        "date_time": record.appointment.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        "age": record.age,
        "height": record.height,
        "blood_pressure": record.blood_pressure,
        "oxygen_level": record.oxygen_level,
        "symptoms": record.symptoms,
        "diagnosis": record.diagnosis,
        "prescription": record.prescription
    } for record in medical_records]), 200
