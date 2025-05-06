from flask import Flask, render_template, request, redirect, url_for, send_file, session
from pathlib import Path
from functools import wraps
import os
from openai import OpenAI

# Leer la clave de OpenAI desde el archivo
clave_openai = os.getenv("OPENAI_API_KEY")
if not clave_openai:
    raise Exception("❌ No se encontró la variable de entorno OPENAI_API_KEY.")

# Crear el cliente de OpenAI
client = OpenAI(api_key=clave_openai)


app = Flask(__name__)
app.secret_key = 'clave-secreta-para-sesiones'

# Usuarios válidos
users = {
    "admin": "admin",
    "ent": "ent"
}

# Decorador para proteger rutas
def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

# Login
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"].strip().lower()
        pwd = request.form["password"].strip().lower()
        if users.get(user) == pwd:
            session['usuario'] = user
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Página principal
@app.route('/index')
@login_requerido
def index():
    return render_template("index.html")

# Fichas
@app.route('/fichas')
@login_requerido
def fichas():
    ruta = Path("Material/Fichas")
    archivos = [f for f in os.listdir(ruta) if f.lower().endswith(".pdf")]
    return render_template("fichas.html", archivos=archivos)

# Síntesis validada
@app.route('/sintesis')
@login_requerido
def sintesis():
    ruta = Path("Material/Síntesis Validado")
    archivos = [f for f in os.listdir(ruta) if f.lower().endswith(".pdf")]
    return render_template("sintesis.html", archivos=archivos)

# Ver PDF
@app.route('/ver_pdf/<tipo>/<nombre>')
@login_requerido
def ver_pdf(tipo, nombre):
    ruta = Path(f"Material/{tipo}/{nombre}")
    return send_file(ruta, as_attachment=False)

# Dashboard Excel
@app.route('/dashboard')
@login_requerido
def dashboard():
    ruta_excel = Path("Material/DASHBOARD PPS-PP ENT.xlsx")
    return send_file(ruta_excel, as_attachment=False)

# Asistente interactivo
@app.route('/asistente', methods=["GET", "POST"])
@login_requerido
def asistente():
    if 'chat' not in session:
        session['chat'] = [{"role": "assistant", "content": "Hazme una pregunta."}]

    if request.method == "POST":
        pregunta = request.form["pregunta"]
        chat = session['chat']
        chat.append({"role": "user", "content": pregunta})

        try:
            respuesta_openai = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "Eres un asistente de salud especializado en ENT."}] + chat
            )
            respuesta = respuesta_openai.choices[0].message.content.strip()
            chat.append({"role": "assistant", "content": respuesta})
        except Exception as e:
            chat.append({"role": "assistant", "content": f"[Error: {e}]"})

        session['chat'] = chat

    return render_template("asistente.html", chat=session['chat'])

# Borrar historial del chat
@app.route('/borrar_chat')
@login_requerido
def borrar_chat():
    session.pop('chat', None)
    return redirect(url_for('asistente'))

# Ejecutar app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

