from flask import Flask, render_template, request, redirect, session
import json
import os
from collections import Counter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from flask import send_file
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = "123"

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# JSON
# =========================

def carregar_json(arquivo):

    if not os.path.exists(arquivo):

        return []

    with open(arquivo, "r", encoding="utf-8") as f:

        return json.load(f)


def salvar_json(arquivo, dados):

    with open(arquivo, "w", encoding="utf-8") as f:

        json.dump(
            dados,
            f,
            indent=4,
            ensure_ascii=False
        )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    usuarios = carregar_json("usuarios.json")

    if request.method == "POST":

        usuario_id = int(
            request.form["usuario_id"]
        )

        usuario = next(
            (
                u for u in usuarios
                if u["id"] == usuario_id
            ),
            None
        )

        session["usuario"] = usuario

        return redirect("/")

    return render_template(
        "login.html",
        usuarios=usuarios
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    chamados = carregar_json("chamados.json")

    abertos = len(
        [
            c for c in chamados
            if c.get("status") == "aberto"
        ]
    )

    andamento = len(
        [
            c for c in chamados
            if c.get("status") == "em_andamento"
        ]
    )

    resolvidos = len(
        [
            c for c in chamados
            if c.get("status") == "resolvido"
        ]
    )

    ranking_colaborador = Counter(
        [
            c.get("usuario", "Desconhecido")
            for c in chamados
        ]
    )

    ranking_setor = Counter(
        [
            c.get("setor", "Não informado")
            for c in chamados
        ]
    )

    problemas = Counter()

    for c in chamados:

        categoria = c.get(
            "categoria",
            "Não categorizado"
        )

        problemas[categoria] += 1

    if usuario["tipo"] == "ti":

        return render_template(
            "dashboard_ti.html",
            usuario=usuario,
            chamados=chamados,
            abertos=abertos,
            andamento=andamento,
            resolvidos=resolvidos,
            ranking_colaborador=ranking_colaborador,
            ranking_setor=ranking_setor,
            setores_json=json.dumps(
                dict(ranking_setor)
            ),
            problemas_json=json.dumps(
                dict(problemas)
            )
        )

    return render_template(
        "dashboard_colab.html",
        usuario=usuario,
        chamados=chamados,
        abertos=abertos,
        andamento=andamento,
        resolvidos=resolvidos
    )


# =========================
# LISTA CHAMADOS
# =========================

@app.route("/chamados")
def chamados():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    chamados = carregar_json("chamados.json")

    return render_template(
        "chamados.html",
        usuario=usuario,
        chamados=chamados
    )


# =========================
# DETALHE
# =========================

@app.route("/chamado/<int:chamado_id>")
def detalhe_chamado(chamado_id):

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    chamados = carregar_json("chamados.json")

    mensagens = carregar_json("mensagens.json")

    chamado = next(
        (
            c for c in chamados
            if c["id"] == chamado_id
        ),
        None
    )

    mensagens_chamado = [
        m for m in mensagens
        if m["chamado_id"] == chamado_id
    ]

    return render_template(
        "detalhe.html",
        usuario=usuario,
        chamado=chamado,
        mensagens=mensagens_chamado
    )


# =========================
# NOVO CHAMADO
# =========================

@app.route("/novo", methods=["GET", "POST"])
def novo_chamado():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] != "colaborador":

        return redirect("/")

    chamados = carregar_json("chamados.json")

    if request.method == "POST":

        novo_id = 1

        if chamados:

            novo_id = chamados[-1]["id"] + 1

        arquivo_nome = ""

        arquivo = request.files.get("arquivo")

        if arquivo and arquivo.filename != "":

            pasta = os.path.join(
                UPLOAD_FOLDER,
                f"chamado_{novo_id}"
            )

            os.makedirs(
                pasta,
                exist_ok=True
            )

            nome_seguro = secure_filename(
                arquivo.filename
            )

            caminho = os.path.join(
                pasta,
                nome_seguro
            )

            arquivo.save(caminho)

            arquivo_nome = caminho

        chamado = {

            "id": novo_id,

            "usuario": usuario["nome"],

            "setor": request.form["setor"],

            "maquina": request.form["maquina"],

            "descricao": request.form["descricao"],

            "status": "aberto",

            "categoria": "Não categorizado",

            "solucao": "",

            "tecnicos": [],

            "arquivo": arquivo_nome
        }

        chamados.append(chamado)

        salvar_json(
            "chamados.json",
            chamados
        )

        return redirect("/chamados")

    return render_template(
        "novo.html",
        usuario=usuario
    )


# =========================
# CHAT
# =========================

@app.route(
    "/mensagem/<int:chamado_id>",
    methods=["POST"]
)
def enviar_mensagem(chamado_id):

    usuario = session.get("usuario")

    mensagens = carregar_json("mensagens.json")

    texto = request.form["mensagem"]

    arquivo_nome = ""

    arquivo = request.files.get("arquivo")

    if arquivo and arquivo.filename != "":

        pasta = os.path.join(
            UPLOAD_FOLDER,
            f"chat_{chamado_id}"
        )

        os.makedirs(
            pasta,
            exist_ok=True
        )

        nome_seguro = secure_filename(
            arquivo.filename
        )

        caminho = os.path.join(
            pasta,
            nome_seguro
        )

        arquivo.save(caminho)

        arquivo_nome = caminho

    mensagem = {

        "chamado_id": chamado_id,

        "usuario": usuario["nome"],

        "mensagem": texto,

        "arquivo": arquivo_nome
    }

    mensagens.append(mensagem)

    salvar_json(
        "mensagens.json",
        mensagens
    )

    return redirect(
        f"/chamado/{chamado_id}"
    )


# =========================
# CATEGORIA
# =========================

@app.route(
    "/categoria/<int:chamado_id>",
    methods=["POST"]
)
def categoria_chamado(chamado_id):

    chamados = carregar_json("chamados.json")

    for c in chamados:

        if c["id"] == chamado_id:

            c["categoria"] = request.form["categoria"]

    salvar_json(
        "chamados.json",
        chamados
    )

    return redirect(
        f"/chamado/{chamado_id}"
    )


# =========================
# SOLUÇÃO
# =========================

@app.route(
    "/solucao/<int:chamado_id>",
    methods=["POST"]
)
def adicionar_solucao(chamado_id):

    chamados = carregar_json("chamados.json")

    for c in chamados:

        if c["id"] == chamado_id:

            c["solucao"] = request.form["solucao"]

    salvar_json(
        "chamados.json",
        chamados
    )

    return redirect(
        f"/chamado/{chamado_id}"
    )


# =========================
# ASSUMIR
# =========================

@app.route("/assumir/<int:chamado_id>")
def assumir_chamado(chamado_id):

    usuario = session.get("usuario")

    chamados = carregar_json("chamados.json")

    for c in chamados:

        if c["id"] == chamado_id:

            if usuario["nome"] not in c["tecnicos"]:

                c["tecnicos"].append(
                    usuario["nome"]
                )

            c["status"] = "em_andamento"

    salvar_json(
        "chamados.json",
        chamados
    )

    return redirect(
        f"/chamado/{chamado_id}"
    )


# =========================
# FINALIZAR
# =========================

@app.route("/finalizar/<int:chamado_id>")
def finalizar_chamado(chamado_id):

    chamados = carregar_json("chamados.json")

    for c in chamados:

        if c["id"] == chamado_id:

            c["status"] = "resolvido"

    salvar_json(
        "chamados.json",
        chamados
    )

    return redirect(
        f"/chamado/{chamado_id}"
    )


# =========================
# EXCLUIR
# =========================

@app.route(
    "/excluir/<int:chamado_id>",
    methods=["GET", "POST"]
)
def excluir_chamado(chamado_id):

    chamados = carregar_json("chamados.json")

    chamado = next(
        (
            c for c in chamados
            if c["id"] == chamado_id
        ),
        None
    )

    if request.method == "POST":

        chamados = [
            c for c in chamados
            if c["id"] != chamado_id
        ]

        salvar_json(
            "chamados.json",
            chamados
        )

        return redirect("/chamados")

    return render_template(
        "confirmar_exclusao.html",
        chamado=chamado
    )
# =========================
# HISTÓRICO
# =========================

@app.route("/historico")
def historico():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    chamados = carregar_json(
        "chamados.json"
    )

    busca = request.args.get(
        "busca",
        ""
    ).lower()

    resultados = []

    tecnicos = set()

    maquinas = set()

    if busca:

        resultados = [

            c for c in chamados

            if

            busca in c.get(
                "maquina",
                ""
            ).lower()

            or

            busca in c.get(
                "usuario",
                ""
            ).lower()

        ]

        for c in resultados:

            maquinas.add(
                c.get("maquina", "")
            )

            for t in c.get(
                "tecnicos",
                []
            ):

                tecnicos.add(t)

    return render_template(

        "historico.html",

        usuario=usuario,

        resultados=resultados,

        busca=busca,

        tecnicos=tecnicos,

        maquinas=maquinas
    )


# =========================
# EXPORTAR PDF
# =========================

@app.route("/exportar/pdf")
def exportar_pdf():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    chamados = carregar_json(
        "chamados.json"
    )

    tecnico = request.args.get(
        "tecnico"
    )

    if tecnico:

        chamados = [

            c for c in chamados

            if tecnico in c.get(
                "tecnicos",
                []
            )

        ]

    arquivo = "relatorio_chamados.pdf"

    doc = SimpleDocTemplate(
        arquivo
    )

    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(

        Paragraph(

            "Relatório de Chamados",

            styles["Title"]

        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    for c in chamados:

        texto = f"""

        <b>ID:</b> {c.get('id')}<br/>

        <b>Colaborador:</b> {c.get('usuario')}<br/>

        <b>Setor:</b> {c.get('setor')}<br/>

        <b>Máquina:</b> {c.get('maquina')}<br/>

        <b>Status:</b> {c.get('status')}<br/>

        <b>Categoria:</b> {c.get('categoria')}<br/>

        <b>Técnicos:</b> {', '.join(c.get('tecnicos', []))}<br/>

        <b>Solução:</b> {c.get('solucao', '')}<br/><br/>

        """

        elementos.append(

            Paragraph(

                texto,

                styles["BodyText"]

            )
        )

        elementos.append(
            Spacer(1, 12)
        )

    doc.build(elementos)

    return send_file(
        arquivo,
        as_attachment=True
    )


# =========================
# EXPORTAR XLSX
# =========================

@app.route("/exportar/xlsx")
def exportar_xlsx():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    chamados = carregar_json(
        "chamados.json"
    )

    tecnico = request.args.get(
        "tecnico"
    )

    if tecnico:

        chamados = [

            c for c in chamados

            if tecnico in c.get(
                "tecnicos",
                []
            )

        ]

    wb = Workbook()

    ws = wb.active

    ws.title = "Chamados"

    headers = [

        "ID",
        "Colaborador",
        "Setor",
        "Máquina",
        "Status",
        "Categoria",
        "Técnicos",
        "Solução"

    ]

    ws.append(headers)

    for c in chamados:

        ws.append([

            c.get("id"),
            c.get("usuario"),
            c.get("setor"),
            c.get("maquina"),
            c.get("status"),
            c.get("categoria"),
            ", ".join(
                c.get(
                    "tecnicos",
                    []
                )
            ),
            c.get(
                "solucao",
                ""
            )

        ])

    arquivo = "relatorio_chamados.xlsx"

    wb.save(arquivo)

    return send_file(
        arquivo,
        as_attachment=True
    )

# =========================
# EDITAR CHAMADO (TI)
# =========================

@app.route("/editar_chamado/<int:id>", methods=["POST"])
def editar_chamado(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    chamados = carregar_json(
        "chamados.json"
    )

    for c in chamados:

        if c["id"] == id:

            c["setor"] = request.form.get(
                "setor",
                c.get("setor", "")
            )

            c["maquina"] = request.form.get(
                "maquina",
                c.get("maquina", "")
            )

            c["categoria"] = request.form.get(
                "categoria",
                c.get("categoria", "")
            )

            c["solucao"] = request.form.get(
                "solucao",
                c.get("solucao", "")
            )

            salvar_json(
                "chamados.json",
                chamados
            )

            break

    return redirect(
        f"/chamado/{id}"
    )

# =========================
# EXECUTAR
# =========================

if __name__ == "__main__":

    app.run(debug=True)