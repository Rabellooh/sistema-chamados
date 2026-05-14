from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, send_from_directory
import os
import io
import json
from collections import Counter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash




app = Flask(__name__)


app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev_secret_key"
)

# =========================
# CONFIG POSTGRESQL
# =========================

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.secret_key = os.getenv("SECRET_KEY")
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )
# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        nome = request.form.get("nome")

        senha = request.form.get("senha")

        resultado = db.session.execute(

            db.text("""

                SELECT *

                FROM usuarios

                WHERE nome = :nome
                AND ativo = true

            """),

            {
                "nome": nome
            }

        ).fetchone()

        if resultado and resultado.senha == senha:

            session["usuario"] = {

                "id": resultado.id,

                "nome": resultado.nome,

                "tipo": resultado.tipo,

                "setor": resultado.setor

            }

            return redirect("/")

        erro = "Usuário ou senha inválidos"

    return render_template(

        "login.html",

        erro=erro if 'erro' in locals()
        else None

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

    chamados = db.session.execute(text("""

        SELECT *
        FROM chamados
        ORDER BY id DESC

    """)).fetchall()

    abertos = len([
        c for c in chamados
        if c.status == "aberto"
    ])

    andamento = len([
        c for c in chamados
        if c.status == "em_andamento"
    ])

    resolvidos = len([
        c for c in chamados
        if c.status == "resolvido"
    ])

    ranking_colaborador = Counter([
        c.usuario or "Desconhecido"
        for c in chamados
    ])

    ranking_setor = Counter([
        c.setor or "Não informado"
        for c in chamados
    ])

    problemas = Counter()

    for c in chamados:

        categoria = (
            c.categoria
            or
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

    busca = request.args.get(
        "busca",
        ""
    ).lower()

    if usuario["tipo"] == "ti":

        query = """

            SELECT *

            FROM chamados

            ORDER BY id DESC

        """

        lista = db.session.execute(
            db.text(query)
        ).fetchall()

    else:

        query = """

            SELECT *

            FROM chamados

            WHERE usuario = :usuario

            ORDER BY id DESC

        """

        lista = db.session.execute(

            db.text(query),

            {
                "usuario": usuario["nome"]
            }

        ).fetchall()

    if busca:

        lista = [

            c for c in lista

            if

            busca in str(c.id).lower()

            or

            busca in str(c.descricao).lower()

            or

            busca in str(c.usuario).lower()

            or

            busca in str(c.maquina).lower()

        ]

    return render_template(

        "chamados.html",

        chamados=lista,

        usuario=usuario,

        busca=busca

    )

# =========================
# DETALHE
# =========================

@app.route("/chamado/<int:id>")
def detalhe_chamado(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    chamado = db.session.execute(

        db.text("""

            SELECT *

            FROM chamados

            WHERE id = :id

        """),

        {
            "id": id
        }

    ).fetchone()

    if not chamado:
        return redirect("/chamados")

    if (

        usuario["tipo"] != "ti"

        and

        chamado.usuario != usuario["nome"]

    ):

        return redirect("/chamados")

    mensagens = db.session.execute(

        db.text("""

            SELECT *

            FROM mensagens

            WHERE chamado_id = :id

            ORDER BY id ASC

        """),

        {
            "id": id
        }

    ).fetchall()

    tecnicos_db = db.session.execute(

        db.text("""

            SELECT tecnico

            FROM chamados_tecnicos

            WHERE chamado_id = :id

        """),

        {
            "id": id
        }

    ).fetchall()

    tecnicos = [

        t.tecnico

        for t in tecnicos_db

    ]

    return render_template(

        "detalhe.html",

        chamado=chamado,

        mensagens=mensagens,

        tecnicos=tecnicos,

        usuario=usuario

    )
# =========================
# NOVO CHAMADO
# =========================

@app.route(
    "/novo",
    methods=["GET", "POST"]
)
def novo_chamado():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "colaborador",
        "administracao",
    ]:
        return redirect("/")

    if request.method == "POST":

        db.session.execute(

            db.text("""

                INSERT INTO chamados (

                    usuario,
                    descricao,
                    setor,
                    maquina,
                    status,
                    categoria,
                    solucao

                )

                VALUES (

                    :usuario,
                    :descricao,
                    :setor,
                    :maquina,
                    'aberto',
                    '',
                    ''

                )

            """),

            {

                "usuario": usuario["nome"],

                "descricao": request.form.get(
                    "descricao",
                    ""
                ),

                "setor": request.form.get(
                    "setor",
                    ""
                ),

                "maquina": request.form.get(
                    "maquina",
                    ""
                )

            }

        )

        db.session.commit()

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

    if not usuario:
        return redirect("/login")

    texto = request.form.get(
        "mensagem",
        ""
    )

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

        arquivo_nome = (
            f"chat_{chamado_id}/{nome_seguro}"
        )

    db.session.execute(

        db.text("""

            INSERT INTO mensagens (

                chamado_id,
                usuario,
                mensagem,
                arquivo

            )

            VALUES (

                :chamado_id,
                :usuario,
                :mensagem,
                :arquivo

            )

        """),

        {

            "chamado_id": chamado_id,

            "usuario": usuario["nome"],

            "mensagem": texto,

            "arquivo": arquivo_nome

        }

    )

    db.session.commit()

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

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    categoria = request.form.get(
        "categoria",
        ""
    )

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET categoria = :categoria

            WHERE id = :id

        """),

        {

            "categoria": categoria,

            "id": chamado_id

        }

    )

    db.session.commit()

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

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    solucao = request.form.get(
        "solucao",
        ""
    )

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET solucao = :solucao

            WHERE id = :id

        """),

        {

            "solucao": solucao,

            "id": chamado_id

        }

    )

    db.session.commit()

    return redirect(
        f"/chamado/{chamado_id}"
    )
# =========================
# ASSUMIR
# =========================

@app.route("/assumir/<int:chamado_id>")
def assumir_chamado(chamado_id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    existe = db.session.execute(

        db.text("""

            SELECT *

            FROM chamados_tecnicos

            WHERE chamado_id = :id
            AND tecnico = :tecnico

        """),

        {
            "id": chamado_id,
            "tecnico": usuario["nome"]
        }

    ).fetchone()

    if not existe:

        db.session.execute(

            db.text("""

                INSERT INTO chamados_tecnicos (

                    chamado_id,
                    tecnico

                )

                VALUES (

                    :id,
                    :tecnico

                )

            """),

            {
                "id": chamado_id,
                "tecnico": usuario["nome"]
            }

        )

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET status = 'em_andamento'

            WHERE id = :id

        """),

        {
            "id": chamado_id
        }

    )

    db.session.commit()

    return redirect(f"/chamado/{chamado_id}")
# =========================
# FINALIZAR CHAMADO
# =========================

@app.route("/finalizar/<int:id>")
def finalizar(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET status = 'resolvido'

            WHERE id = :id

        """),

        {
            "id": id
        }

    )

    db.session.commit()

    return redirect("/chamados")

# =========================
# EXCLUIR
# =========================

@app.route(
    "/excluir/<int:chamado_id>",
    methods=["GET", "POST"]
)
def excluir_chamado(chamado_id):

    chamado = db.session.execute(text("""

        SELECT *
        FROM chamados
        WHERE id = :id

    """), {
        "id": chamado_id
    }).fetchone()

    if not chamado:
        return redirect("/chamados")

    if request.method == "POST":

        db.session.execute(text("""

            DELETE FROM chamados
            WHERE id = :id

        """), {
            "id": chamado_id
        })

        db.session.commit()

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

    busca = request.args.get(
        "busca",
        ""
    ).lower()

    resultados = []

    tecnicos = set()

    maquinas = set()

    if busca:

        resultados = db.session.execute(

            text("""

                SELECT *

                FROM chamados

                WHERE

                    LOWER(maquina) LIKE :busca

                    OR

                    LOWER(usuario) LIKE :busca

                ORDER BY id DESC

            """),

            {
                "busca": f"%{busca}%"
            }

        ).fetchall()

        for c in resultados:

            maquinas.add(c.maquina)

            tecnicos_db = db.session.execute(

                text("""

                    SELECT tecnico

                    FROM chamados_tecnicos

                    WHERE chamado_id = :id

                """),

                {
                    "id": c.id
                }

            ).fetchall()

            for t in tecnicos_db:

                tecnicos.add(t.tecnico)

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

    chamados = db.session.execute(

        text("""

            SELECT *

            FROM chamados

            ORDER BY id DESC

        """)

    ).fetchall()

    tecnico = request.args.get(
        "tecnico"
    )

    if tecnico:

        chamados_filtrados = []

        for c in chamados:

            tecnicos_db = db.session.execute(

                text("""

                    SELECT tecnico

                    FROM chamados_tecnicos

                    WHERE chamado_id = :id

                """),

                {
                    "id": c.id
                }

            ).fetchall()

            tecnicos = [

                t.tecnico

                for t in tecnicos_db

            ]

            if tecnico in tecnicos:

                chamados_filtrados.append(c)

        chamados = chamados_filtrados

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

        tecnicos_db = db.session.execute(

            text("""

                SELECT tecnico

                FROM chamados_tecnicos

                WHERE chamado_id = :id

            """),

            {
                "id": c.id
            }

        ).fetchall()

        tecnicos = [

            t.tecnico

            for t in tecnicos_db

        ]

        texto = f"""

        <b>ID:</b> {c.id}<br/>

        <b>Colaborador:</b> {c.usuario}<br/>

        <b>Setor:</b> {c.setor}<br/>

        <b>Máquina:</b> {c.maquina}<br/>

        <b>Status:</b> {c.status}<br/>

        <b>Categoria:</b> {c.categoria}<br/>

        <b>Técnicos:</b> {', '.join(tecnicos)}<br/>

        <b>Solução:</b> {c.solucao or ''}<br/><br/>

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

    chamados = db.session.execute(

        text("""

            SELECT *

            FROM chamados

            ORDER BY id DESC

        """)

    ).fetchall()

    tecnico = request.args.get(
        "tecnico"
    )

    if tecnico:

        chamados_filtrados = []

        for c in chamados:

            tecnicos_db = db.session.execute(

                text("""

                    SELECT tecnico

                    FROM chamados_tecnicos

                    WHERE chamado_id = :id

                """),

                {
                    "id": c.id
                }

            ).fetchall()

            tecnicos = [

                t.tecnico

                for t in tecnicos_db

            ]

            if tecnico in tecnicos:

                chamados_filtrados.append(c)

        chamados = chamados_filtrados

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

        tecnicos_db = db.session.execute(

            text("""

                SELECT tecnico

                FROM chamados_tecnicos

                WHERE chamado_id = :id

            """),

            {
                "id": c.id
            }

        ).fetchall()

        tecnicos = [

            t.tecnico

            for t in tecnicos_db

        ]

        ws.append([

            c.id,
            c.usuario,
            c.setor,
            c.maquina,
            c.status,
            c.categoria,
            ", ".join(tecnicos),
            c.solucao or ""

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

    db.session.execute(text("""

        UPDATE chamados

        SET

            setor = :setor,
            maquina = :maquina,
            categoria = :categoria,
            solucao = :solucao

        WHERE id = :id

    """), {

        "setor": request.form.get("setor"),
        "maquina": request.form.get("maquina"),
        "categoria": request.form.get("categoria"),
        "solucao": request.form.get("solucao"),
        "id": id

    })

    db.session.commit()

    return redirect(
        f"/chamado/{id}"
    )
# =========================
# REABRIR CHAMADO
# =========================

@app.route("/reabrir/<int:id>")
def reabrir(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET status = 'em_andamento'

            WHERE id = :id

        """),

        {
            "id": id
        }

    )

    db.session.commit()

    return redirect("/chamados")
# =========================
# EXECUTAR
# =========================
# =========================
# INVENTÁRIO
# =========================

@app.route("/inventario")
def inventario():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    ativos = db.session.execute(

        db.text("""

            SELECT *

            FROM ativos

            ORDER BY id DESC

        """)

    ).fetchall()

    return render_template(

        "inventario.html",

        ativos=ativos,

        usuario=usuario
    )
# =========================
# USUÁRIOS
# =========================

@app.route("/usuarios")
def usuarios():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    busca = request.args.get(
        "busca",
        ""
    ).strip()

    if busca:

        usuarios_db = db.session.execute(

            db.text("""

                SELECT *

                FROM usuarios

                WHERE

                    CAST(id AS TEXT)
                    LIKE :busca

                    OR

                    LOWER(nome)
                    LIKE LOWER(:busca)

                ORDER BY id ASC

            """),

            {
                "busca": f"%{busca}%"
            }

        ).fetchall()

    else:

        usuarios_db = db.session.execute(

            db.text("""

                SELECT *

                FROM usuarios

                ORDER BY id ASC

            """)

        ).fetchall()

    return render_template(

        "usuarios.html",

        usuarios=usuarios_db,

        usuario=usuario,

        busca=busca

    )
# =========================
# NOVO USUÁRIO
# =========================

@app.route(
    "/novo_usuario",
    methods=["GET", "POST"]
)
def novo_usuario():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    if request.method == "POST":

        dados = {

            "id": request.form.get("id"),

            "nome": request.form.get("nome"),

            "senha": generate_password_hash(
                request.form.get("senha")
            ),

            "tipo": request.form.get("tipo"),

            "setor": request.form.get("setor"),

            "email": request.form.get("email"),

            "ativo": True

        }

        existe = db.session.execute(

            db.text("""

                SELECT id

                FROM usuarios

                WHERE id = :id

                OR nome = :nome

            """),

            {
                "id": dados["id"],
                "nome": dados["nome"]
            }

        ).fetchone()

        if existe:

            flash(
                "Usuário já existe.",
                "danger"
            )

            return redirect("/novo_usuario")

        db.session.execute(

            db.text("""

                INSERT INTO usuarios (

                    id,
                    nome,
                    senha,
                    tipo,
                    setor,
                    email,
                    ativo

                )

                VALUES (

                    :id,
                    :nome,
                    :senha,
                    :tipo,
                    :setor,
                    :email,
                    :ativo

                )

            """),

            dados

        )

        db.session.commit()

        flash(
            "Usuário criado com sucesso!",
            "success"
        )

        return redirect("/usuarios")

    return render_template(
        "novo_usuario.html",
        usuario=usuario
    )

# =========================
# IMPORTAR USUÁRIOS XLSX
# =========================

@app.route(
    "/importar_usuarios",
    methods=["POST"]
)
def importar_usuarios():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    arquivo = request.files.get("arquivo")

    if not arquivo:

        flash(
            "Nenhum arquivo enviado.",
            "error"
        )

        return redirect("/usuarios")

    try:

        df = pd.read_excel(arquivo)

        for _, linha in df.iterrows():

            existe = db.session.execute(

                db.text("""

                    SELECT id

                    FROM usuarios

                    WHERE id = :id

                """),

                {
                    "id": int(linha["id"])
                }

            ).fetchone()

            if existe:
                continue

            senha_hash = generate_password_hash(
                str(linha["senha"])
            )

            db.session.execute(

                db.text("""

                    INSERT INTO usuarios (

                        id,
                        nome,
                        senha,
                        tipo,
                        setor,
                        email,
                        ativo

                    )

                    VALUES (

                        :id,
                        :nome,
                        :senha,
                        :tipo,
                        :setor,
                        :email,
                        true

                    )

                """),

                {

                    "id": int(linha["id"]),

                    "nome": str(linha["nome"]),

                    "senha": senha_hash,

                    "tipo": str(linha["tipo"]),

                    "setor": str(linha["setor"]),

                    "email": str(linha["email"])

                }

            )

        db.session.commit()

        flash(
            "Usuários importados com sucesso!",
            "success"
        )

    except Exception as e:

        flash(
            f"Erro ao importar planilha: {e}",
            "error"
        )

    return redirect("/usuarios")
# =========================
# EDITAR USUÁRIO
# =========================

@app.route(
    "/editar_usuario/<int:id>",
    methods=["GET", "POST"]
)
def editar_usuario(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    usuario_db = db.session.execute(

        db.text("""

            SELECT *

            FROM usuarios

            WHERE id = :id

        """),

        {
            "id": id
        }

    ).fetchone()

    if not usuario_db:
        return redirect("/usuarios")

    if request.method == "POST":

        db.session.execute(

            db.text("""

                UPDATE usuarios

                SET

                    nome = :nome,
                    senha = :senha,
                    tipo = :tipo,
                    setor = :setor,
                    email = :email,
                    ativo = :ativo

                WHERE id = :id

            """),

            {

                "id": id,

                "nome": request.form.get("nome"),

                "senha": generate_password_hash(
                    request.form.get("senha")
                ),

                "tipo": request.form.get("tipo"),

                "setor": request.form.get("setor"),

                "email": request.form.get("email"),

                "ativo":
                True if request.form.get("ativo")
                == "true"
                else False

            }

        )

        db.session.commit()

        flash(
            "Usuário atualizado com sucesso!",
            "success"
        )

        return redirect("/usuarios")

    return render_template(

        "editar_usuario.html",

        usuario_db=usuario_db,

        usuario=usuario
    )
# =========================
# DESATIVAR USUÁRIO
# =========================

@app.route("/desativar_usuario/<int:id>")
def desativar_usuario(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    db.session.execute(

        db.text("""

            UPDATE usuarios

            SET ativo = false

            WHERE id = :id

        """),

        {
            "id": id
        }

    )

    db.session.commit()

    flash(
        "Usuário desativado.",
        "warning"
    )

    return redirect("/usuarios")
# =========================
# IMPORTAR INVENTÁRIOS
# =========================

@app.route("/importar_inventario")
def importar_inventario():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    pasta = "Planilhas"

    arquivos = [

        arq

        for arq in os.listdir(pasta)

        if arq.endswith(".xlsx")

    ]

    total_importados = 0

    for arquivo in arquivos:

        caminho = os.path.join(
            pasta,
            arquivo
        )

        df = pd.read_excel(caminho)

        df.columns = [

            str(col).strip().upper()

            for col in df.columns

        ]

        for _, row in df.iterrows():

            id_maquina = str(
                row["ID"]
            )

            existe = db.session.execute(

                db.text("""

                    SELECT id

                    FROM ativos

                    WHERE id_maquina = :id_maquina

                """),

                {
                    "id_maquina": id_maquina
                }

            ).fetchone()

            dados = {

                "id_maquina": id_maquina,

                "marca": str(
                    row["MARCA"]
                ),

                "modelo": str(
                    row["MODELO"]
                ),

                "sistema_operacional": str(
                    row["SISTEMA OPERACIONAL"]
                ),

                "memoria_ram": str(
                    row["MEMORIA RAM"]
                ),

                "armazenamento": str(
                    row["ARMAZENAMENTO"]
                ),

                "usuario_atual": str(
                    row["USUARIO"]
                ),

                "setor": str(
                    row["SETOR"]
                )

            }

            if existe:

                db.session.execute(

                    db.text("""

                        UPDATE ativos

                        SET

                            marca = :marca,

                            modelo = :modelo,

                            sistema_operacional =
                            :sistema_operacional,

                            memoria_ram =
                            :memoria_ram,

                            armazenamento =
                            :armazenamento,

                            usuario_atual =
                            :usuario_atual,

                            setor = :setor

                        WHERE id_maquina =
                        :id_maquina

                    """),

                    dados

                )

            else:

                db.session.execute(

                    db.text("""

                        INSERT INTO ativos (

                            id_maquina,
                            marca,
                            modelo,
                            sistema_operacional,
                            memoria_ram,
                            armazenamento,
                            usuario_atual,
                            setor

                        )

                        VALUES (

                            :id_maquina,
                            :marca,
                            :modelo,
                            :sistema_operacional,
                            :memoria_ram,
                            :armazenamento,
                            :usuario_atual,
                            :setor

                        )

                    """),

                    dados

                )

            total_importados += 1

    db.session.commit()

    return f"""

    Inventários importados com sucesso!

    Total de registros processados:
    {total_importados}

    """

# =========================
# PESQUISA INVENTÁRIO
# =========================

@app.route(
    "/pesquisar_ativos",
    methods=["GET"]
)
def pesquisar_ativos():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    termo = request.args.get(
        "termo",
        ""
    )

    ativos = []

    if termo:

        ativos = db.session.execute(

            db.text("""

                SELECT *

                FROM ativos

                WHERE

                    LOWER(id_maquina)
                    LIKE LOWER(:termo)

                OR

                    LOWER(usuario_atual)
                    LIKE LOWER(:termo)

                OR

                    LOWER(setor)
                    LIKE LOWER(:termo)

                ORDER BY id DESC

            """),

            {
                "termo": f"%{termo}%"
            }

        ).fetchall()

    return render_template(

        "pesquisa_ativos.html",

        ativos=ativos,

        termo=termo,

        usuario=usuario
    )
# =========================
# EDITAR POSIÇÃO
# =========================

@app.route(
    "/editar_posicao/<posicao>",
    methods=["GET", "POST"]
)
def editar_posicao(posicao):

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

    if request.method == "POST":

        nova_maquina = request.form.get(
            "maquina"
        )

        colaborador = request.form.get(
            "colaborador"
        )

        nova_posicao = request.form.get(
            "nova_posicao"
        )

        db.session.execute(

            db.text("""

                UPDATE mapa_posicoes

                SET

                    maquina = :maquina,

                    colaborador = :colaborador,

                    posicao = :nova_posicao

                WHERE posicao = :posicao

            """),

            {
                "maquina": nova_maquina,
                "colaborador": colaborador,
                "nova_posicao": nova_posicao,
                "posicao": posicao
            }

        )

        db.session.commit()

        flash(
            "Posição atualizada com sucesso!",
            "success"
        )

        sala_db = db.session.execute(

            db.text("""

                SELECT sala

                FROM mapa_posicoes

                WHERE posicao = :nova_posicao

            """),

            {
                "nova_posicao": nova_posicao
            }

        ).fetchone()

        if sala_db:

            if sala_db.sala == "BL":

                return redirect("/mapa_bl")

            return redirect("/mapa_hunter")

        return redirect("/")

    posicao_db = db.session.execute(

        db.text("""

            SELECT *

            FROM mapa_posicoes

            WHERE posicao = :posicao

        """),

        {
            "posicao": posicao
        }

    ).fetchone()

    return render_template(

        "editar_posicao.html",

        posicao=posicao_db

    )
# =========================
# EDITAR ATIVO
# =========================

@app.route(
    "/editar_ativo/<int:id>",
    methods=["GET", "POST"]
)
def editar_ativo(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    ativo = db.session.execute(

        db.text("""

            SELECT *

            FROM ativos

            WHERE id = :id

        """),

        {
            "id": id
        }

    ).fetchone()

    if request.method == "POST":

        dados = {

            "id": id,

            "marca": request.form.get("marca"),

            "modelo": request.form.get("modelo"),

            "sistema_operacional":
            request.form.get(
                "sistema_operacional"
            ),

            "memoria_ram":
            request.form.get(
                "memoria_ram"
            ),

            "armazenamento":
            request.form.get(
                "armazenamento"
            ),

            "usuario_atual":
            request.form.get(
                "usuario_atual"
            ),

            "setor":
            request.form.get(
                "setor"
            )

        }

        db.session.execute(

            db.text("""

                UPDATE ativos

                SET

                    marca = :marca,

                    modelo = :modelo,

                    sistema_operacional =
                    :sistema_operacional,

                    memoria_ram =
                    :memoria_ram,

                    armazenamento =
                    :armazenamento,

                    usuario_atual =
                    :usuario_atual,

                    setor = :setor

                WHERE id = :id

            """),

            dados

        )

        db.session.commit()

        return redirect(
            "/pesquisar_ativos"
        )

    return render_template(

        "editar_ativo.html",

        ativo=ativo,

        usuario=usuario
    )

# =========================
# MAPA HUNTER
# =========================

@app.route("/mapa_hunter")
def mapa_hunter():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    maquinas = db.session.execute(

        db.text("""

            SELECT
                id,
                id_maquina,
                usuario_atual,
                marca,
                modelo,
                setor

            FROM ativos

            WHERE LOWER(setor)
            LIKE LOWER('%hunter%')

        """)

    ).fetchall()

    chamados_abertos = db.session.execute(

        db.text("""

            SELECT DISTINCT maquina

            FROM chamados

            WHERE status != 'resolvido'

        """)

    ).fetchall()

    maquinas_com_chamado = [

        c.maquina

        for c in chamados_abertos

        if c.maquina

    ]

    mapa_db = db.session.execute(

        db.text("""

            SELECT
                posicao,
                maquina,
                colaborador,
                sala

            FROM mapa_posicoes

            WHERE sala = 'Hunter'

            ORDER BY posicao

        """)

    ).fetchall()

    mapa = {

        item.posicao: {
            "maquina": item.maquina,
            "colaborador": item.colaborador
        }

        for item in mapa_db

    }

    return render_template(

        "mapa_hunter.html",

        usuario=usuario,

        maquinas=maquinas,

        mapa=mapa,

        mapa_db=mapa_db,

        maquinas_com_chamado=
        maquinas_com_chamado

    )

# =========================
# MAPA BL
# =========================

@app.route("/mapa_bl")
def mapa_bl():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    maquinas = db.session.execute(

        db.text("""

            SELECT
                id,
                id_maquina,
                usuario_atual,
                marca,
                modelo,
                setor

            FROM ativos

            WHERE LOWER(setor)
            LIKE LOWER('%bl%')

        """)

    ).fetchall()

    chamados_abertos = db.session.execute(

        db.text("""

            SELECT DISTINCT maquina

            FROM chamados

            WHERE status != 'Finalizado'

        """)

    ).fetchall()

    maquinas_com_chamado = [

        c.maquina

        for c in chamados_abertos

        if c.maquina

    ]

    mapa_db = db.session.execute(

        db.text("""

            SELECT
                posicao,
                maquina,
                colaborador,
                sala

            FROM mapa_posicoes

            WHERE sala = 'BL'

            ORDER BY posicao

        """)

    ).fetchall()

    mapa = {

        item.posicao: {
            "maquina": item.maquina,
            "colaborador": item.colaborador
        }

        for item in mapa_db

    }

    return render_template(

        "mapa_bl.html",

        usuario=usuario,

        maquinas=maquinas,

        mapa=mapa,

        mapa_db=mapa_db,

        maquinas_com_chamado=
        maquinas_com_chamado

    )
# =========================
# TESTE BANCO
# =========================

@app.route("/teste_bd")
def teste_bd():

    try:

        db.session.execute(
        db.text("SELECT 1")
    )

        return "Banco conectado com sucesso!"

    except Exception as e:

        return f"Erro: {e}"
@app.route("/debug-db")
def debug_db():
    result = db.session.execute(
        db.text("SELECT COUNT(*) FROM usuarios")
    ).fetchone()
    return f"Usuarios: {result[0]}"
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )