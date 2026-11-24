"""
Migration: Evolucao editorial — consolidar cronica em posts.

Adiciona colunas resumo, subtitulo, status, atualizado_em na tabela posts.
Migra dados da tabela cronica para posts.
Dropa a tabela cronica.

Execute: docker exec postais-da-parnaiba-app python scripts/migrate_editorial.py
"""

import sys

from sqlalchemy import text

from app.database.session import SessionLocal


def migrate(session):
    # 1. Adicionar colunas novas na tabela posts
    new_columns = [
        ("resumo", "VARCHAR(500)"),
        ("subtitulo", "VARCHAR(255)"),
        ("status", "VARCHAR(20) NOT NULL DEFAULT 'draft'"),
        ("atualizado_em", "TIMESTAMPTZ"),
    ]

    for col_name, col_def in new_columns:
        try:
            session.execute(text(f"ALTER TABLE posts ADD COLUMN {col_name} {col_def}"))
            session.commit()
            print(f"  [OK] Coluna '{col_name}' adicionada em posts")
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print(f"  [SKIP] Coluna '{col_name}' ja existe em posts")
            else:
                print(f"  [ERRO] Coluna '{col_name}': {e}")
                return False

    # 2. Migrar dados da tabela cronica para posts
    cronica_rows = session.execute(text("SELECT * FROM cronica")).fetchall()
    if cronica_rows:
        print(f"\n  Migrando {len(cronica_rows)} cronica(s) para posts...")
        for row in cronica_rows:
            status = "published" if row.publicado else "draft"
            publicado_em = row.criado_em if row.publicado else None

            session.execute(
                text("""
                    INSERT INTO posts (titulo, slug, autor, categoria, conteudo,
                                       imagem_capa_url, publicado_em, criado_em,
                                       resumo, subtitulo, status, atualizado_em)
                    VALUES (:titulo, :slug, :autor, 'cronica', :conteudo,
                            :imagem_capa_url, :publicado_em, :criado_em,
                            :resumo, :subtitulo, :status, :atualizado_em)
                """),
                {
                    "titulo": row.titulo,
                    "slug": row.slug,
                    "autor": row.autor or "",
                    "conteudo": row.conteudo,
                    "imagem_capa_url": row.imagem_capa_url,
                    "publicado_em": publicado_em,
                    "criado_em": row.criado_em,
                    "resumo": row.resumo,
                    "subtitulo": row.subtitulo,
                    "status": status,
                    "atualizado_em": row.atualizado_em,
                },
            )
            print(f"    -> '{row.titulo}' migrado como {status}")
        session.commit()
    else:
        print("\n  Nenhuma cronica para migrar.")

    # 3. Atualizar posts existentes (que nao vieram de cronicas)
    session.execute(
        text("""
            UPDATE posts SET status = 'published'
            WHERE publicado_em IS NOT NULL AND status = 'draft'
        """)
    )
    session.commit()
    print("  [OK] Posts existentes com publicado_em atualizados para 'published'")

    # 4. Dropar a tabela cronica
    try:
        session.execute(text("DROP TABLE IF EXISTS cronica CASCADE"))
        session.commit()
        print("  [OK] Tabela 'cronica' removida")
    except Exception as e:
        session.rollback()
        print(f"  [ERRO] Ao dropar cronica: {e}")
        return False

    # 5. Validar resultado
    result = session.execute(text("SELECT COUNT(*) FROM posts")).scalar()
    print(f"\n  [VALIDACAO] Total de posts: {result}")

    rows = session.execute(
        text("SELECT id, titulo, status, publicado_em FROM posts")
    ).fetchall()
    for r in rows:
        print(
            f"    id={r.id} | {r.titulo} | status={r.status} "
            f"| publicado_em={r.publicado_em}"
        )

    return True


if __name__ == "__main__":
    print("=== Migration: Evolucao Editorial ===\n")
    with SessionLocal() as session:
        success = migrate(session)
    if success:
        print("\n=== Migration concluida com sucesso ===")
    else:
        print("\n=== Migration FALHOU ===")
        sys.exit(1)
