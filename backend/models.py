from database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

class NGO(db.Model):
    __tablename__ = 'ngos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    requirements = db.relationship('NGORequirement', backref='ngo', lazy=True)

class NGORequirement(db.Model):
    __tablename__ = 'ngo_requirements'
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngos.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)

class MedicineDonation(db.Model):
    __tablename__ = 'medicine_donations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text, nullable=True)

class MedicineRequest(db.Model):
    __tablename__ = 'medicine_requests'
    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50)) # Add this
    reason = db.Column(db.Text)         # Add this
    address = db.Column(db.Text)        # Add this
    status = db.Column(db.String(50), default='Pending')