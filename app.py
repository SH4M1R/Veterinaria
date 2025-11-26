# =========================================
# happy_pet_project - app.py
# Backend Flask para Happy Pet
# =========================================

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# =========================================
# CONFIGURACIÓN DE FLASK
# =========================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this_secret')

# =========================================
# CONFIGURACIÓN BASE DE DATOS
# =========================================
basedir = os.path.abspath(os.path.dirname(__file__))  # ruta del proyecto
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)

db_path = os.path.join(instance_dir, 'happy_pet.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================================
# EXTENSIONES
# =========================================
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =========================================
# MODELOS
# =========================================
class User(UserMixin, db.Model):
    """Modelo de usuario (admin o invitado/cliente)"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Employee(db.Model):
    """Modelo de empleado del sistema"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    info = db.Column(db.String(200))


class Service(db.Model):
    """Modelo de servicios ofrecidos"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    description = db.Column(db.String(200))


class Reservation(db.Model):
    """Modelo de reservas de citas"""
    id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.String(100))
    owner_email = db.Column(db.String(120))
    pet_type = db.Column(db.String(50))
    pet_name = db.Column(db.String(100))
    pet_size = db.Column(db.String(50))
    pet_weight = db.Column(db.Float)
    pet_gender = db.Column(db.String(20))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service')
    reserved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================
# LOGIN MANAGER
# =========================================
@login_manager.user_loader
def load_user(user_id):
    """Carga de usuario por ID para Flask-Login"""
    return User.query.get(int(user_id))


# =========================================
# INICIALIZACIÓN DE LA BD Y USUARIOS
# =========================================
def inicializar_db():
    """Crea las tablas y usuarios iniciales si no existen"""
    db.create_all()

    # Crear usuarios iniciales: admin y veterinario
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(email='admin@gmail.com', name='Admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)

    vet = User.query.filter_by(email='veterinario@gmail.com').first()
    if not vet:
        vet = User(email='veterinario@gmail.com', name='Veterinario', is_admin=True)
        vet.set_password('veterinario')
        db.session.add(vet)

    db.session.commit()


# =========================================
# RUTAS PÚBLICAS (USUARIOS)
# =========================================

@app.route('/')
def index():
    """Home público con servicios y personal"""
    services = Service.query.all()
    employees = Employee.query.all()
    return render_template('user/home.html', services=services, employees=employees)


@app.route('/login', methods=['GET','POST'])
def login():
    """Login de usuarios (clientes, admin o invitados)"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        flash('Credenciales inválidas','danger')
    return render_template('login.html')


@app.route('/guest', methods=['POST'])
def guest():
    """Acceso como usuario invitado"""
    guest = User.query.filter_by(email='guest@happypet.test').first()
    if not guest:
        guest = User(email='guest@happypet.test', name='Invitado')
        guest.set_password('guest')
        db.session.add(guest)
        db.session.commit()
    login_user(guest)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    logout_user()
    return redirect(url_for('index'))


@app.route('/reservar', methods=['GET','POST'])
def reservar():
    """Formulario para reservar citas de mascotas"""
    services = Service.query.all()
    if request.method == 'POST':
        # Captura de datos del formulario
        pet_type = request.form.get('pet_type')
        pet_name = request.form.get('pet_name')
        pet_size = request.form.get('pet_size')
        pet_weight = float(request.form.get('pet_weight') or 0)
        pet_gender = request.form.get('pet_gender')
        owner_name = request.form.get('owner_name') or (current_user.name if current_user.is_authenticated else 'Invitado')
        owner_email = request.form.get('owner_email') or (current_user.email if current_user.is_authenticated else 'guest@happypet.test')
        service_id = int(request.form.get('service_id') or 1)
        date = request.form.get('date')
        time = request.form.get('time')

        try:
            reserved_at = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        except:
            flash('Formato de fecha u hora inválido','danger')
            return redirect(url_for('reservar'))

        r = Reservation(
            owner_name=owner_name,
            owner_email=owner_email,
            pet_type=pet_type,
            pet_name=pet_name,
            pet_size=pet_size,
            pet_weight=pet_weight,
            pet_gender=pet_gender,
            service_id=service_id,
            reserved_at=reserved_at
        )
        db.session.add(r)
        db.session.commit()

        # Preparar datos para pantalla de confirmación
        day = reserved_at.strftime('%A')
        fecha = reserved_at.strftime('%d %B %Y')
        hora = reserved_at.strftime('%H:%M')

        return render_template('user/confirmacion.html', dia=day, fecha=fecha, hora=hora)
    
    return render_template('user/reservar.html', services=services)


# =========================================
# RUTAS ADMIN
# =========================================

@app.route('/admin')
@login_required
def admin_dashboard():
    """Panel principal del admin"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    total_reservas = Reservation.query.count()
    total_empleados = Employee.query.count()
    total_servicios = Service.query.count()
    return render_template('admin/dashboard.html',
                           total_reservas=total_reservas,
                           total_empleados=total_empleados,
                           total_servicios=total_servicios)


@app.route('/admin/empleados', methods=['GET','POST'])
@login_required
def admin_empleados():
    """CRUD de empleados"""
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        info = request.form.get('info')

        if not name:
            flash('Nombre requerido','danger')
            return redirect(url_for('admin_empleados'))

        e = Employee(name=name, role=role, info=info)
        db.session.add(e)
        db.session.commit()
        flash('Empleado creado','success')
        return redirect(url_for('admin_empleados'))

    empleados = Employee.query.all()
    return render_template('admin/empleados.html', empleados=empleados)


@app.route('/admin/servicios', methods=['GET','POST'])
@login_required
def admin_servicios():
    """CRUD de servicios"""
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price') or 0)
        description = request.form.get('description')

        if not name:
            flash('Nombre requerido','danger')
            return redirect(url_for('admin_servicios'))

        s = Service(name=name, price=price, description=description)
        db.session.add(s)
        db.session.commit()
        flash('Servicio agregado','success')
        return redirect(url_for('admin_servicios'))

    servicios = Service.query.all()
    return render_template('admin/servicios.html', servicios=servicios)


@app.route('/admin/reservas', methods=['GET','POST'])
@login_required
def admin_reservas():
    """CRUD de reservas (editar fecha/hora)"""
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        rid = int(request.form.get('reservation_id'))
        date = request.form.get('date')
        time = request.form.get('time')

        r = Reservation.query.get(rid)
        if r:
            r.reserved_at = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            db.session.commit()
            flash('Reserva actualizada','success')

        return redirect(url_for('admin_reservas'))

    reservations = Reservation.query.order_by(Reservation.reserved_at).all()
    return render_template('admin/reservas.html', reservations=reservations)


# =========================================
# EJECUCIÓN DE LA APP
# =========================================
if __name__ == '__main__':
    with app.app_context():
        inicializar_db()  # Crear tablas y usuarios iniciales
    app.run(debug=True)
