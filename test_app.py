import unittest
from app import app, db, Producto


class BaseTestCase(unittest.TestCase):
    """Configuración base: BD en memoria, se crea y destruye por cada test."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # ------------------------------------------------------------------ helpers
    def _crear_producto(self, nombre='Laptop', precio=999.99, stock=10,
                        descripcion='Descripción', categoria='Electrónica'):
        with app.app_context():
            p = Producto(nombre=nombre, precio=precio, stock=stock,
                         descripcion=descripcion, categoria=categoria)
            db.session.add(p)
            db.session.commit()
            return p.id


# ======================================================================
# Modelo
# ======================================================================
class TestModeloProducto(BaseTestCase):

    def test_crear_producto_minimo(self):
        """Un producto se persiste con los campos obligatorios."""
        with app.app_context():
            p = Producto(nombre='Mouse', precio=25.0, stock=5)
            db.session.add(p)
            db.session.commit()
            guardado = db.session.get(Producto, p.id)
            self.assertEqual(guardado.nombre, 'Mouse')
            self.assertEqual(guardado.precio, 25.0)
            self.assertEqual(guardado.stock, 5)
            self.assertIsNone(guardado.descripcion)
            self.assertIsNone(guardado.categoria)

    def test_crear_producto_completo(self):
        """Un producto se persiste con todos los campos."""
        with app.app_context():
            p = Producto(nombre='Teclado', precio=50.0, stock=20,
                         descripcion='Teclado mecánico', categoria='Periféricos')
            db.session.add(p)
            db.session.commit()
            guardado = db.session.get(Producto, p.id)
            self.assertEqual(guardado.descripcion, 'Teclado mecánico')
            self.assertEqual(guardado.categoria, 'Periféricos')

    def test_repr(self):
        """__repr__ devuelve el formato esperado."""
        with app.app_context():
            p = Producto(nombre='Monitor', precio=300.0, stock=3)
            self.assertIn('Monitor', repr(p))

    def test_fecha_creacion_automatica(self):
        """fecha_creacion se asigna automáticamente."""
        with app.app_context():
            p = Producto(nombre='Webcam', precio=80.0, stock=7)
            db.session.add(p)
            db.session.commit()
            self.assertIsNotNone(p.fecha_creacion)


# ======================================================================
# READ — Listar productos (GET /)
# ======================================================================
class TestListarProductos(BaseTestCase):

    def test_lista_vacia(self):
        """La página principal responde 200 sin productos."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'No hay productos', resp.data)

    def test_lista_con_productos(self):
        """Los productos creados aparecen en la lista."""
        self._crear_producto(nombre='Impresora', precio=199.0)
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Impresora', resp.data)

    def test_busqueda_por_nombre(self):
        """La búsqueda filtra por nombre."""
        self._crear_producto(nombre='Monitor 4K', precio=500.0)
        self._crear_producto(nombre='Auriculares', precio=80.0)
        resp = self.client.get('/?q=monitor')
        self.assertIn(b'Monitor 4K', resp.data)
        self.assertNotIn(b'Auriculares', resp.data)

    def test_busqueda_por_categoria(self):
        """La búsqueda filtra por categoría."""
        self._crear_producto(nombre='Silla', precio=150.0, categoria='Mobiliario')
        self._crear_producto(nombre='Switch', precio=90.0, categoria='Redes')
        resp = self.client.get('/?q=mobiliario')
        self.assertIn(b'Silla', resp.data)
        self.assertNotIn(b'Switch', resp.data)

    def test_busqueda_sin_resultados(self):
        """Búsqueda sin coincidencias muestra mensaje adecuado."""
        resp = self.client.get('/?q=xyzinexistente')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'xyzinexistente', resp.data)


# ======================================================================
# READ — Detalle (GET /producto/<id>)
# ======================================================================
class TestDetalleProducto(BaseTestCase):

    def test_detalle_existente(self):
        """GET /producto/<id> devuelve 200 con los datos del producto."""
        pid = self._crear_producto(nombre='Router', precio=75.0)
        resp = self.client.get(f'/producto/{pid}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Router', resp.data)

    def test_detalle_no_existente(self):
        """GET /producto/999 devuelve 404."""
        resp = self.client.get('/producto/999')
        self.assertEqual(resp.status_code, 404)


# ======================================================================
# CREATE (GET + POST /nuevo)
# ======================================================================
class TestCrearProducto(BaseTestCase):

    def test_formulario_crear_get(self):
        """GET /nuevo devuelve 200 con el formulario."""
        resp = self.client.get('/nuevo')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Crear', resp.data)

    def test_crear_producto_valido(self):
        """POST /nuevo con datos válidos crea el producto y redirige."""
        resp = self.client.post('/nuevo', data={
            'nombre': 'Disco SSD',
            'descripcion': '1TB NVMe',
            'precio': '120.50',
            'stock': '15',
            'categoria': 'Almacenamiento'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Disco SSD', resp.data)
        with app.app_context():
            self.assertEqual(Producto.query.count(), 1)

    def test_crear_producto_sin_nombre(self):
        """POST /nuevo sin nombre muestra error de validación."""
        resp = self.client.post('/nuevo', data={
            'nombre': '',
            'precio': '50.0',
            'stock': '5'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'obligatorio', resp.data)
        with app.app_context():
            self.assertEqual(Producto.query.count(), 0)

    def test_crear_producto_sin_precio(self):
        """POST /nuevo sin precio muestra error de validación."""
        resp = self.client.post('/nuevo', data={
            'nombre': 'Producto X',
            'precio': '',
            'stock': '5'
        }, follow_redirects=True)
        self.assertIn(b'obligatorio', resp.data)
        with app.app_context():
            self.assertEqual(Producto.query.count(), 0)

    def test_crear_producto_precio_invalido(self):
        """POST /nuevo con precio no numérico muestra error."""
        resp = self.client.post('/nuevo', data={
            'nombre': 'Producto Y',
            'precio': 'abc',
            'stock': '5'
        }, follow_redirects=True)
        self.assertIn('número válido'.encode(), resp.data)

    def test_crear_producto_precio_negativo(self):
        """POST /nuevo con precio negativo muestra error."""
        resp = self.client.post('/nuevo', data={
            'nombre': 'Producto Z',
            'precio': '-10',
            'stock': '5'
        }, follow_redirects=True)
        self.assertIn(b'negativo', resp.data)

    def test_crear_producto_stock_invalido(self):
        """POST /nuevo con stock no entero muestra error."""
        resp = self.client.post('/nuevo', data={
            'nombre': 'Producto W',
            'precio': '30',
            'stock': 'mucho'
        }, follow_redirects=True)
        self.assertIn('entero'.encode(), resp.data)


# ======================================================================
# UPDATE (GET + POST /editar/<id>)
# ======================================================================
class TestEditarProducto(BaseTestCase):

    def test_formulario_editar_get(self):
        """GET /editar/<id> devuelve 200 con los datos precargados."""
        pid = self._crear_producto(nombre='Cable HDMI', precio=15.0)
        resp = self.client.get(f'/editar/{pid}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Cable HDMI', resp.data)

    def test_editar_no_existente(self):
        """GET /editar/999 devuelve 404."""
        resp = self.client.get('/editar/999')
        self.assertEqual(resp.status_code, 404)

    def test_editar_producto_valido(self):
        """POST /editar/<id> actualiza los datos del producto."""
        pid = self._crear_producto(nombre='Pantalla', precio=300.0, stock=5)
        resp = self.client.post(f'/editar/{pid}', data={
            'nombre': 'Pantalla Curva',
            'descripcion': '27 pulgadas',
            'precio': '350.00',
            'stock': '8',
            'categoria': 'Monitores'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Pantalla Curva', resp.data)
        with app.app_context():
            p = db.session.get(Producto, pid)
            self.assertEqual(p.nombre, 'Pantalla Curva')
            self.assertEqual(p.precio, 350.0)
            self.assertEqual(p.stock, 8)

    def test_editar_sin_nombre(self):
        """POST /editar/<id> sin nombre muestra error y no actualiza."""
        pid = self._crear_producto(nombre='Hub USB', precio=20.0)
        self.client.post(f'/editar/{pid}', data={
            'nombre': '',
            'precio': '20.0',
            'stock': '3'
        }, follow_redirects=True)
        with app.app_context():
            p = db.session.get(Producto, pid)
            self.assertEqual(p.nombre, 'Hub USB')

    def test_editar_precio_negativo(self):
        """POST /editar/<id> con precio negativo muestra error y no actualiza."""
        pid = self._crear_producto(nombre='Adaptador', precio=10.0)
        resp = self.client.post(f'/editar/{pid}', data={
            'nombre': 'Adaptador',
            'precio': '-5',
            'stock': '2'
        }, follow_redirects=True)
        self.assertIn(b'negativo', resp.data)
        with app.app_context():
            p = db.session.get(Producto, pid)
            self.assertEqual(p.precio, 10.0)


# ======================================================================
# DELETE (POST /eliminar/<id>)
# ======================================================================
class TestEliminarProducto(BaseTestCase):

    def test_eliminar_existente(self):
        """POST /eliminar/<id> borra el producto y redirige."""
        pid = self._crear_producto(nombre='Pendrive', precio=12.0)
        resp = self.client.post(f'/eliminar/{pid}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with app.app_context():
            self.assertIsNone(db.session.get(Producto, pid))

    def test_eliminar_muestra_confirmacion(self):
        """Tras eliminar aparece mensaje flash con el nombre del producto."""
        pid = self._crear_producto(nombre='Pendrive Pro', precio=20.0)
        resp = self.client.post(f'/eliminar/{pid}', follow_redirects=True)
        self.assertIn(b'Pendrive Pro', resp.data)

    def test_eliminar_no_existente(self):
        """POST /eliminar/999 devuelve 404."""
        resp = self.client.post('/eliminar/999')
        self.assertEqual(resp.status_code, 404)

    def test_eliminar_no_afecta_otros(self):
        """Eliminar un producto no borra los demás."""
        pid1 = self._crear_producto(nombre='Producto A', precio=10.0)
        pid2 = self._crear_producto(nombre='Producto B', precio=20.0)
        self.client.post(f'/eliminar/{pid1}')
        with app.app_context():
            self.assertIsNotNone(db.session.get(Producto, pid2))


if __name__ == '__main__':
    unittest.main(verbosity=2)
