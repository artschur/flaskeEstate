from flask import Flask, render_template, request, redirect, jsonify, json
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///estates.db"
db = SQLAlchemy(app)
UPLOAD_FOLDER = "static/images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

migrate = Migrate(app, db)


class Estate(db.Model):
    ownerId = db.Column(db.Integer)
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False)
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

@app.route('/api/<id>')
def getIdRest(id):
        imovel = Estate.query.get(id)
        try:
            return jsonify(estate_schema.dump(imovel))
        except:
            return 'erro'

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
                ownerId=1,
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
            return redirect("/")
    else:
        return render_template("add.html", title="Add Estate")


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


@app.route("/<id>", methods=["GET"])
def show(id):
    try:
        imovel = Estate.query.get(id)
        imovel.price = "{:,}".format(imovel.price)

    except:
        return "erro ao encontrar imóvel"
    return render_template("singleEstate.html", estate=imovel)


@app.route("/", methods=["GET"])
def index():
    estates = Estate.query.all()
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
    app.run(debug=True)