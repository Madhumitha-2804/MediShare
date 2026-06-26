import os

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from database import db
from models import (
    User,
    NGO,
    NGORequirement,
    MedicineDonation,
    MedicineRequest
)

from ai_models.match_ngo import match_ngo


# ==========================
# AI LAZY LOADING
# ==========================

verifier = None


def get_verifier():
    global verifier

    if verifier is None:
        from ai_models.verify_medicine import MedicineVerifier
        verifier = MedicineVerifier()

    return verifier



# ==========================
# FLASK CONFIG
# ==========================

template_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "templates")
)

app = Flask(
    __name__,
    template_folder=template_dir
)


app.secret_key = "super_secret_session_key_medishare"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///medishare.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = "uploads"

app.config["ALLOWED_EXTENSIONS"] = {
    "png",
    "jpg",
    "jpeg"
}


os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)



# ==========================
# DATABASE INIT
# ==========================

db.init_app(app)



# ==========================
# HELPERS
# ==========================

def allowed_file(filename):

    return (
        "." in filename and
        filename.rsplit(".",1)[1].lower()
        in app.config["ALLOWED_EXTENSIONS"]
    )



# ==========================
# DATABASE SEED
# ==========================

@app.before_request
def create_tables_and_seeds():

    db.create_all()


    if not NGO.query.first():

        ngo1 = NGO(
            name="Helping Hands NGO",
            location="chennai"
        )

        ngo2 = NGO(
            name="Care Foundation",
            location="coimbatore"
        )


        ngo3 = NGO(
            name="Hope Medical Trust",
            location="madurai"
        )


        db.session.add_all(
            [
                ngo1,
                ngo2,
                ngo3
            ]
        )


        db.session.commit()



        db.session.add_all(
            [

            NGORequirement(
                ngo_id=ngo1.id,
                medicine_name="PARACETAMOL"
            ),

            NGORequirement(
                ngo_id=ngo1.id,
                medicine_name="DOLO"
            ),

            NGORequirement(
                ngo1.id,
                medicine_name="AMOXICILLIN"
            ),

            NGORequirement(
                ngo2.id,
                medicine_name="AZITHROMYCIN"
            ),

            NGORequirement(
                ngo2.id,
                medicine_name="CETIRIZINE"
            ),

            NGORequirement(
                ngo3.id,
                medicine_name="PARACETAMOL"
            )

            ]
        )


        db.session.commit()



    if not User.query.filter_by(
        username="demo_user"
    ).first():


        user = User(

            username="demo_user",

            password=generate_password_hash(
                "password123"
            ),

            role="Consumer",

            age=25,

            phone="9876543210",

            address="Chennai"

        )


        db.session.add(user)

        db.session.commit()





# ==========================
# PAGE ROUTES
# ==========================


@app.route("/")
def home():

    return render_template(
        "login.html"
    )



@app.route("/role-selection")
def role_selection():

    return render_template(
        "role-selection.html"
    )



@app.route("/consumer-dashboard")
def consumer_dashboard():

    return render_template(
        "consumer-dashboard.html"
    )



@app.route("/consumer-profile")
def consumer_profile():

    return render_template(
        "consumer-profile.html"
    )



@app.route("/donor-dashboard")
def donor_dashboard():

    return render_template(
        "donor-dashboard.html"
    )



@app.route("/donate-medicine")
def donate_medicine():

    return render_template(
        "donate-medicine.html"
    )


@app.route("/my-donations")
def my_donations():

    donations = MedicineDonation.query.all()

    return render_template(
        "my_donations.html",
        donations=donations
    )


@app.route("/request-medicine",
methods=["GET","POST"])

def request_medicine():


    if request.method=="POST":


        medicine_name = request.form.get(
            "medicine_name"
        ).upper()


        quantity = request.form.get(
            "quantity"
        )


        address = request.form.get(
            "address"
        )



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



        return jsonify(
            {
            "status":"success",
            "message":"Request submitted"
            }
        )



    return render_template(
        "request-medicine.html"
    )




@app.route("/my-requests")
def my_requests():

    return render_template(
        "my-requests.html"
    )





# ==========================
# API
# ==========================


@app.route(
"/api/profile",
methods=["GET","POST"]
)

def manage_profile():


    user = User.query.filter_by(
        username="demo_user"
    ).first()



    if request.method=="POST":


        data=request.json


        user.username=data.get(
            "name",
            user.username
        )


        user.age=data.get(
            "age",
            user.age
        )


        user.phone=data.get(
            "phone",
            user.phone
        )


        user.address=data.get(
            "address",
            user.address
        )


        db.session.commit()


        return jsonify(
            {
            "status":"success"
            }
        )




    return jsonify({

        "name":user.username,

        "age":user.age,

        "phone":user.phone,

        "address":user.address,

        "aadhaar_status":"Verified"

    })






@app.route("/api/my-requests")
def get_user_requests():


    data=[]


    requests = MedicineRequest.query.all()



    for r in requests:


        data.append({

            "medicine_name":r.medicine_name,

            "quantity":r.quantity,

            "status":r.status,

            "reason":r.reason,

            "address":r.address

        })



    return jsonify(
        {
        "requests":data
        }
    )






# ==========================
# AI VERIFY MEDICINE
# ==========================


@app.route(
"/verify-medicine",
methods=["POST"]
)

def verify_medicine_route():


    files=request.files.getlist(
        "images"
    )


    saved=[]



    for file in files:


        if allowed_file(file.filename):


            filename=secure_filename(
                file.filename
            )


            path=os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )


            file.save(path)


            saved.append(path)




    if not saved:

        return jsonify(
            {
            "error":"No images"
            }
        )




    result = get_verifier().verify_medicine(
        saved
    )



    donation = MedicineDonation(

        user_id=1,

        medicine_name=result["medicine_name"],

        expiry_date=result["expiry_date"],

        status=result["status"],

        reason=result["reason"]

    )



    db.session.add(donation)

    db.session.commit()



    return jsonify(result)






if __name__=="__main__":

    app.run(
        debug=True,
        port=5000
    )