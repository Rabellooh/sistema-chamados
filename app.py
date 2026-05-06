from flask import Flask, render_template, request, redirect, session, send_from_directory
import json, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "segredo"

BASE = os.path.dirname(__file__)

ARQ_CHAMADOS = os.path.join(BASE, "chamados.json")
ARQ_MSG = os.path.join(BASE, "mensagens.json")
ARQ_USERS = os.path.join(BASE, "usuarios.json")
UPLOAD = os.path.join(BASE, "uploads")

os.makedirs(UPLOAD, exist_ok=True)


def load(arq):
    if not os.path.exists(arq):
        return []
    with open(arq, "r") as f:
        return json.load(f)


def save(arq, data):
    with open(arq, "w") as f:
        json.dump(data, f, indent=4)


# LOGIN
@app.before_request
def check():
    if "usuario" not in session and request.endpoint != "login":
        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    usuarios = load(ARQ_USERS)

    if request.method == "POST":
        uid = int(request.form["usuario_id"])
        for u in usuarios:
            if u["id"] == uid:
                session["usuario"] = u
                return redirect("/")

    return render_template("login.html", usuarios=usuarios)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# DASHBOARD
@app.route("/")
def dashboard():
    chamados = load(ARQ_CHAMADOS)

    total = len(chamados)
    abertos = len([c for c in chamados if c["status"] == "aberto"])
    andamento = len([c for c in chamados if c["status"] == "em_andamento"])
    resolvidos = len([c for c in chamados if c["status"] == "resolvido"])

    return render_template("dashboard.html",
                           total=total,
                           abertos=abertos,
                           andamento=andamento,
                           resolvidos=resolvidos,
                           usuario=session["usuario"])


# LISTA
@app.route("/chamados")
def chamados():
    lista = load(ARQ_CHAMADOS)
    user = session["usuario"]

    if user["tipo"] == "colaborador":
        lista = [c for c in lista if c["usuario"] == user["nome"]]

    return render_template("chamados.html", chamados=lista, usuario=user)


# NOVO
@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        chamados = load(ARQ_CHAMADOS)

        chamados.append({
            "id": len(chamados) + 1,
            "usuario": session["usuario"]["nome"],
            "setor": request.form["setor"],
            "maquina": request.form["maquina"],
            "descricao": request.form["descricao"],
            "status": "aberto",
            "tecnicos": []
        })

        save(ARQ_CHAMADOS, chamados)
        return redirect("/chamados")

    return render_template("novo.html")


# DETALHE + CHAT
@app.route("/chamado/<int:id>", methods=["GET", "POST"])
def detalhe(id):
    chamados = load(ARQ_CHAMADOS)
    mensagens = load(ARQ_MSG)
    usuarios = load(ARQ_USERS)

    chamado = next((c for c in chamados if c["id"] == id), None)
    if not chamado:
        return "Chamado não encontrado"

    pasta = os.path.join(UPLOAD, f"chamado_{id}")
    os.makedirs(pasta, exist_ok=True)

    if request.method == "POST":
        texto = request.form.get("mensagem")
        arquivo = request.files.get("arquivo")

        nome_arquivo = None

        if arquivo and arquivo.filename:
            nome = secure_filename(arquivo.filename)
            caminho = os.path.join(pasta, nome)
            arquivo.save(caminho)
            nome_arquivo = f"chamado_{id}/{nome}"

        mensagens.append({
            "chamado_id": id,
            "autor": session["usuario"]["nome"],
            "texto": texto,
            "arquivo": nome_arquivo
        })

        save(ARQ_MSG, mensagens)
        return redirect(f"/chamado/{id}")

    msgs = [m for m in mensagens if m["chamado_id"] == id]

    return render_template("detalhe.html",
                           chamado=chamado,
                           mensagens=msgs,
                           usuario=session["usuario"],
                           usuarios=usuarios)


# ASSUMIR
@app.route("/assumir/<int:id>")
def assumir(id):
    chamados = load(ARQ_CHAMADOS)
    user = session["usuario"]

    if user["tipo"] == "ti":
        for c in chamados:
            if c["id"] == id:
                if user["nome"] not in c["tecnicos"]:
                    c["tecnicos"].append(user["nome"])
                c["status"] = "em_andamento"

    save(ARQ_CHAMADOS, chamados)
    return redirect("/chamados")


# FINALIZAR
@app.route("/finalizar/<int:id>")
def finalizar(id):
    chamados = load(ARQ_CHAMADOS)

    for c in chamados:
        if c["id"] == id:
            c["status"] = "resolvido"

    save(ARQ_CHAMADOS, chamados)
    return redirect("/chamados")


# ADD TECNICO
@app.route("/add_tecnico/<int:id>", methods=["POST"])
def add_tecnico(id):
    chamados = load(ARQ_CHAMADOS)
    nome = request.form.get("tecnico")

    for c in chamados:
        if c["id"] == id:
            if nome and nome not in c["tecnicos"]:
                c["tecnicos"].append(nome)
                c["status"] = "em_andamento"

    save(ARQ_CHAMADOS, chamados)
    return redirect(f"/chamado/{id}")


# REMOVER TECNICO
@app.route("/remover_tecnico/<int:id>/<nome>")
def remover_tecnico(id, nome):
    chamados = load(ARQ_CHAMADOS)

    for c in chamados:
        if c["id"] == id:
            if nome in c["tecnicos"]:
                c["tecnicos"].remove(nome)

    save(ARQ_CHAMADOS, chamados)
    return redirect(f"/chamado/{id}")


# UPLOAD
@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD, filename)


if __name__ == "__main__":
    app.run(debug=True)