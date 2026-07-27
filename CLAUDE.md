# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Script único (`hive-to-markdown.py`) que busca posts de uma conta Hive ou Steemit via `beem`, baixa as imagens referenciadas e salva cada post como arquivo Markdown com front-matter YAML (title, date, permlink, categories, tags, author). Uso típico: arquivar/republicar conteúdo de blogs Hive/Steemit.

## Setup e execução

```bash
pip install -r requirements.txt

# Post de ontem (padrão) da conta no Hive
python hive-to-markdown.py <author> <output_path>

# Apenas o último post
python hive-to-markdown.py <author> <output_path> --last

# Todos os posts (ignora filtro de data)
python hive-to-markdown.py <author> <output_path> --all

# Posts de hoje
python hive-to-markdown.py <author> <output_path> --today

# Rede Steemit em vez de Hive
python hive-to-markdown.py <author> <output_path> --steemit

# Incluir posts marcados com tag 'actifit' (excluídos por padrão)
python hive-to-markdown.py <author> <output_path> --actifit
```

Não há testes, lint ou build configurados neste repositório.

## Arquitetura

Fluxo único em `main()` dentro de `hive-to-markdown.py`:

1. Conecta ao node RPC (`api.hive.blog` ou `api.steemit.com`) via `beem.Hive` + `beem.account.Account`.
2. Busca até 500 posts do blog da conta (`account.get_blog`) e filtra por data (ontem por padrão, ou `--today`/`--all`/`--last`) e por tag `actifit`.
3. Para cada post aprovado:
   - Coleta URLs de imagem de duas fontes: `json_metadata.image` e regex sobre o corpo Markdown (`extract_images_from_markdown`).
   - Baixa cada imagem (`download_image`) com nome único via `uuid4`, preservando a extensão original, e substitui a URL original pelo nome do arquivo local dentro do conteúdo.
   - Monta front-matter YAML (title sanitizado, date, permlink prefixado com `/hive/` ou `/steemit/`, categoria = primeira tag ou "General", lista de tags, author) e um rodapé com link para o post original.
   - Grava o arquivo em `<path>/<data>_<permlink>.md`.

Pontos a observar ao modificar:
- O parâmetro `platform` ("hive" ou "steemit") controla node RPC, prefixo de link (`https://{platform}.blog/...`), prefixo de permlink no front-matter e categoria extra (`Hive`/`Steemit`).
- `download_image` e `extract_images_from_markdown` não têm dependência do restante do fluxo — podem ser testados isoladamente.
- Erros de download de imagem são apenas logados (print) e não interrompem o processamento do post.
