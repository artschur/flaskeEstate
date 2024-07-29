from flask import Flask, render_template, request, redirect, jsonify, json, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import random
from flask_session import Session

SESSION_TYPE = 'filesystem'
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///estates.db"
db = SQLAlchemy(app)
UPLOAD_FOLDER = "static/images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = f'{random.randint(0, 16)}'
app.config.from_object(__name__)
Session(app)

migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(26), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"User {self.username}"

class Estate(db.Model):
    ownerId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False, default='No address')
    price = db.Column(db.Integer, nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    area = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"estate at {self.address} for {self.price} "

#defining marshmallow schema
class EstateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Estate
        load_instance = True

estate_schema = EstateSchema()

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

user_schema = UserSchema()

@app.route('/auth', methods=['POST', 'GET'])
def auth():
    username = session.get('username')
    password = session.get('password')
    print(f"Auth session data: {username}, {password}")  # Debugging line
    user = User.query.filter_by(username=username).first()
    if user.password == password:
        return redirect(url_for('add'))
    else:
        flash('Invalid username or password')



@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' or password == '':
            return 'Username and password cannot be empty'   
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            print('sucesso')
            session['username'] = username
            return redirect(url_for('index'))
        
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('login'))        

@app.route('/register', methods=['POST', 'GET'])
def createAccount():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' or password == '':
            return 'Username and password cannot be empty'
        if username == User.query.filter_by(username=username).all():
            return 'Username already exists'
        hashed_pass = generate_password_hash(password)


        user = User(username=username, password=hashed_pass)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            return 'Error creating user, it may already exist'
    
        session['username'] = username
        session['password'] = hashed_pass
        print(f"Register session data: {username}, {hashed_pass}")  # Debugging line
  

        return redirect(url_for('add'))


@app.route('/api/all')
def getAllEstates():
    dict = {}
    for i in Estate.query.all():
        dict[i.id] = estate_schema.dump(i)
    return dict

@app.route('/api/<id>/img')
def getImageId(id):
    imovel = Estate.query.get(id)
    try:
        return imovel.image_urlf
    except:
        return ' erro ao encontrar imovel'
    

@app.route('/api/<id>')
def getIdRest(id):
        imovel = Estate.query.get(id)
        try:
            return jsonify(estate_schema.dump(imovel))
        except:
            return 'Esse imovel não existe'

@app.route("/add", methods=["POST", "GET"])
def add():
    if request.method == "POST":
        if 'image' not in request.files:
            return 'No image part'
        file = request.files['image']
        if file.filename == '':
            return 'No selected image'
        if file:
            filename = secure_filename((file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], (filename)))


            address = request.form["address"]
            price = int(request.form["price"].replace(".", ""))
            bedrooms = int(request.form["bedrooms"])
            bathrooms = int(request.form["bathrooms"])
            area = int(request.form["area"])
            typee = request.form.get("type")
            image_url = filename

            estate = Estate(
                ownerId=User.query.filter_by(username=session.get('username')).first().id,
                address=address,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                area=area,
                type=typee,
                img_url=image_url
            )

            db.session.add(estate)
            db.session.commit()
            return redirect("/estates")
    else:
        return render_template("add.html", title="Add Estate", username=session.get('username'))


@app.route("/delete/<id>", methods=["GET", "POST"])
def deleteEstate(id):
    if request.method == "POST":
        estate = Estate.query.get(id)
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], estate.img_url))
        except:
            pass
        db.session.delete(estate)
        db.session.commit()
        return redirect("/")


@app.route("/find/<id>", methods=["GET"])
def show(id):
    try:
        imovel = Estate.query.get(id)
        imovel.price = "{:,}".format(imovel.price)

    except:
        return "erro ao encontrar imóvel"
    return render_template("singleEstate.html", estate=imovel)


@app.route("/estates", methods=["GET"])
def index():
    estates = Estate.query.filter_by(ownerId=User.query.filter_by(username=session.get('username')).first().id).all()
    totalValor = 0
    countImoveis = 0

    for estate in estates:
        if type(estate.price) == str:
            estate.price = int(estate.price.replace(".", "").replace(",", ""))
        totalValor += estate.price
        countImoveis += 1

    # Format each estate price after the loop
    for estate in estates:
        estate.price = "{:,}".format(estate.price)

    totalValor = "{:,}".format(totalValor)

    return render_template(
        "index.html", estates=estates, total=totalValor, nImoveis=countImoveis
    )


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)