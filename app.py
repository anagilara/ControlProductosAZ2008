from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'az2008-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Producto {self.nombre}>'


with app.app_context():
    db.create_all()


# READ - Listar todos los productos
@app.route('/')
def index():
    busqueda = request.args.get('q', '')
    if busqueda:
        productos = Producto.query.filter(
            Producto.nombre.ilike(f'%{busqueda}%') |
            Producto.categoria.ilike(f'%{busqueda}%')
        ).all()
    else:
        productos = Producto.query.order_by(Producto.fecha_creacion.desc()).all()
    return render_template('index.html', productos=productos, busqueda=busqueda)


# READ - Ver detalle de un producto
@app.route('/producto/<int:id>')
def detalle(id):
    producto = db.get_or_404(Producto, id)
    return render_template('detalle.html', producto=producto)


# CREATE - Formulario nuevo producto
@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio_str = request.form.get('precio', '').strip()
        stock_str = request.form.get('stock', '0').strip()
        categoria = request.form.get('categoria', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        if not precio_str:
            errores.append('El precio es obligatorio.')
        else:
            try:
                precio = float(precio_str)
                if precio < 0:
                    errores.append('El precio no puede ser negativo.')
            except ValueError:
                errores.append('El precio debe ser un número válido.')
                precio = None
        try:
            stock = int(stock_str)
            if stock < 0:
                errores.append('El stock no puede ser negativo.')
        except ValueError:
            errores.append('El stock debe ser un número entero.')
            stock = 0

        if errores:
            for e in errores:
                flash(e, 'danger')
            return render_template('form.html', accion='Crear', producto=None)

        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categoria
        )
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado exitosamente.', 'success')
        return redirect(url_for('index'))

    return render_template('form.html', accion='Crear', producto=None)


# UPDATE - Editar producto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    producto = db.get_or_404(Producto, id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio_str = request.form.get('precio', '').strip()
        stock_str = request.form.get('stock', '0').strip()
        categoria = request.form.get('categoria', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        if not precio_str:
            errores.append('El precio es obligatorio.')
        else:
            try:
                precio = float(precio_str)
                if precio < 0:
                    errores.append('El precio no puede ser negativo.')
            except ValueError:
                errores.append('El precio debe ser un número válido.')
                precio = None
        try:
            stock = int(stock_str)
            if stock < 0:
                errores.append('El stock no puede ser negativo.')
        except ValueError:
            errores.append('El stock debe ser un número entero.')
            stock = producto.stock

        if errores:
            for e in errores:
                flash(e, 'danger')
            return render_template('form.html', accion='Editar', producto=producto)

        producto.nombre = nombre
        producto.descripcion = descripcion
        producto.precio = precio
        producto.stock = stock
        producto.categoria = categoria
        db.session.commit()
        flash('Producto actualizado exitosamente.', 'success')
        return redirect(url_for('index'))

    return render_template('form.html', accion='Editar', producto=producto)


# DELETE - Eliminar producto
@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    producto = db.get_or_404(Producto, id)
    db.session.delete(producto)
    db.session.commit()
    flash(f'Producto "{producto.nombre}" eliminado.', 'warning')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
