--
-- PostgreSQL database dump
--

\restrict 9szS7ybwRuLSty0FPLRFc4amjzxVy5M4jihczR1WkBkLFksUfFQUNp0H67pm17g

-- Dumped from database version 17.9
-- Dumped by pg_dump version 17.9

-- Started on 2026-05-12 15:25:53

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 16451)
-- Name: ativos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ativos (
    id integer NOT NULL,
    id_maquina character varying(100) NOT NULL,
    marca character varying(100),
    modelo character varying(100),
    sistema_operacional character varying(100),
    memoria_ram character varying(100),
    armazenamento character varying(100),
    usuario_atual character varying(100),
    setor character varying(100),
    status character varying(50),
    observacoes text
);


ALTER TABLE public.ativos OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16450)
-- Name: ativos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ativos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ativos_id_seq OWNER TO postgres;

--
-- TOC entry 4964 (class 0 OID 0)
-- Dependencies: 219
-- Name: ativos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ativos_id_seq OWNED BY public.ativos.id;


--
-- TOC entry 230 (class 1259 OID 16508)
-- Name: chamado_tecnicos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chamado_tecnicos (
    id integer NOT NULL,
    chamado_id integer,
    tecnico character varying(120)
);


ALTER TABLE public.chamado_tecnicos OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16507)
-- Name: chamado_tecnicos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chamado_tecnicos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chamado_tecnicos_id_seq OWNER TO postgres;

--
-- TOC entry 4965 (class 0 OID 0)
-- Dependencies: 229
-- Name: chamado_tecnicos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chamado_tecnicos_id_seq OWNED BY public.chamado_tecnicos.id;


--
-- TOC entry 222 (class 1259 OID 16462)
-- Name: chamados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chamados (
    id integer NOT NULL,
    colaborador character varying(100),
    descricao text,
    setor character varying(100),
    maquina character varying(100),
    status character varying(50),
    categoria character varying(50),
    solucao text,
    data_abertura timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    id_maquina character varying(50)
);


ALTER TABLE public.chamados OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16461)
-- Name: chamados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chamados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chamados_id_seq OWNER TO postgres;

--
-- TOC entry 4966 (class 0 OID 0)
-- Dependencies: 221
-- Name: chamados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chamados_id_seq OWNED BY public.chamados.id;


--
-- TOC entry 228 (class 1259 OID 16499)
-- Name: mapa_posicoes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mapa_posicoes (
    id integer NOT NULL,
    sala character varying(100),
    posicao character varying(50),
    maquina character varying(50),
    colaborador character varying(150)
);


ALTER TABLE public.mapa_posicoes OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16498)
-- Name: mapa_posicoes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mapa_posicoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mapa_posicoes_id_seq OWNER TO postgres;

--
-- TOC entry 4967 (class 0 OID 0)
-- Dependencies: 227
-- Name: mapa_posicoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mapa_posicoes_id_seq OWNED BY public.mapa_posicoes.id;


--
-- TOC entry 224 (class 1259 OID 16472)
-- Name: mensagens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mensagens (
    id integer NOT NULL,
    chamado_id integer,
    usuario character varying(100),
    mensagem text,
    arquivo text,
    data_envio timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.mensagens OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16471)
-- Name: mensagens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mensagens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mensagens_id_seq OWNER TO postgres;

--
-- TOC entry 4968 (class 0 OID 0)
-- Dependencies: 223
-- Name: mensagens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mensagens_id_seq OWNED BY public.mensagens.id;


--
-- TOC entry 226 (class 1259 OID 16487)
-- Name: tecnicos_chamado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tecnicos_chamado (
    id integer NOT NULL,
    chamado_id integer,
    tecnico character varying(100)
);


ALTER TABLE public.tecnicos_chamado OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16486)
-- Name: tecnicos_chamado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tecnicos_chamado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tecnicos_chamado_id_seq OWNER TO postgres;

--
-- TOC entry 4969 (class 0 OID 0)
-- Dependencies: 225
-- Name: tecnicos_chamado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tecnicos_chamado_id_seq OWNED BY public.tecnicos_chamado.id;


--
-- TOC entry 218 (class 1259 OID 16444)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    tipo character varying(30) NOT NULL,
    senha character varying(255),
    setor character varying(100),
    email character varying(200)
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16443)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 4970 (class 0 OID 0)
-- Dependencies: 217
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 4773 (class 2604 OID 16454)
-- Name: ativos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ativos ALTER COLUMN id SET DEFAULT nextval('public.ativos_id_seq'::regclass);


--
-- TOC entry 4780 (class 2604 OID 16511)
-- Name: chamado_tecnicos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chamado_tecnicos ALTER COLUMN id SET DEFAULT nextval('public.chamado_tecnicos_id_seq'::regclass);


--
-- TOC entry 4774 (class 2604 OID 16465)
-- Name: chamados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chamados ALTER COLUMN id SET DEFAULT nextval('public.chamados_id_seq'::regclass);


--
-- TOC entry 4779 (class 2604 OID 16502)
-- Name: mapa_posicoes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapa_posicoes ALTER COLUMN id SET DEFAULT nextval('public.mapa_posicoes_id_seq'::regclass);


--
-- TOC entry 4776 (class 2604 OID 16475)
-- Name: mensagens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mensagens ALTER COLUMN id SET DEFAULT nextval('public.mensagens_id_seq'::regclass);


--
-- TOC entry 4778 (class 2604 OID 16490)
-- Name: tecnicos_chamado id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos_chamado ALTER COLUMN id SET DEFAULT nextval('public.tecnicos_chamado_id_seq'::regclass);


--
-- TOC entry 4772 (class 2604 OID 16447)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4948 (class 0 OID 16451)
-- Dependencies: 220
-- Data for Name: ativos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ativos (id, id_maquina, marca, modelo, sistema_operacional, memoria_ram, armazenamento, usuario_atual, setor, status, observacoes) FROM stdin;
1	76	Acer	Acer Aspire 3 A314-35	W11 HOME	8 GB RAM	256 GB SSD	Rosane Moraes	BackOffice	\N	\N
2	39	Asus	X515JA	W11 HOME	8 GB RAM	256 GB SSD	Fátima Figueiredo	BackOffice	\N	\N
3	70	Samsung	NP550XED-KT4BR	W11 HOME	8 GB RAM	256 GB SSD	Bruno Mendes	BackOffice	\N	\N
4	56	Samsung	NP550XDA	W11 HOME	4 GB RAM	256 GB SSD	Raysa Oliveira	BackOffice	\N	\N
5	52	HP	HP 250 G8	W11 PRO	8 GB RAM	256 GB SSD	Clara Albuquerque	BackOffice	\N	\N
6	80	Lenovo	IdeaPad 1 15IAU7	W11 HOME	8 GB RAM	256 GB SSD	Steffanie Ycaza	BackOffice	\N	\N
7	79	Acer	Acer Aspire Go 15 AG15-71P	W11 HOME	8 GB RAM	512 GB SSD	Igor Guedes	BackOffice	\N	\N
8	PC 01-15 (D19)	DELL	Optiplex 3070	W11 PRO	16 GB RAM	256 GB SSD	Natália Soares	BL	\N	\N
9	PC 02-15 (D16)	DELL	Optiplex 3070	W11 PRO	16 GB RAM	256 GB SSD	Yasmin Vieira	BL	\N	\N
10	PC 03-15 (D18)	DELL	Optiplex 3070	W10 PRO	8 GB RAM	240 GB SSD	Vago	BL	\N	\N
11	PC 04-15 (D14)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Graziele Costa	BL	\N	\N
12	PC 05-15 (D17)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	256 GB SSD	Lara Matos	BL	\N	\N
13	PC 06-15 (D13)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Rayssa Souza	BL	\N	\N
14	PC 07-15 (D15)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Agatha Amaral	BL	\N	\N
15	PC 08-15 (L20)	LENOVO	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	256 GB SSD	Harissa Oliveira	BL	\N	\N
16	PC 01-16 (L19)	LENOVO	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Rosiene Santos	BL	\N	\N
17	PC 02-16 (L18)	LENOVO	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Dandarah Alves	BL	\N	\N
18	PC 03-16 (D12)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Luciane Rocha	BL	\N	\N
19	PC 04-16 (L17)	LENOVO	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Ludmila Santos	BL	\N	\N
20	PC 05-16 (D11)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Tayná Gomes	BL	\N	\N
21	PC 06-16 (D10)	DELL	Optiplex 3070	W10 PRO	8 GB RAM	240 GB SSD	Vago	BL	\N	\N
22	PC 07-16 (N/A)	nan	nan	nan	nan	nan	(N/A)	BL	\N	\N
23	PC 08-16 (D09)	DELL	Optiplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Vago	BL	\N	\N
24	Notebook 49	ASUS	X515J	W10 HOME	8 GB RAM	256 GB SSD	Gracielle  Monteiro	BL	\N	\N
25	Notebook 50	ASUS	X515J	W10 PRO	8 GB RAM	256 GB SSD	Thaiane Cerqueira	BL	\N	\N
26	43	ASUS	X515J	W11 HOME	4 GB RAM	256 GB SSD	Larissa Nascimento	Farmer	\N	\N
27	34	ASUS	X515J	W11 HOME	8 GB RAM	256 GB SSD	Fabiana Soares	Farmer	\N	\N
28	58	Samsung	NP550XDA-KP3BR	W11 HOME	4 GB RAM	256 GB SSD	Marianna Lisboa	Farmer	\N	\N
29	40	ASUS	X515J	W11 HOME	8 GB RAM	256 GB SSD	Joyce Ramos	Farmer	\N	\N
30	53	ASUS	X515J	W11 HOME	8 GB RAM	256 GB SSD	Reinaldo Silva	Farmer	\N	\N
31	33	ASUS	X515J	W11 HOME	8 GB RAM	256 GB SSD	Yasmin Fernandes	Farmer	\N	\N
32	71	Samsung	NP550XED-KT4BR	W11 HOME	8 GB RAM	256 GB SSD	nan	Farmer	\N	\N
33	68	Samsung	NP550XED-KT4BR	W11 HOME	8 GB RAM	256 GB SSD	Natalia Weydtt	Farmer	\N	\N
34	51	ASUS	X515J	W11 HOME	4 GB RAM	256 GB SSD	Leticia Pinheiro	Farmer	\N	\N
35	36	ASUS	X515J	W11 HOME	4 GB RAM	128 GB SSD	Amanda Costa	Farmer	\N	\N
36	47	ASUS	X515J	W11 HOME 	4 GB RAM	256 GB SSD	Melissa Siqueira	Farmer	\N	\N
37	67	Samsung	NP550XED-KT4BR	W11 HOME 	8 GB RAM	256 GB SSD	Leticia Carvalho	Farmer	\N	\N
38	77	Acer	Aspire 3 A315-510P	W11 HOME 	8 GB RAM	256 GB SSD	Thamires Vaz	Farmer	\N	\N
39	61	Acer	Aspire 3 A314-35	W11 PRO EDUCATION	12 GB RAM	128 GB SSD	Cinthia Souza	Farmer	\N	\N
40	45	ASUS	X515J	W11 HOME 	4 GB RAM	256 GB SSD	Juliana Torres	Farmer	\N	\N
41	1 (D08)	Dell	Opitplex 3070	W11 PRO	16 GB RAM	256 GB SSD	Michelle Torres	Hunter	\N	\N
42	3 (L16)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Gabrielly Fernandes	Hunter	\N	\N
43	5 (L15)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	16 GB RAM	240 GB SSD	Bianca Oliveira	Hunter	\N	\N
44	7 (L14)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Amanda Silva	Hunter	\N	\N
45	9 (L13)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Lorrayne Martins	Hunter	\N	\N
46	11 (L12)	Lenovo	Lenovo ThinkCentre Tiny	W11 PRO	8 GB RAM	240 GB SSD	Marcelly Valente	Hunter	\N	\N
47	2 (D07)	Dell	Opitplex 3070	W10 PRO	8 GB RAM	256 GB SSD	Ane Soares	Hunter	\N	\N
48	4 (L07)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	256 GB SSD	Julia Faria	Hunter	\N	\N
49	6 (L08)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Tauane Esteves	Hunter	\N	\N
50	8 (L09)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Sarah Silva (F)	Hunter	\N	\N
51	10 (L10)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Suzy Valério	Hunter	\N	\N
52	12 (L11)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Thayana Bernado	Hunter	\N	\N
53	13 (D04)	Dell	Opitplex 3040	W11 PRO	12 GB RAM	240 GB SSD	Thaina Santana	Hunter	\N	\N
54	15 (D05)	Dell	Opitplex 3040	W10 PRO	8 GB RAM	256 GB SSD	Giovanna Velozo	Hunter	\N	\N
55	17 (L04)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	256 GB SSD	Vitória Reis	Hunter	\N	\N
56	19 (L05)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	256 GB SSD	Rayssa Nogueira (F)	Hunter	\N	\N
57	21 (D06)	Dell	Opitplex 3070	W10 PRO	8 GB RAM	256 GB SSD	Carolina Palma	Hunter	\N	\N
58	23 (L06)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Lanna Oliveira	Hunter	\N	\N
59	14 (D01)	Dell	Opitplex 3070	W11 PRO	8 GB RAM	240 GB SSD	Thayna Mendes	Hunter	\N	\N
60	16 (L01)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Kézia Alves	Hunter	\N	\N
61	18 (D02)	Dell	Opitplex 3050	W11 PRO	8 GB RAM	256 GB SSD	Priscila Alburquerque	Hunter	\N	\N
62	20 (D03)	Dell	Opitplex 3050	W11 PRO	8 GB RAM	240 GB SSD	Rebeca Mota	Hunter	\N	\N
63	22(L02)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	240 GB SSD	Mariana Neves	Hunter	\N	\N
64	24 (L03)	Lenovo	Lenovo ThinkCentre Tiny	W10 PRO	8 GB RAM	256 GB SSD	Nathallya Costa	Hunter	\N	\N
65	64	Samsung	Galaxy Book	W10 HOME	8 GB RAM	256 GB SSD	Mariana Queiroz	Hunter	\N	\N
66	78	Acer	Aspire 3 A315	W10 HOME	8 GB RAM	256 GB SSD	Yasmin Almeida	Hunter	\N	\N
67	42	ASUS	X515J	W11 HOME	8 GB RAM	256 GB SSD	Carla Cardoso	Hunter	\N	\N
\.


--
-- TOC entry 4958 (class 0 OID 16508)
-- Dependencies: 230
-- Data for Name: chamado_tecnicos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chamado_tecnicos (id, chamado_id, tecnico) FROM stdin;
\.


--
-- TOC entry 4950 (class 0 OID 16462)
-- Dependencies: 222
-- Data for Name: chamados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chamados (id, colaborador, descricao, setor, maquina, status, categoria, solucao, data_abertura, id_maquina) FROM stdin;
\.


--
-- TOC entry 4956 (class 0 OID 16499)
-- Dependencies: 228
-- Data for Name: mapa_posicoes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mapa_posicoes (id, sala, posicao, maquina, colaborador) FROM stdin;
1	Hunter	PC 01	D08	\N
2	Hunter	PC 02	D07	\N
3	Hunter	PC 03	L16	\N
4	Hunter	PC 04	L07	\N
5	Hunter	PC 05	L15	\N
6	Hunter	PC 06	L08	\N
7	Hunter	PC 07	L14	\N
8	Hunter	PC 08	L09	\N
9	Hunter	PC 09	L13	\N
10	Hunter	PC 10	L10	\N
11	Hunter	PC 11	L12	\N
12	Hunter	PC 12	L11	\N
13	Hunter	PC 13	D04	\N
15	Hunter	PC 15	D05	\N
16	Hunter	PC 16	L01	\N
17	Hunter	PC 17	L04	\N
18	Hunter	PC 18	D02	\N
19	Hunter	PC 19	L05	\N
20	Hunter	PC 20	D03	\N
21	Hunter	PC 21	L06	\N
22	Hunter	PC 22	L02	\N
23	Hunter	PC 23	L06	\N
24	Hunter	PC 24	L03	\N
25	Hunter	NOTEBOOK 64	NOTEBOOK 64	\N
26	Hunter	NOTEBOOK 42	NOTEBOOK 42	\N
27	Hunter	NOTEBOOK 78	NOTEBOOK 78	\N
28	BL	PC 01	BL01	\N
29	BL	PC 02	BL02	\N
30	BL	PC 03	BL03	\N
31	BL	PC 04	BL04	\N
32	BL	PC 05	BL05	\N
33	BL	PC 06	BL06	\N
34	BL	PC 07	BL07	\N
35	BL	PC 08	BL08	\N
36	BL	PC 09	BL09	\N
37	BL	PC 10	BL10	\N
38	BL	PC 11	BL11	\N
39	BL	PC 12	BL12	\N
40	BL	PC 13	BL13	\N
42	BL	PC 15	BL15	\N
43	BL	PC 16	BL16	\N
44	BL	NOTEBOOK 01	NOTEBOOK 01	\N
45	BL	NOTEBOOK 02	NOTEBOOK 02	\N
46	BL	1016 - PC 01	L19	\N
47	BL	1016 - PC 02	L18	\N
48	BL	1016 - PC 03	D12	\N
49	BL	1016 - PC 04	L17	\N
50	BL	1016 - PC 05	D11	\N
51	BL	1016 - PC 06	D10	\N
52	BL	1016 - PC 07	\N	\N
53	BL	1016 - PC 08	D09	\N
56	BL	1015 - PC 03	D18	\N
57	BL	1015 - PC 04	D14	\N
58	BL	1015 - PC 05	D17	\N
59	BL	1015 - PC 06	D13	\N
60	BL	1015 - PC 07	D15	\N
61	BL	1015 - PC 08	L20	\N
62	BL	NOTEBOOK 49	NOTEBOOK 49	\N
55	BL	1015 - PC 02	D16	
54	BL	1015 - PC 01	D19	Natália Soares
63	BL	NOTEBOOK 50	NOTEBOOK 50	teste
14	Hunter	PC 14	D01	teste
41	BL	PC 14	D01	teste
\.


--
-- TOC entry 4952 (class 0 OID 16472)
-- Dependencies: 224
-- Data for Name: mensagens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mensagens (id, chamado_id, usuario, mensagem, arquivo, data_envio) FROM stdin;
\.


--
-- TOC entry 4954 (class 0 OID 16487)
-- Dependencies: 226
-- Data for Name: tecnicos_chamado; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tecnicos_chamado (id, chamado_id, tecnico) FROM stdin;
\.


--
-- TOC entry 4946 (class 0 OID 16444)
-- Dependencies: 218
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nome, tipo, senha, setor, email) FROM stdin;
1	Gabriel	ti	123	TI	\N
2	Marcelo	ti	123	TI	\N
3	Sabrina	administracao	123	Administrativo	\N
4	joao	colaborador	123	Financeiro	\N
\.


--
-- TOC entry 4971 (class 0 OID 0)
-- Dependencies: 219
-- Name: ativos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ativos_id_seq', 67, true);


--
-- TOC entry 4972 (class 0 OID 0)
-- Dependencies: 229
-- Name: chamado_tecnicos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chamado_tecnicos_id_seq', 1, false);


--
-- TOC entry 4973 (class 0 OID 0)
-- Dependencies: 221
-- Name: chamados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chamados_id_seq', 1, false);


--
-- TOC entry 4974 (class 0 OID 0)
-- Dependencies: 227
-- Name: mapa_posicoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mapa_posicoes_id_seq', 63, true);


--
-- TOC entry 4975 (class 0 OID 0)
-- Dependencies: 223
-- Name: mensagens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mensagens_id_seq', 1, false);


--
-- TOC entry 4976 (class 0 OID 0)
-- Dependencies: 225
-- Name: tecnicos_chamado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tecnicos_chamado_id_seq', 1, false);


--
-- TOC entry 4977 (class 0 OID 0)
-- Dependencies: 217
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 5, true);


--
-- TOC entry 4784 (class 2606 OID 16460)
-- Name: ativos ativos_id_maquina_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ativos
    ADD CONSTRAINT ativos_id_maquina_key UNIQUE (id_maquina);


--
-- TOC entry 4786 (class 2606 OID 16458)
-- Name: ativos ativos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ativos
    ADD CONSTRAINT ativos_pkey PRIMARY KEY (id);


--
-- TOC entry 4796 (class 2606 OID 16513)
-- Name: chamado_tecnicos chamado_tecnicos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chamado_tecnicos
    ADD CONSTRAINT chamado_tecnicos_pkey PRIMARY KEY (id);


--
-- TOC entry 4788 (class 2606 OID 16470)
-- Name: chamados chamados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_pkey PRIMARY KEY (id);


--
-- TOC entry 4794 (class 2606 OID 16504)
-- Name: mapa_posicoes mapa_posicoes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapa_posicoes
    ADD CONSTRAINT mapa_posicoes_pkey PRIMARY KEY (id);


--
-- TOC entry 4790 (class 2606 OID 16480)
-- Name: mensagens mensagens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mensagens
    ADD CONSTRAINT mensagens_pkey PRIMARY KEY (id);


--
-- TOC entry 4792 (class 2606 OID 16492)
-- Name: tecnicos_chamado tecnicos_chamado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos_chamado
    ADD CONSTRAINT tecnicos_chamado_pkey PRIMARY KEY (id);


--
-- TOC entry 4782 (class 2606 OID 16449)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4799 (class 2606 OID 16514)
-- Name: chamado_tecnicos chamado_tecnicos_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chamado_tecnicos
    ADD CONSTRAINT chamado_tecnicos_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id) ON DELETE CASCADE;


--
-- TOC entry 4797 (class 2606 OID 16481)
-- Name: mensagens mensagens_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mensagens
    ADD CONSTRAINT mensagens_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id);


--
-- TOC entry 4798 (class 2606 OID 16493)
-- Name: tecnicos_chamado tecnicos_chamado_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tecnicos_chamado
    ADD CONSTRAINT tecnicos_chamado_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id);


-- Completed on 2026-05-12 15:25:53

--
-- PostgreSQL database dump complete
--

\unrestrict 9szS7ybwRuLSty0FPLRFc4amjzxVy5M4jihczR1WkBkLFksUfFQUNp0H67pm17g

