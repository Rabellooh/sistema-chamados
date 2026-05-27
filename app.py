from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, send_from_directory
from flask_mail import Mail, Message
import os
import json
import urllib.parse
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
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

@app.context_processor
def carregar_notificacoes():

    usuario = session.get("usuario")

    if not usuario:
        return {}

    notificacoes = db.session.execute(
        text("""
            SELECT
                id,
                titulo,
                mensagem,
                tipo,
                link,
                lida,
                criada_em
            FROM notificacoes
            WHERE usuario_id = :usuario_id
            ORDER BY criada_em DESC
            LIMIT 5
        """),
        {
            "usuario_id": usuario["id"]
        }
    ).fetchall()

    total_notificacoes = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM notificacoes
            WHERE usuario_id = :usuario_id
            AND lida = false
        """),
        {
            "usuario_id": usuario["id"]
        }
    ).scalar()

    return {
        "notificacoes_topo": notificacoes,
        "total_notificacoes": total_notificacoes
    }


def criar_notificacao(
    usuario_id,
    titulo,
    mensagem,
    tipo="sistema",
    link="#"
):

    db.session.execute(
        text("""
            INSERT INTO notificacoes
            (
                usuario_id,
                titulo,
                mensagem,
                tipo,
                link
            )
            VALUES
            (
                :usuario_id,
                :titulo,
                :mensagem,
                :tipo,
                :link
            )
        """),
        {
            "usuario_id": usuario_id,
            "titulo": titulo,
            "mensagem": mensagem,
            "tipo": tipo,
            "link": link
        }
    )

    db.session.commit()


@app.route("/notificacao/<int:id>")
def abrir_notificacao(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    db.session.execute(
        text("""
            UPDATE notificacoes
            SET lida = true
            WHERE id = :id
            AND usuario_id = :usuario_id
        """),
        {
            "id": id,
            "usuario_id": usuario["id"]
        }
    )

    db.session.commit()

    return redirect(request.args.get("link", "/"))

# =========================
# EXCLUIR NOTIFICAÇÃO
# =========================

@app.route("/excluir_notificacao/<int:id>")
def excluir_notificacao(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    db.session.execute(

        db.text("""

            DELETE FROM notificacoes

            WHERE id = :id
            AND usuario_id = :usuario_id

        """),

        {
            "id": id,
            "usuario_id": usuario["id"]
        }

    )

    db.session.commit()

    return redirect(request.referrer or "/")


# =========================
# LIMPAR NOTIFICAÇÕES
# =========================

@app.route("/limpar_notificacoes")
def limpar_notificacoes():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    db.session.execute(

        db.text("""

            DELETE FROM notificacoes

            WHERE usuario_id = :usuario_id

        """),

        {
            "usuario_id": usuario["id"]
        }

    )

    db.session.commit()

    return redirect(request.referrer or "/")

# =========================
# ENVIO EMAIL
# =========================
def enviar_email(destinatario, assunto, html):

    try:

        msg = Message(
            subject=assunto,
            recipients=[destinatario]
        )

        msg.html = html

        mail.send(msg)

        print(f"Email enviado para {destinatario}")

        return True

    except Exception as e:

        print("ERRO AO ENVIAR EMAIL:")
        print(e)

        return False

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

        if resultado and check_password_hash(resultado.senha, senha):

            session["usuario"] = {

                "id": resultado.id,

                "nome": resultado.nome,

                "tipo": resultado.tipo,

                "setor": resultado.setor

            }
            if resultado.precisa_trocar_senha:
                return redirect("/trocar_senha")

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
# TROCAR SENHA
# =========================

@app.route(
    "/trocar_senha",
    methods=["GET", "POST"]
)
def trocar_senha():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if request.method == "POST":

        nova_senha = request.form.get(
            "nova_senha"
        )

        confirmar_senha = request.form.get(
            "confirmar_senha"
        )

        if nova_senha != confirmar_senha:

            flash(
                "As senhas não coincidem.",
                "error"
            )

            return redirect("/trocar_senha")

        senha_hash = generate_password_hash(
            nova_senha
        )

        db.session.execute(

            db.text("""

                UPDATE usuarios

                SET

                    senha = :senha,

                    precisa_trocar_senha = FALSE

                WHERE id = :id

            """),

            {
                "senha": senha_hash,
                "id": usuario["id"]
            }

        )

        db.session.commit()

        flash(
            "Senha alterada com sucesso!",
            "success"
        )

        return redirect("/")

    return render_template(
        "trocar_senha.html",
        usuario=usuario
    )


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
        if c.status == "Finalizado"
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

        # =========================
        # KANBAN
        # =========================

        tarefas_pendentes = db.session.execute(

            text("""

                SELECT COUNT(*)

                FROM tarefas

                WHERE LOWER(status) = 'pendente'

            """)

        ).scalar()

        tarefas_andamento = db.session.execute(

            text("""

                SELECT COUNT(*)

                FROM tarefas

                WHERE LOWER(status) = 'andamento'

            """)

        ).scalar()

        tarefas_aguardando = db.session.execute(

            text("""

                SELECT COUNT(*)

                FROM tarefas

                WHERE LOWER(status) = 'aguardando'

            """)

        ).scalar()

        tarefas_criticas = db.session.execute(

            text("""

                SELECT *

                FROM tarefas

                WHERE LOWER(prioridade) = 'critica'

                AND LOWER(status) != 'finalizado'

                ORDER BY id DESC

                LIMIT 5

            """)

        ).fetchall()

        # =========================
        # MÁQUINAS COM PROBLEMAS
        # =========================

        maquinas_problema = db.session.execute(

            text("""

                SELECT DISTINCT maquina

                FROM chamados

                WHERE status != 'Finalizado'
                AND maquina IS NOT NULL

                LIMIT 10

            """)

        ).fetchall()

        # =========================
        # ÚLTIMAS MOVIMENTAÇÕES
        # =========================

        movimentacoes = db.session.execute(

            text("""

                SELECT *

                FROM movimentacoes_mapa

                ORDER BY data_movimentacao DESC

                LIMIT 5

            """)

        ).fetchall()

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
            ),

            tarefas_pendentes=tarefas_pendentes,
            tarefas_andamento=tarefas_andamento,
            tarefas_aguardando=tarefas_aguardando,

            tarefas_criticas=tarefas_criticas,

            maquinas_problema=maquinas_problema,

            movimentacoes=movimentacoes

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

    if usuario["tipo"] == "ti":
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

        chamado_criado = db.session.execute(

            db.text("""

                SELECT id

                FROM chamados

                WHERE usuario = :usuario

                ORDER BY id DESC

                LIMIT 1

            """),

            {
                "usuario": usuario["nome"]
            }

        ).fetchone()

        if chamado_criado:

            tecnicos = db.session.execute(

                db.text("""

                    SELECT id

                    FROM usuarios

                    WHERE tipo IN ('ti', 'administracao')
                    AND ativo = true

                """)

            ).fetchall()

            for tecnico in tecnicos:

                criar_notificacao(

                    usuario_id=tecnico.id,

                    titulo="Novo chamado aberto",

                    mensagem=f"{usuario['nome']} abriu o chamado #{chamado_criado.id}.",

                    tipo="chamado",

                    link=f"/chamado/{chamado_criado.id}"

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

    chamado = db.session.execute(

        db.text("""

            SELECT *

            FROM chamados

            WHERE id = :id

        """),

        {
            "id": chamado_id
        }

    ).fetchone()

    if chamado:

        # =========================
        # SE COLABORADOR ENVIOU
        # NOTIFICA TODOS OS TIs
        # =========================

        if usuario["tipo"] not in [
            "ti",
            "administracao"
        ]:

            tecnicos = db.session.execute(

                db.text("""

                    SELECT id

                    FROM usuarios

                    WHERE tipo IN ('ti', 'administracao')
                    AND ativo = true

                """)

            ).fetchall()

            for tecnico in tecnicos:

                criar_notificacao(

                    usuario_id=tecnico.id,

                    titulo="Nova mensagem em chamado",

                    mensagem=f"{usuario['nome']} enviou uma mensagem no chamado #{chamado_id}.",

                    tipo="mensagem",

                    link=f"/chamado/{chamado_id}"

                )

        # =========================
        # SE TI / ADMIN ENVIOU
        # NOTIFICA O DONO DO CHAMADO
        # =========================

        else:

            dono_chamado = db.session.execute(

                db.text("""

                    SELECT id

                    FROM usuarios

                    WHERE LOWER(nome) = LOWER(:nome)

                    LIMIT 1

                """),

                {
                    "nome": chamado.usuario
                }

            ).fetchone()

            if dono_chamado:

                criar_notificacao(

                    usuario_id=dono_chamado.id,

                    titulo="Nova resposta no seu chamado",

                    mensagem=f"{usuario['nome']} respondeu o chamado #{chamado_id}.",

                    tipo="mensagem",

                    link=f"/chamado/{chamado_id}"

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
# ASSUMIR CHAMADO
# =========================

@app.route("/assumir/<int:chamado_id>")
def assumir_chamado(chamado_id):

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

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

    chamado = db.session.execute(

        db.text("""

            SELECT *

            FROM chamados

            WHERE id = :id

        """),

        {
            "id": chamado_id
        }

    ).fetchone()

    usuario_chamado = db.session.execute(

        db.text("""

            SELECT id, email

            FROM usuarios

            WHERE nome = :nome

        """),

        {
            "nome": chamado.usuario
        }

    ).fetchone()

    email_usuario = None

    if usuario_chamado:

        email_usuario = usuario_chamado.email

        # =========================
        # NOTIFICAÇÃO
        # =========================

        criar_notificacao(

            usuario_id=usuario_chamado.id,

            titulo="Chamado assumido",

            mensagem=f"{usuario['nome']} assumiu seu chamado #{chamado.id}.",

            tipo="chamado",

            link=f"/chamado/{chamado.id}"

        )

    if email_usuario:

        try:

            msg = Message(
                subject="Seu chamado foi assumido",
                recipients=[email_usuario]
            )

            msg.sender = (
                "Sistema TI",
                "helpdesk.tctelecom@gmail.com"
            )

            msg.html = f"""

            <div style="
                background:#f4f7fb;
                padding:40px;
                font-family:Arial,sans-serif;
            ">

                <div style="
                    max-width:600px;
                    margin:auto;
                    background:white;
                    border-radius:16px;
                    overflow:hidden;
                    border:1px solid #dbe4ee;
                    box-shadow:0 4px 20px rgba(0,0,0,0.08);
                ">

                    <div style="
                        background:#2563eb;
                        padding:25px;
                        color:white;
                    ">

                        <h1 style="
                            margin:0;
                            font-size:24px;
                        ">
                            Sistema de Chamados TI
                        </h1>

                    </div>

                    <div style="padding:30px;">

                        <h2 style="
                            color:#0f172a;
                            margin-top:0;
                        ">
                            Chamado em atendimento
                        </h2>

                        <p style="
                            color:#334155;
                            line-height:1.7;
                            font-size:15px;
                        ">
                            Olá,
                        </p>

                        <p style="
                            color:#334155;
                            line-height:1.7;
                            font-size:15px;
                        ">
                            Seu chamado foi assumido
                            e já está em atendimento.
                        </p>

                        <div style="
                            background:#f8fafc;
                            border:1px solid #e2e8f0;
                            border-radius:10px;
                            padding:20px;
                            margin:25px 0;
                        ">

                            <p style="margin:0 0 10px 0;">
                                <strong>Status:</strong>
                                Em andamento
                            </p>

                            <p style="margin:0 0 10px 0;">
                                <strong>Técnico:</strong>
                                {session["usuario"]["nome"]}
                            </p>

                            <p style="margin:0;">
                                <strong>Chamado:</strong>
                                #{chamado.id}
                            </p>

                        </div>

                        <p style="
                            color:#64748b;
                            font-size:14px;
                            line-height:1.6;
                        ">
                            Em breve a equipe de TI
                            irá analisar o problema.
                        </p>

                    </div>

                    <div style="
                        background:#f8fafc;
                        padding:20px;
                        border-top:1px solid #e2e8f0;
                        text-align:center;
                    ">

                        <p style="
                            margin:0;
                            color:#94a3b8;
                            font-size:12px;
                        ">
                            Mensagem automática • Não responda este email
                        </p>

                    </div>

                </div>

            </div>

            """

            mail.send(msg)

        except Exception as e:

            print(e)

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

        flash(
            "Chamado não encontrado.",
            "error"
        )

        return redirect("/chamados")

    db.session.execute(

        db.text("""

            UPDATE chamados

            SET status = 'Finalizado'

            WHERE id = :id

        """),

        {
            "id": id
        }

    )

    usuario_chamado = db.session.execute(

        db.text("""

            SELECT id

            FROM usuarios

            WHERE LOWER(nome) = LOWER(:nome)

            LIMIT 1

        """),

        {
            "nome": chamado.usuario
        }

    ).fetchone()

    if usuario_chamado:

        criar_notificacao(

            usuario_id=usuario_chamado.id,

            titulo="Chamado finalizado",

            mensagem=f"{usuario['nome']} finalizou seu chamado #{id}.",

            tipo="chamado",

            link=f"/chamado/{id}"

        )

    db.session.commit()

    flash(
        "Chamado finalizado com sucesso!",
        "success"
    )

    return redirect("/chamados")

# =========================
# EXCLUIR
# =========================

@app.route(
    "/excluir/<int:chamado_id>",
    methods=["GET", "POST"]
)
def excluir_chamado(chamado_id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

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

        tecnicos_vinculados = db.session.execute(text("""

            SELECT tecnico
            FROM chamados_tecnicos
            WHERE chamado_id = :id

        """), {
            "id": chamado_id
        }).fetchall()

        usuario_dono = db.session.execute(text("""

            SELECT id
            FROM usuarios
            WHERE LOWER(nome) = LOWER(:nome)
            LIMIT 1

        """), {
            "nome": chamado.usuario
        }).fetchone()

        if usuario_dono:

            criar_notificacao(

                usuario_id=usuario_dono.id,

                titulo="Chamado excluído",

                mensagem=f"O chamado #{chamado_id} foi excluído por {usuario['nome']}.",

                tipo="chamado",

                link="/chamados"

            )

        for tecnico in tecnicos_vinculados:

            tecnico_db = db.session.execute(text("""

                SELECT id
                FROM usuarios
                WHERE LOWER(nome) = LOWER(:nome)
                LIMIT 1

            """), {
                "nome": tecnico.tecnico
            }).fetchone()

            if tecnico_db:

                criar_notificacao(

                    usuario_id=tecnico_db.id,

                    titulo="Chamado excluído",

                    mensagem=f"O chamado #{chamado_id}, vinculado a você, foi excluído por {usuario['nome']}.",

                    tipo="chamado",

                    link="/chamados"

                )

        # REMOVE MENSAGENS RELACIONADAS

        db.session.execute(text("""

            DELETE FROM mensagens

            WHERE chamado_id = :id

        """), {
            "id": chamado_id
        })

        # REMOVE TÉCNICOS RELACIONADOS

        db.session.execute(text("""

            DELETE FROM chamados_tecnicos

            WHERE chamado_id = :id

        """), {
            "id": chamado_id
        })

        # REMOVE CHAMADO

        db.session.execute(text("""

            DELETE FROM chamados

            WHERE id = :id

        """), {
            "id": chamado_id
        })

        db.session.commit()

        flash(
            "Chamado excluído com sucesso!",
            "success"
        )

        return redirect("/chamados")

    return render_template(

        "confirmar_exclusao.html",

        usuario=usuario,

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

    total_ativos = db.session.execute(

        db.text("""

            SELECT COUNT(*)

            FROM ativos

        """)

    ).scalar()

    total_setores = db.session.execute(

        db.text("""

            SELECT COUNT(DISTINCT setor)

            FROM ativos

        """)

    ).scalar()

    total_colaboradores = db.session.execute(

        db.text("""

            SELECT COUNT(DISTINCT usuario_atual)

            FROM ativos

            WHERE usuario_atual IS NOT NULL

        """)

    ).scalar()

    maquinas_chamado = db.session.execute(

        db.text("""

            SELECT COUNT(DISTINCT maquina)

            FROM chamados

            WHERE status != 'Finalizado'

        """)

    ).scalar()

    return render_template(

        "inventario.html",

        usuario=usuario,

        ativos=ativos,

        total_ativos=total_ativos,

        total_setores=total_setores,

        total_colaboradores=total_colaboradores,

        maquinas_chamado=maquinas_chamado

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

        nova_senha = request.form.get("senha")

        if nova_senha:

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
                        nova_senha
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

        else:

            db.session.execute(

                db.text("""

                    UPDATE usuarios

                    SET

                        nome = :nome,
                        tipo = :tipo,
                        setor = :setor,
                        email = :email,
                        ativo = :ativo

                    WHERE id = :id

                """),

                {

                    "id": id,

                    "nome": request.form.get("nome"),

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
# RESETAR SENHA
# =========================

@app.route("/resetar_senha/<int:id>")
def resetar_senha(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:
        return redirect("/")

    nova_senha = "123456"

    senha_hash = generate_password_hash(
        nova_senha
    )

    db.session.execute(

        db.text("""

            UPDATE usuarios

            SET senha = :senha,

            precisa_trocar_senha = TRUE

            WHERE id = :id

        """),

        {
            "senha": senha_hash,
            "id": id
        }

    )

    db.session.commit()

    flash(
        "Senha resetada para: 123456",
        "success"
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
                row.get("ID", "")
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

    ram = request.args.get(
        "ram",
        ""
    )

    armazenamento = request.args.get(
        "armazenamento",
        ""
    )

    sistema = request.args.get(
        "sistema",
        ""
    )

    marca = request.args.get(
        "marca",
        ""
    )

    query = """

        SELECT

            id,
            id_maquina,
            marca,
            modelo,
            sistema_operacional,
            memoria_ram,
            armazenamento,
            usuario_atual,
            setor

        FROM ativos

        WHERE 1=1

    """

    params = {}

    if termo:

        query += """

            AND (

                LOWER(id_maquina)
                LIKE LOWER(:termo)

                OR

                LOWER(usuario_atual)
                LIKE LOWER(:termo)

                OR

                LOWER(setor)
                LIKE LOWER(:termo)

                OR

                LOWER(modelo)
                LIKE LOWER(:termo)

            )

        """

        params["termo"] = f"%{termo}%"

    if ram:

        query += """

            AND LOWER(memoria_ram)
            LIKE LOWER(:ram)

        """

        params["ram"] = f"%{ram}%"

    if armazenamento:

        query += """

            AND LOWER(armazenamento)
            LIKE LOWER(:armazenamento)

        """

        params["armazenamento"] = f"%{armazenamento}%"

    if sistema:

        query += """

            AND LOWER(sistema_operacional)
            LIKE LOWER(:sistema)

        """

        params["sistema"] = f"%{sistema}%"

    if marca:

        query += """

            AND LOWER(marca)
            LIKE LOWER(:marca)

        """

        params["marca"] = f"%{marca}%"

    query += """

        ORDER BY id DESC

    """

    ativos = db.session.execute(

        db.text(query),

        params

    ).fetchall()

    return render_template(

        "pesquisa_ativos.html",

        ativos=ativos,

        termo=termo,

        ram=ram,

        armazenamento=armazenamento,

        sistema=sistema,

        marca=marca,

        usuario=usuario

    )
# =========================
# EDITAR POSIÇÃO
# =========================

@app.route(
    "/editar_posicao/<path:posicao>",
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

    posicao = urllib.parse.unquote(posicao)

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

    if not posicao_db:

        flash(
            "Posição não encontrada.",
            "error"
        )

        return redirect("/")

    ativo = None

    if posicao_db.maquina:

        ativo = db.session.execute(

            db.text("""

                SELECT *

                FROM ativos

                WHERE id_maquina = :maquina

            """),

            {
                "maquina": posicao_db.maquina
            }

        ).fetchone()

    if request.method == "POST":

        nova_posicao = request.form.get(
            "nova_posicao"
        )

        nova_maquina = request.form.get(
            "maquina"
        )

        colaborador = request.form.get(
            "colaborador"
        )

        # =========================
        # ATUALIZA MAPA
        # =========================

        db.session.execute(

            db.text("""

                UPDATE mapa_posicoes

                SET

                    posicao = :nova_posicao,
                    maquina = :maquina

                WHERE id = :id

            """),

            {
                "nova_posicao": nova_posicao,
                "maquina": nova_maquina,
                "id": posicao_db.id
            }

        )

        # =========================
        # ATUALIZA ATIVO
        # =========================

        if nova_maquina:

            db.session.execute(

                db.text("""

                    UPDATE ativos

                    SET usuario_atual = :usuario

                    WHERE id_maquina = :maquina

                """),

                {
                    "usuario": colaborador,
                    "maquina": nova_maquina
                }

            )

        db.session.commit()

        flash(
            "Posição atualizada com sucesso!",
            "success"
        )

        if posicao_db.sala == "BL":
            return redirect("/mapa_bl")

        return redirect("/mapa_hunter")

    return render_template(

        "editar_posicao.html",

        usuario=usuario,

        posicao=posicao_db,

        ativo=ativo

    )
# =========================
# EXCLUIR POSIÇÃO
# =========================

@app.route("/excluir_posicao/<path:posicao>")
def excluir_posicao(posicao):

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

    sala_db = db.session.execute(

        db.text("""

            SELECT sala

            FROM mapa_posicoes

            WHERE posicao = :posicao

        """),

        {
            "posicao": posicao
        }

    ).fetchone()

    db.session.execute(

        db.text("""

            DELETE FROM mapa_posicoes

            WHERE posicao = :posicao

        """),

        {
            "posicao": posicao
        }

    )

    db.session.commit()

    flash(
        "Posição excluída com sucesso!",
        "success"
    )

    if sala_db:

        if sala_db.sala == "BL":

            return redirect(
                url_for("mapa_bl")
            )

        return redirect(
            url_for("mapa_hunter")
        )

    return redirect("/")
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

    # =========================
    # ATIVOS HUNTER
    # =========================

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

    # =========================
    # CHAMADOS ABERTOS
    # =========================

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

    # =========================
    # POSIÇÕES HUNTER
    # =========================

    mapa_db = db.session.execute(

        db.text("""

            SELECT
                id,
                posicao,
                maquina,
                colaborador,
                sala

            FROM mapa_posicoes

            WHERE sala = 'Hunter'

            ORDER BY posicao

        """)

    ).fetchall()

    # =========================
    # MONTAGEM MAPA
    # =========================

    mapa = {}

    for item in mapa_db:

        status = "livre"

        if item.maquina in maquinas_com_chamado:

            status = "problema"

        maquina_info = None

        for maquina in maquinas:

            if (
                str(maquina.id_maquina).strip()
                ==
                str(item.maquina).strip()
            ):

                maquina_info = {

                    "modelo": maquina.modelo,
                    "usuario_atual": maquina.usuario_atual,
                    "marca": maquina.marca,
                    "setor": maquina.setor

                }

                break

        mapa[item.posicao] = {

            "maquina": item.maquina,

            "colaborador": (
                maquina_info["usuario_atual"]
                if maquina_info
                else item.colaborador
            ),

            "status": status,

            "info": maquina_info

        }

    # =========================
    # CONTADORES
    # =========================

    total_desktops = len([

        item for item in mapa_db

        if "NOTEBOOK" not in item.posicao.upper()

    ])

    total_notebooks = len([

        item for item in mapa_db

        if "NOTEBOOK" in item.posicao.upper()

    ])

    total_chamados = len(maquinas_com_chamado)

    # =========================
    # RENDER
    # =========================

    return render_template(

        "mapa_hunter.html",

        usuario=usuario,

        maquinas=maquinas,

        mapa=mapa,

        mapa_db=mapa_db,

        maquinas_com_chamado=maquinas_com_chamado,

        total_desktops=total_desktops,

        total_notebooks=total_notebooks,

        total_chamados=total_chamados

    )
# =========================
# MAPA BL
# =========================

@app.route("/mapa_bl")
def mapa_bl():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    maquinas = db.session.execute(

        db.text("""

            SELECT
                id_maquina,
                usuario_atual,
                marca,
                modelo,
                setor

            FROM ativos

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
                id,
                posicao,
                maquina,
                sala

            FROM mapa_posicoes

            WHERE sala = 'BL'

            ORDER BY posicao

        """)

    ).fetchall()

    mapa = {}

    for item in mapa_db:

        status = "livre"

        if item.maquina in maquinas_com_chamado:
            status = "problema"

        maquina_info = None

        for maquina in maquinas:

            if maquina.id_maquina == item.maquina:

                maquina_info = {

                    "modelo": maquina.modelo,
                    "usuario_atual": maquina.usuario_atual,
                    "marca": maquina.marca,
                    "setor": maquina.setor

                }

                break

        mapa[item.posicao] = {

            "maquina": item.maquina,

            "colaborador":
            maquina_info["usuario_atual"]
            if maquina_info
            else None,

            "status": status,

            "info": maquina_info

        }

    total_desktops = len([

        item for item in mapa_db

        if (
            item.posicao.startswith("1015")
            or
            item.posicao.startswith("1016")
        )

    ])

    total_notebooks = len([

        item for item in mapa_db

        if "NOTEBOOK" in item.posicao.upper()

    ])

    total_chamados = len(maquinas_com_chamado)

    return render_template(

        "mapa_bl.html",

        usuario=usuario,
        maquinas=maquinas,
        mapa=mapa,
        mapa_db=mapa_db,
        maquinas_com_chamado=maquinas_com_chamado,

        total_desktops=total_desktops,
        total_notebooks=total_notebooks,
        total_chamados=total_chamados

    )
# =========================
# NOVA POSIÇÃO
# =========================

@app.route(
    "/nova_posicao",
    methods=["GET", "POST"]
)
def nova_posicao():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

    if request.method == "POST":

        sala = request.form.get(
            "sala"
        )

        posicao = request.form.get(
            "posicao"
        )

        maquina = request.form.get(
            "maquina"
        )

        colaborador = request.form.get(
            "colaborador"
        )

        # limpa espaços
        if sala:
            sala = sala.strip()

        if posicao:
            posicao = posicao.strip()

        if maquina:
            maquina = maquina.strip()

        if colaborador:
            colaborador = colaborador.strip()

        # verifica se já existe
        existe = db.session.execute(

            db.text("""

                SELECT id

                FROM mapa_posicoes

                WHERE posicao = :posicao

            """),

            {
                "posicao": posicao
            }

        ).fetchone()

        if existe:

            flash(
                "Essa posição já existe.",
                "error"
            )

            return redirect("/nova_posicao")

        db.session.execute(

            db.text("""

                INSERT INTO mapa_posicoes (

                    sala,
                    posicao,
                    maquina,
                    colaborador

                )

                VALUES (

                    :sala,
                    :posicao,
                    :maquina,
                    :colaborador

                )

            """),

            {
                "sala": sala,
                "posicao": posicao,
                "maquina": maquina,
                "colaborador": colaborador
            }

        )

        db.session.commit()

        flash(
            "Posição criada com sucesso!",
            "success"
        )

        if sala == "BL":

            return redirect("/mapa_bl")

        return redirect("/mapa_hunter")

    return render_template(

        "nova_posicao.html",

        usuario=usuario

    )

# =========================
# MOVIMENTAR MÁQUINA
# =========================

@app.route(
    "/movimentar_maquina",
    methods=["GET", "POST"]
)
def movimentar_maquina():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

    posicoes = db.session.execute(

        db.text("""

            SELECT *

            FROM mapa_posicoes

            ORDER BY sala, posicao

        """)

    ).fetchall()

    if request.method == "POST":

        origem = request.form.get(
            "origem"
        )

        destino = request.form.get(
            "destino"
        )

        origem_db = db.session.execute(

            db.text("""

                SELECT *

                FROM mapa_posicoes

                WHERE posicao = :origem

            """),

            {
                "origem": origem
            }

        ).fetchone()

        destino_db = db.session.execute(

            db.text("""

                SELECT *

                FROM mapa_posicoes

                WHERE posicao = :destino

            """),

            {
                "destino": destino
            }

        ).fetchone()

        if not origem_db or not destino_db:

            flash(
                "Posição inválida.",
                "error"
            )

            return redirect(
                "/movimentar_maquina"
            )
        ativo_origem = None

        if origem_db.maquina:

            ativo_origem = db.session.execute(

                db.text("""

                    SELECT *

                    FROM ativos

                    WHERE id_maquina = :maquina

                """),

                {
                    "maquina": origem_db.maquina
                }

            ).fetchone()
        # move dados
        db.session.execute(

            db.text("""

                UPDATE mapa_posicoes

                SET

                    maquina = :maquina,

                    colaborador = :colaborador

                WHERE posicao = :destino

            """),

            {
                "maquina": origem_db.maquina,
                "colaborador": (
                    ativo_origem.usuario_atual
                    if ativo_origem
                    else None
                ),
                "destino": destino
            }

        )

        # limpa origem
        db.session.execute(

            db.text("""

                UPDATE mapa_posicoes

                SET

                    maquina = NULL,

                    colaborador = NULL

                WHERE posicao = :origem

            """),

            {
                "origem": origem
            }

        )
        
        #histórico
        db.session.execute(
            db.text("""
                    INSERT INTO movimentacoes_mapa(
                    maquina,
                    colaborador,
                    origem,
                    destino,
                    usuario_responsavel
                    )
                    
                    VALUES(
                    :maquina,
                    :colaborador,
                    :origem,
                    :destino,
                    :usuario
                    )
                    """),
                {
                    "maquina": origem_db.maquina,
                    "colaborador": origem_db.colaborador,
                    "origem": origem,
                    "destino": destino,
                    "usuario": usuario["nome"]
                }
        )

        db.session.commit()

        flash(
            "Movimentação realizada com sucesso!",
            "success"
        )

        if origem_db.sala == "BL":

            return redirect("/mapa_bl")

        return redirect("/mapa_hunter")

    return render_template(

        "movimentar_maquina.html",

        usuario=usuario,

        posicoes=posicoes

    )

# =========================
# HISTÓRICO MAPA
# =========================

@app.route("/historico_mapa")
def historico_mapa():

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return redirect("/")

    historico = db.session.execute(

        db.text("""

            SELECT *

            FROM movimentacoes_mapa

            ORDER BY data_movimentacao DESC

        """)

    ).fetchall()

    return render_template(

        "historico_mapa.html",

        usuario=usuario,

        historico=historico

    )

# =========================
# HISTÓRICO DA MÁQUINA
# =========================

@app.route("/historico_maquina/<id_maquina>")
def historico_maquina(id_maquina):

    usuario = session.get("usuario")

    if not usuario:

        return redirect("/login")

    ativo = db.session.execute(

        db.text("""

            SELECT *

            FROM ativos

            WHERE id_maquina = :id_maquina

        """),

        {
            "id_maquina": id_maquina
        }

    ).fetchone()

    if not ativo:

        flash(
            "Máquina não encontrada.",
            "error"
        )

        return redirect("/")

    chamados = db.session.execute(

        db.text("""

            SELECT *

            FROM chamados

            WHERE maquina = :id_maquina

            ORDER BY id DESC

        """),

        {
            "id_maquina": id_maquina
        }

    ).fetchall()

    movimentacoes = db.session.execute(

        db.text("""

            SELECT *

            FROM movimentacoes_mapa

            WHERE maquina = :id_maquina

            ORDER BY data_movimentacao DESC

        """),

        {
            "id_maquina": id_maquina
        }

    ).fetchall()

    total_chamados = len(chamados)

    chamados_abertos = len([

        c for c in chamados

        if (c.status or "").lower() != "finalizado"

    ])

    chamados_finalizados = len([

        c for c in chamados

        if (c.status or "").lower() == "finalizado"

    ])

    return render_template(

        "historico_maquina.html",

        usuario=usuario,

        ativo=ativo,

        chamados=chamados,

        movimentacoes=movimentacoes,

        total_chamados=total_chamados,

        chamados_abertos=chamados_abertos,

        chamados_finalizados=chamados_finalizados

    )
# =========================
# KANBAN - TAREFAS TI
# =========================

# =========================
# TAREFAS
# =========================

@app.route("/tarefas")
def tarefas():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    pendentes = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE LOWER(status) = 'pendente'

            ORDER BY id DESC

        """)

    ).fetchall()

    andamento = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE LOWER(status) = 'andamento'

            ORDER BY id DESC

        """)

    ).fetchall()

    aguardando = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE LOWER(status) = 'aguardando'

            ORDER BY id DESC

        """)

    ).fetchall()

    finalizadas = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE LOWER(status) = 'finalizado'

            ORDER BY id DESC

        """)

    ).fetchall()

    return render_template(

        "tarefas.html",

        usuario=usuario,

        pendentes=pendentes,

        andamento=andamento,

        aguardando=aguardando,

        finalizadas=finalizadas

    )


# =========================
# NOVA TAREFA
# =========================

@app.route(
    "/nova_tarefa",
    methods=["POST"]
)
def nova_tarefa():

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    dados = {

        "titulo":
        request.form.get("titulo"),

        "descricao":
        request.form.get("descricao"),

        "prioridade":
        request.form.get("prioridade"),

        "responsavel":
        request.form.get("responsavel"),

        "setor":
        request.form.get("setor"),

        "prazo":
        request.form.get("prazo") or None,

        "criado_por":
        usuario["nome"]

    }

    db.session.execute(

        db.text("""

            INSERT INTO tarefas (

                titulo,
                descricao,
                prioridade,
                responsavel,
                setor,
                prazo,
                status,
                criado_por

            )

            VALUES (

                :titulo,
                :descricao,
                :prioridade,
                :responsavel,
                :setor,
                :prazo,
                'pendente',
                :criado_por

            )

        """),

        dados

    )

    # =========================
    # NOTIFICAÇÃO
    # =========================

    responsavel_nome = request.form.get("responsavel")

    if responsavel_nome:

        responsavel_db = db.session.execute(

            db.text("""

                SELECT id

                FROM usuarios

                WHERE LOWER(nome) = LOWER(:nome)

                LIMIT 1

            """),

            {
                "nome": responsavel_nome
            }

        ).fetchone()

        if responsavel_db:

            criar_notificacao(

                usuario_id=responsavel_db.id,

                titulo="Nova tarefa atribuída",

                mensagem=f"Você recebeu a tarefa: {request.form.get('titulo')}",

                tipo="kanban",

                link="/tarefas"

            )

    db.session.commit()

    flash(
        "Tarefa criada com sucesso!",
        "success"
    )

    return redirect("/tarefas")
# =========================
# ALTERAR STATUS
# =========================

@app.route("/mover_tarefa/<int:id>/<status>")
def mover_tarefa(id, status):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    status_validos = [
        "pendente",
        "andamento",
        "aguardando",
        "finalizado"
    ]

    if status not in status_validos:

        flash(
            "Status inválido.",
            "error"
        )

        return redirect("/tarefas")

    db.session.execute(

        db.text("""

            UPDATE tarefas

            SET status = :status

            WHERE id = :id

        """),

        {
            "id": id,
            "status": status
        }

    )

    db.session.commit()

    flash(
        "Status atualizado!",
        "success"
    )

    return redirect("/tarefas")


# =========================
# EDITAR TAREFA
# =========================

@app.route(
    "/editar_tarefa/<int:id>",
    methods=["GET", "POST"]
)
def editar_tarefa(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    tarefa = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE id = :id

        """),

        {
            "id": id
        }

    ).fetchone()

    if not tarefa:

        flash(
            "Tarefa não encontrada.",
            "error"
        )

        return redirect("/tarefas")

    if request.method == "POST":

        dados = {

            "id": id,

            "titulo":
            request.form.get("titulo"),

            "descricao":
            request.form.get("descricao"),

            "prioridade":
            request.form.get("prioridade"),

            "responsavel":
            request.form.get("responsavel"),

            "setor":
            request.form.get("setor"),

            "prazo":
            request.form.get("prazo") or None

        }

        db.session.execute(

            db.text("""

                UPDATE tarefas

                SET

                    titulo = :titulo,
                    descricao = :descricao,
                    prioridade = :prioridade,
                    responsavel = :responsavel,
                    setor = :setor,
                    prazo = :prazo

                WHERE id = :id

            """),

            dados

        )

        responsavel_db = None

        if dados["responsavel"]:

            responsavel_db = db.session.execute(

                db.text("""

                    SELECT id

                    FROM usuarios

                    WHERE LOWER(nome) = LOWER(:nome)

                    LIMIT 1

                """),

                {
                    "nome": dados["responsavel"]
                }

            ).fetchone()

        if responsavel_db:

            criar_notificacao(

                usuario_id=responsavel_db.id,

                titulo="Tarefa atualizada",

                mensagem=f"A tarefa '{dados['titulo']}' foi atualizada por {usuario['nome']}.",

                tipo="kanban",

                link="/tarefas"

            )

        db.session.commit()

        flash(
            "Tarefa atualizada!",
            "success"
        )

        return redirect("/tarefas")

    return render_template(

        "editar_tarefa.html",

        usuario=usuario,

        tarefa=tarefa

    )

# =========================
# EXCLUIR TAREFA
# =========================

@app.route("/excluir_tarefa/<int:id>")
def excluir_tarefa(id):

    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    if usuario["tipo"] != "ti":
        return redirect("/")

    tarefa = db.session.execute(

        db.text("""

            SELECT *

            FROM tarefas

            WHERE id = :id

        """),

        {
            "id": id
        }

    ).fetchone()

    if not tarefa:

        flash(
            "Tarefa não encontrada.",
            "error"
        )

        return redirect("/tarefas")

    responsavel_db = None

    if tarefa.responsavel:

        responsavel_db = db.session.execute(

            db.text("""

                SELECT id

                FROM usuarios

                WHERE LOWER(nome) = LOWER(:nome)

                LIMIT 1

            """),

            {
                "nome": tarefa.responsavel
            }

        ).fetchone()

    if responsavel_db:

        criar_notificacao(

            usuario_id=responsavel_db.id,

            titulo="Tarefa excluída",

            mensagem=f"A tarefa '{tarefa.titulo}' foi excluída por {usuario['nome']}.",

            tipo="kanban",

            link="/tarefas"

        )

    db.session.execute(

        db.text("""

            DELETE FROM tarefas

            WHERE id = :id

        """),

        {
            "id": id
        }

    )

    db.session.commit()

    flash(
        "Tarefa excluída!",
        "success"
    )

    return redirect("/tarefas")

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

@app.route("/reset_admin")
def reset_admin():

    senha_hash = generate_password_hash("123")

    db.session.execute(db.text("""

        UPDATE usuarios
        SET senha = :senha
        WHERE nome = 'admin'

    """), {
        "senha": senha_hash
    })

    db.session.commit()

    return "Senha resetada!"

# =========================
# API INVENTÁRIO
# =========================
@app.route("/api/inventario")
def api_inventario():

    usuario = session.get("usuario")

    if not usuario:

        return {
            "erro": "Não autenticado"
        }, 401

    if usuario["tipo"] not in [
        "ti",
        "administracao"
    ]:

        return {
            "erro": "Sem permissão"
        }, 403

    dados = db.session.execute(

        db.text("""

            SELECT

                usuario_atual,
                id_maquina,
                marca,
                modelo,
                sistema_operacional,
                memoria_ram,
                armazenamento,
                setor,
                status,
                observacoes

            FROM ativos

            ORDER BY usuario_atual

        """)

    ).fetchall()

    inventario = {}

    for item in dados:

        chave = item.usuario_atual

        if not chave:

            chave = "SEM_USUARIO"

        if chave not in inventario:

            inventario[chave] = []

        inventario[chave].append({

            "patrimonio": item.id_maquina,
            "marca": item.marca,
            "modelo": item.modelo,
            "sistema_operacional": item.sistema_operacional,
            "memoria_ram": item.memoria_ram,
            "armazenamento": item.armazenamento,
            "setor": item.setor,
            "status": item.status,
            "observacoes": item.observacoes

        })

    return inventario

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
