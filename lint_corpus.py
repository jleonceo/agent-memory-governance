#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_corpus.py - Linter de salud de un corpus de memoria de agente.
Primera pieza del harness de gobernanza de memoria.

NO juzga si el contenido es VERDAD (eso es del arbitro/verificador, al admitir).
Solo revisa la FONTANERIA del corpus: enlaces [[...]] rotos, notas huerfanas,
punteros muertos en el indice, RAGs citados en skills que no existen, marcas STALE.

Uso:
  python lint_corpus.py --memory <dir_de_notas> [--rag <dir>] [--skills <dir>] [--index MEMORY.md]

Supuestos del corpus (el formato de memoria de Claude Code, adaptable):
  - cada nota es un .md con frontmatter YAML (campo opcional `name:` como slug)
  - las notas se enlazan entre si con wikilinks [[slug]]
  - hay un indice (MEMORY.md) con punteros markdown a las notas
  - (opcional) las skills declaran sus RAGs bajo un encabezado "RAG QUE DEBES CARGAR"

Sin dependencias externas. Solo lectura.
"""
import argparse, re, sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser(description="Lint de fontaneria de un corpus de memoria de agente")
ap.add_argument("--memory", required=True, help="directorio de las notas de memoria (.md)")
ap.add_argument("--index", default="MEMORY.md", help="nombre del fichero indice dentro de --memory")
ap.add_argument("--rag", default=None, help="(opcional) directorio de RAGs")
ap.add_argument("--skills", default=None, help="(opcional) directorio de skills (una carpeta por skill con SKILL.md)")
args = ap.parse_args()

MEMORY_DIR = Path(args.memory)
RAG_DIR    = Path(args.rag) if args.rag else None
SKILLS_DIR = Path(args.skills) if args.skills else None
INDEX_FILE = MEMORY_DIR / args.index

WIKILINK = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]*)?\]\]")
MDLINK   = re.compile(r"\]\(([^)]+?\.md)\)")
MD_NAME  = re.compile(r"`([A-Za-z0-9_./\\-]+\.md)`")
NAME_FM  = re.compile(r"^name:\s*(.+?)\s*$", re.M)

def read(p):
    try: return p.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def mtime(p):
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")

def strip_code(t):
    # quita bloques cercados ```...``` y codigo inline `...` para no confundir
    # un enlace real con uno citado como EJEMPLO entre comillas (p.ej. `[[A7]]`).
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t

mem_files = [p for p in MEMORY_DIR.glob("*.md") if p.name != INDEX_FILE.name]
# slugs validos = nombre de archivo (stem) + valor de 'name:' del frontmatter
valid = set()
for p in mem_files:
    valid.add(p.stem.lower())
    m = NAME_FM.search(read(p)[:400])
    if m: valid.add(m.group(1).strip().lower())

R = []
def out(s=""): R.append(s)

n_rag    = len(list(RAG_DIR.glob("*.md"))) if RAG_DIR else 0
n_skills = len(list(SKILLS_DIR.glob("*/SKILL.md"))) if SKILLS_DIR else 0
out("# Lint del corpus de memoria")
out(f"\nMemoria: {len(mem_files)} notas + {INDEX_FILE.name} - "
    f"RAG: {n_rag} ficheros - Skills: {n_skills}\n")
out("> Solo revisa fontaneria (estructura/enlaces). NO juzga si el contenido es verdad.\n")

# CHECK 1 - wikilinks rotos
broken, inbound = [], set()
for p in mem_files:
    for m in WIKILINK.finditer(strip_code(read(p))):
        t = m.group(1).strip()
        inbound.add(t.lower())
        if t.lower() not in valid:
            broken.append((p.name, t))
out("## 1. Wikilinks [[...]] que no resuelven a una nota existente")
out("> Pueden ser referencias a futuro intencionales (la nota aun no escrita). Revisar.")
if broken:
    for f, t in sorted(set(broken)):
        out(f"- `{f}` -> [[{t}]]")
    out(f"\n**{len(set(broken))} sin resolver.**")
else:
    out("Ninguno.")
out("")

# CHECK 2 - punteros del indice sin archivo
idx = read(INDEX_FILE)
idx_ref, idx_missing = set(), []
for m in MDLINK.finditer(idx):
    name = Path(m.group(1).replace("\\", "/")).name
    idx_ref.add(name[:-3].lower() if name.lower().endswith(".md") else name.lower())
    if not (MEMORY_DIR / name).exists():
        idx_missing.append(m.group(1))
out(f"## 2. Punteros de {INDEX_FILE.name} a archivos que no existen")
if idx_missing:
    for t in sorted(set(idx_missing)): out(f"- `{t}`")
    out(f"\n**{len(set(idx_missing))} punteros muertos.**")
else:
    out("Ninguno. OK")
out("")

# CHECK 3 - huerfanas
orphans = [p.name for p in mem_files
           if p.stem.lower() not in inbound and p.stem.lower() not in idx_ref]
out(f"## 3. Notas huerfanas (ni en el indice {INDEX_FILE.name} ni enlazadas por otra nota)")
if orphans:
    for f in sorted(orphans): out(f"- `{f}`")
    out(f"\n**{len(orphans)} huerfanas.**")
else:
    out("Ninguna. OK")
out("")

# CHECK 4 - RAGs citados en skills que no existen
if RAG_DIR and SKILLS_DIR:
    rag_files = {p.name.lower() for p in RAG_DIR.glob("*.md")}
    ABSPATH = re.compile(r"[A-Za-z]:[\\/][^\s`*\"']+?\.md")
    def rag_section(txt):
        m = re.search(r"#+\s*RAG QUE DEBES CARGAR(.*?)(?:\n#+\s|\n---|\Z)", txt, re.S | re.I)
        return m.group(1) if m else ""
    def resolve_rag(name, full_txt):
        # 1) en la carpeta canonica de RAGs
        if name.lower() in rag_files:
            return True
        # 2) ruta absoluta citada en la propia skill que EXISTA (RAG cross-repo, valido)
        for m in ABSPATH.finditer(full_txt):
            p = Path(m.group(0))
            if p.name.lower() == name.lower() and p.exists():
                return True
        return False
    rag_missing = []
    for sp in SKILLS_DIR.glob("*/SKILL.md"):
        full = read(sp)
        for m in MD_NAME.finditer(rag_section(full)):
            name = Path(m.group(1).replace("\\", "/")).name
            if name.lower() == "skill.md": continue
            if not resolve_rag(name, full):
                rag_missing.append((sp.parent.name, name))
    out("## 4. RAGs citados en una skill que no existen (ni en rag/ ni como ruta absoluta valida)")
    if rag_missing:
        for sk, name in sorted(set(rag_missing)):
            out(f"- skill `{sk}` cita `{name}` -> no esta en rag/")
        out(f"\n**{len(set(rag_missing))} sin resolver.**")
    else:
        out("Ninguno. OK")
else:
    out("## 4. RAGs citados en skills")
    out("Saltado (pasa --rag y --skills para activarlo).")
out("")

# CHECK 5 - STALE
stale = []
for base in [d for d in (RAG_DIR, MEMORY_DIR) if d]:
    for p in base.glob("*.md"):
        if re.search(r"\bSTALE\b", read(p)):
            stale.append((p.name, mtime(p)))
out("## 5. Ficheros con marca STALE (vigilar caducidad)")
if stale:
    for name, mt in sorted(set(stale)):
        out(f"- `{name}` (ult. modif. {mt})")
    out(f"\n**{len(set(stale))} marcados STALE.**")
else:
    out("Ninguno.")
out("")

out("---")
out("*lint_corpus.py - primera pieza del harness de gobernanza de memoria - solo fontaneria, NO verifica veracidad*")

text = "\n".join(R)
print(text)
outp = Path.cwd() / "lint_corpus_informe.md"
try:
    outp.write_text(text, encoding="utf-8")
    print(f"\n[Informe guardado en {outp}]")
except Exception as e:
    print(f"\n[No se pudo guardar: {e}]")
