# Postais da Parnaiba API

Backend FastAPI para o site **Postais da Parnaiba**, um museu digital de fotos
historicas com conteudo editorial.

## Stack

- FastAPI
- PostgreSQL + SQLAlchemy
- Pydantic v2
- Poetry
- Ruff
- Taskipy
- Pytest

## Setup

```bash
cp .env.example .env
poetry install
poetry shell
```

Edite o `DATABASE_URL` no `.env` para apontar para seu PostgreSQL.

Crie um administrador:

```bash
python scripts/create_admin.py
```

Rode a API:

```bash
task dev
```

A documentacao interativa fica em:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Tasks

```bash
task dev     # inicia o servidor local
task lint    # roda ruff check
task format  # formata com ruff format
task test    # roda pytest
```

## Autenticacao

Login:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua-senha"}'
```

Use o token retornado nas rotas administrativas:

```bash
Authorization: Bearer SEU_TOKEN
```

## Exemplos de rotas

Criar postal:

```bash
curl -X POST http://127.0.0.1:8000/postais \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Porto das Barcas",
    "descricao": "Registro historico do Porto das Barcas.",
    "imagem_url": "https://example.com/porto.jpg",
    "epoca": "Anos 1940",
    "localizacao": "Parnaiba, PI"
  }'
```

Listar postais:

```bash
curl "http://127.0.0.1:8000/postais?page=1&size=10"
```

Criar post:

```bash
curl -X POST http://127.0.0.1:8000/posts \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "A Parnaiba antiga",
    "autor": "Equipe editorial",
    "categoria": "cronica",
    "conteudo": "# Memoria\nTexto em markdown.",
    "imagem_capa_url": "https://example.com/capa.jpg",
    "publicado_em": "2026-06-10T12:00:00Z"
  }'
```

Listar posts por categoria:

```bash
curl "http://127.0.0.1:8000/posts?categoria=cronica&page=1&size=10"
```

Upload de imagem:

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "file=@foto.jpg"
```

## Categorias de posts

- `cronica`
- `noticia`
- `manchete`
- `estudo`

## Deploy (VPS com Docker)

O frontend deve ficar em `../Postais-da-Parnaiba` (ao lado deste diretório), pois
o nginx o serve como arquivos estáticos.

```bash
# 1. Clone os dois repositórios como diretórios irmãos
mkdir -p /opt/postais && cd /opt/postais
git clone <URL_DO_BACKEND> Backend-Postais_da_Parnaiba
git clone <URL_DO_FRONTEND> Postais-da-Parnaiba

# 2. Entre no backend e rode o deploy
cd Backend-Postais_da_Parnaiba
bash deploy.sh                 # HTTP (por IP)
# ou
bash deploy.sh seudominio.com  # HTTPS com Let's Encrypt
```

O `deploy.sh` cria o `.env`, gera `SECRET_KEY` e `POSTGRES_PASSWORD`, pede a
senha do admin e configura o SSL quando um domínio é informado.

Verificações úteis:

```bash
curl http://localhost/api/health   # {"status":"ok"}
make logs                          # logs dos containers
make status                        # status dos containers
```
