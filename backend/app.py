import os
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash 

from database import db
from models import User, NGO, NGORequirement, MedicineDonation, MedicineRequest
from ai_models.verify_medicine import MedicineVerifier
from ai_models.match_ngo import match_ngo

# Setup dynamic absolute paths for templates folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = "super_secret_session_key_medishare"

# App Configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///medishare.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize Database and AI Engine
db.init_app(app)
verifier = MedicineVerifier()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# --- AUTOMATIC DATABASE SEEDING ---
@app.before_request
def create_tables_and_seeds():
    db.create_all()
    
    # Seed NGOs if missing
    if not NGO.query.first():
        ngo1 = NGO(name="Helping Hands NGO", location="chennai")
        ngo2 = NGO(name="Care Foundation", location="coimbatore")
        ngo3 = NGO(name="Hope Medical Trust", location="madurai")
        db.session.add_all([ngo1, ngo2, ngo3])
        db.session.commit()

        db.session.add_all([
            NGORequirement(ngo_id=ngo1.id, medicine_name="PARACETAMOL"),
            NGORequirement(ngo_id=ngo1.id, medicine_name="DOLO"),
            NGORequirement(ngo_id=ngo1.id, medicine_name="AMOXICILLIN"),
            NGORequirement(ngo_id=ngo2.id, medicine_name="AZITHROMYCIN"),
            NGORequirement(ngo_id=ngo2.id, medicine_name="CETIRIZINE"),
            NGORequirement(ngo_id=ngo3.id, medicine_name="PARACETAMOL"),
            NGORequirement(ngo_id=ngo3.id, medicine_name="IBUPROFEN")
        ])
        db.session.commit()
        
    # Seed standard consumer testing profile if missing
    if not User.query.filter_by(username="demo_user").first():
        default_user = User(
            username="demo_user", 
            password=generate_password_hash("password123"),
            role="Consumer", 
            age=25, 
            phone="9876543210", 
            address="123 Main St, Chennai"
        )
        db.session.add(default_user)
        db.session.commit()

# --- WEB UI ROUTING VIEWS ---
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/consumer-dashboard")
def consumer_dashboard():
    return render_template("consumer-dashboard.html")

@app.route("/consumer-profile")
def consumer_profile():
    return render_template("consumer-profile.html")

@app.route("/request-medicine", methods=["GET", "POST"])
def request_medicine():
    if request.method == "POST":
        # 1. Grab text fields from form
        medicine_name = request.form.get("medicine_name", "").strip().upper()
        quantity = request.form.get("quantity")
        address = request.form.get("address")
        aadhaar = request.form.get("aadhaar")
        
        # 2. Handle the prescription file upload
        if "prescription" not in request.files:
            return jsonify({"status": "error", "message": "Prescription file is mandatory"}), 400
            
        file = request.files["prescription"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            
            # 3. Save the request details to the database (Properly Indented)
            new_request = MedicineRequest(
                user_id=1, 
                medicine_name=medicine_name,
                quantity=quantity,
                reason="Prescription Submitted",
                address=address,
                status="Pending"
            )
            db.session.add(new_request)
            db.session.commit()
            
            return jsonify({"status": "success", "message": "Medicine request submitted successfully!"})
            
        return jsonify({"status": "error", "message": "Invalid file type format"}), 400

    # If it's a regular GET request, just show the HTML form page
    return render_template("request-medicine.html")

@app.route("/my-requests")
def my_requests():
    return render_template("my-requests.html")

@app.route("/role-selection")
def role_selection():
    return render_template("role-selection.html")

@app.route("/donate-medicine")
def donate_medicine():
    return render_template("donate-medicine.html")


# --- SYSTEM API ENDPOINTS ---
@app.route("/api/profile", methods=["GET", "POST"])
def manage_profile():
    user = User.query.filter_by(username="demo_user").first()
    if not user:
        return jsonify({"status": "error", "message": "User context unavailable"}), 404

    if request.method == "POST":
        data = request.json or request.form
        user.username = data.get("name", user.username)
        user.age = data.get("age", user.age)
        user.phone = data.get("phone", user.phone)
        user.address = data.get("address", user.address)
        db.session.commit()
        return jsonify({"status": "success", "message": "Profile updated successfully"})
    
    pending_count = MedicineRequest.query.filter_by(user_id=user.id, status="Pending").count()
    approved_count = MedicineRequest.query.filter_by(user_id=user.id, status="Approved").count()

    return jsonify({
        "name": user.username,
        "age": user.age,
        "phone": user.phone,
        "address": user.address,
        "aadhaar_status": "Verified",
        "pending": pending_count,
        "approved": approved_count
    })
@app.route("/api/my-requests", methods=["GET"])
def get_user_requests():
    # Fetch data from DB
    requests = MedicineRequest.query.all()
    output = []
    for req in requests:
        output.append({
            "medicine_name": req.medicine_name,
            "status": req.status,
            "quantity": req.quantity,
            "reason": req.reason,
            "address": req.address
        })
    return jsonify({"requests": output})
@app.route("/donor-dashboard")
def donor_dashboard():
    return render_template("donor_dashboard.html")

@app.route("/verify-medicine", methods=["POST"])
def verify_medicine_route():
    if "images" not in request.files:
        return jsonify({"status": "error", "message": "No medicine images uploaded"}), 400

    files = request.files.getlist("images")
    donor_location = request.form.get("donor_location", "").strip().lower()
    user_id = request.form.get("user_id", 1) 

    saved_image_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            saved_image_paths.append(file_path)

    if not saved_image_paths:
        return jsonify({"status": "error", "message": "No valid image files received."}), 400

    verification_result = verifier.verify_medicine(saved_image_paths)

    donation = MedicineDonation(
        user_id=user_id,
        medicine_name=verification_result["medicine_name"],
        expiry_date=verification_result["expiry_date"],
        status=verification_result["status"],
        reason=verification_result["reason"]
    )
    db.session.add(donation)
    db.session.commit()

    response = {
        "status": "success",
        "verification_result": verification_result,
        "ngo_matches": []
    }

    if verification_result["status"] == "VERIFIED":
        db_ngos = NGO.query.all()
        ngo_data_payload = []
        for ngo in db_ngos:
            ngo_data_payload.append({
                "ngo_name": ngo.name,
                "location": ngo.location,
                "required_medicines": [req.medicine_name for req in ngo.requirements]
            })
        
        ngo_matches = match_ngo(verification_result["medicine_name"], donor_location, ngo_data_payload)
        response["ngo_matches"] = ngo_matches

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)