# agent-memory-governance

[Español](#español) · [English](#english)

---

## Español

Tres piezas pequeñas para que la memoria persistente de un agente de IA no se convierta
en un vertedero. Salen de un sistema en uso real: unas 100 notas acumuladas en dos meses
de trabajo diario con Claude Code.

### El problema explicado desde cero

Si trabajas a diario con un agente de IA, tarde o temprano querrás que **recuerde**: las
decisiones que tomasteis, los errores que ya cometió una vez, las reglas de tu proyecto.
La forma habitual de conseguirlo es darle memoria persistente: ficheros de texto que el
agente lee al arrancar y va escribiendo mientras trabaja.

Guardar es la parte fácil. Lo que casi nadie cuenta es que **esa memoria se pudre**. Y se
pudre de tres formas distintas:

1. **Fontanería rota.** Notas que enlazan a notas que ya no existen, notas huérfanas que
   nada referencia, índices que apuntan a ficheros borrados. El agente sigue el enlace y
   encuentra el vacío.
2. **Caducidad.** Cosas que fueron verdad y dejaron de serlo: la cifra de hace un mes, la
   ruta que cambió, la decisión que se revirtió. La nota sigue ahí, escrita con la misma
   seguridad que el primer día.
3. **Falsedad consistente.** La peor: una nota bien escrita y bien enlazada... y falsa.
   Pasa cualquier comprobación de forma, y el agente la consultará con total confianza,
   porque la memoria propia no se cuestiona.

El almacenamiento está resuelto: hay patrones públicos de sobra para *guardar* memoria
de agente. Lo que no encontré en ningún sitio es la **gobernanza**: quién vigila lo
guardado, cómo se detecta lo podrido, y qué entra y qué no. Esto es lo que construí.

### Las tres piezas

#### 1. El linter de fontanería ([lint_corpus.py](lint_corpus.py))

Un script de Python sin dependencias que revisa la estructura del corpus: wikilinks
`[[...]]` que no resuelven, punteros del índice a ficheros que no existen, notas huérfanas,
referencias de las skills a documentos ausentes, y marcas `STALE` (contenido señalado como
sensible a quedarse obsoleto).

```
python lint_corpus.py --memory <dir_de_notas> [--rag <dir>] [--skills <dir>]
```

Escribe además un informe en `lint_corpus_informe.md` en el directorio actual. No juzga si
el contenido es verdad, solo si la estructura se sostiene. Es deliberado:
una comprobación barata que se puede ejecutar a diario encuentra la podredumbre de
tipo 1 antes de que el agente tropiece con ella.

#### 2. El rastro del log automático ([hooks/log_memoria.ps1](hooks/log_memoria.ps1))

Un hook de Claude Code (PostToolUse) que añade una línea a un `log.md` append-only cada
vez que el agente crea o modifica una nota. Fecha, operación, fichero, descripción.

El formato importa poco. Lo que vale es que **no depende de la disciplina de nadie**, ni
del humano ni del agente: se dispara solo, en cada escritura del agente con sus herramientas
Write y Edit (una edición hecha a mano fuera del agente no queda registrada). Cuando algo
aparece mal en la memoria, el log te dice cuándo entró y qué decía. Sin rastro, una nota corrupta es un
misterio; con rastro, es un diff.

#### 3. Las citas de origen ([docs/convencion_citations.md](docs/convencion_citations.md))

Una convención: cada nota termina diciendo **quién la verificó, contra qué fuente, y si
la comprobación se puede re-ejecutar hoy**. Una nota re-ejecutable se defiende sola; una
sin fuente depende de la fe. El documento explica el formato y el porqué, con ejemplo real.

### Lo que estas piezas NO cazan (y conviene decirlo claro)

El lint caza la inconsistencia, pero no la **falsedad consistente**: una mentira bien
formateada pasa el lint, queda registrada con su fecha y hasta puede llevar un bloque
de citas impecable.

Las tres piezas resuelven la podredumbre de tipo 1, acotan la de tipo 2 (marcas STALE +
citas con fecha) y dejan la de tipo 3 señalada pero no resuelta. Para cazar una falsedad
consistente hace falta algo más caro: **verificar la afirmación contra la fuente primaria
de su dominio**, es decir, ejecutar la consulta o lanzar el test de nuevo. Eso es la
cuarta pieza. Y la cuarta pieza está congelada a propósito.

### Por qué la cuarta pieza está congelada

El diseño existe: un **árbitro de admisión** con interfaz genérica
(`dominio + afirmación + evidencia → ADMITIR / RECHAZAR / ADMITIR_DEGRADADO + razón`),
enchufable por dominio. En mi caso, el dominio contable verificaría contra MySQL; otros
dominios enchufarían su propia fuente de verdad.

Lo congelé antes de construirlo. Al revisar el camino completo encontré dos cosas:

1. De ~100 notas del corpus real, solo 15-20 tenían riesgo real de admisión. El problema
   que el árbitro ataca es más pequeño de lo que parecía desde dentro.
2. El problema original (que la información correcta *llegue* al agente en el momento
   de necesidad, la recuperación) seguía sin tocar. Estaba a punto de construir la cuarta
   pieza de admisión teniendo cero piezas de recuperación.

Construir el árbitro habría sido seguir por inercia: el siguiente paso del plan, no el
siguiente paso del problema. La regla que me apliqué es la misma que gobierna las notas:
**la gobernanza también se aplica al roadmap**. Se descongela el día que haya evidencia
de que el método manual (verificar al usar, no al guardar) no basta.

### De dónde sale esto

Del proyecto TechAcces: una empresa ficticia con contabilidad real (~17.000 líneas de
diario en MySQL) sobre la que desarrollo enjambres de agentes Claude con evaluación
continua. Dos meses de sesiones diarias generan mucha memoria, y los problemas de arriba
no son hipotéticos: los tres tipos de podredumbre aparecieron de verdad.

Una anécdota que resume el espíritu: en su primera pasada sobre el corpus real, el linter
reportó dos problemas... que eran **fallos del propio linter** (no entendía referencias
legítimas entre repositorios y marcaba como rotos los enlaces citados como ejemplo dentro
de código). Se corrigió el linter, no el corpus. La herramienta de vigilancia también se
vigila: nada se da por bueno sin comprobar, tampoco el verificador.

Más que un framework, esto son tres piezas pequeñas y un criterio. Cópialas y adáptalas
a tu corpus. Y quédate con la pregunta que las origina: *¿quién vigila lo que tu agente
recuerda?*

### Relación con otros proyectos

Este harness es una pieza de un trabajo más amplio sobre sistemas con varios agentes. Las piezas hermanas:

- [claude-code-context-management](https://github.com/jleonceo/claude-code-context-management): la hermana directa de este repo. Aquí se gobierna *qué* recuerda el agente; allí, *cuánto* de eso se carga cada sesión, para que los ficheros de contexto (CLAUDE.md y MEMORY.md) no saturen el contexto.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): la misma filosofía (medir antes de confiar) aplicada a una skill, qué es y cómo se examina.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): el sistema cuyo conocimiento gobierna este harness, con sus caídas explicadas.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): las cinco reglas para gobernar skills, cada una con su cicatriz real.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): el enrutado multi-agente, a qué agente va cada petición sin romper al crecer.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): la coherencia del estado comprobada por pura aritmética, sin IA.
- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): qué es un asistente de IA, para quien empieza de cero.
- [tesoreria-forecast-ia](https://github.com/jleonceo/tesoreria-forecast-ia): previsión de caja por descomposición con backtesting, más ratios y aging.
- [control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia): detección de fraude contable con aritmética, dentro de un marco de control interno.

---

## English

Three small pieces to keep an AI agent's persistent memory from turning into a junkyard.
They come from a system in real use: around 100 notes accumulated over two months of daily
work with Claude Code.

### The problem from scratch

If you work daily with an AI agent, sooner or later you will want it to **remember**: the
decisions you made together, the mistakes it already made once, your project's rules. The
usual way to get that is to give it persistent memory: text files the agent reads on startup
and writes to as it works.

Saving is the easy part. What almost nobody tells you is that **that memory rots**. And it
rots in three different ways:

1. **Broken plumbing.** Notes that link to notes that no longer exist, orphan notes that
   nothing references, indexes pointing at deleted files. The agent follows the link and
   finds the void.
2. **Staleness.** Things that were true and stopped being true: last month's figure, the
   path that changed, the decision that was reverted. The note is still there, written with
   the same confidence as day one.
3. **Consistent falsehood.** The worst: a well-written, well-linked note... and false. It
   passes any formal check, and the agent will consult it with full confidence, because one's
   own memory is not questioned.

Storage is solved: there are plenty of public patterns to *save* agent memory. What I did not
find anywhere is the **governance**: who watches what is stored, how the rot is detected, and
what gets in and what does not. That is what I built.

### The three pieces

#### 1. The plumbing linter ([lint_corpus.py](lint_corpus.py))

A dependency-free Python script that checks the corpus structure: `[[...]]` wikilinks that do
not resolve, index pointers to files that do not exist, orphan notes, skill references to
missing documents, and `STALE` markers (content flagged as prone to going out of date).

```
python lint_corpus.py --memory <notes_dir> [--rag <dir>] [--skills <dir>]
```

It also writes a report to `lint_corpus_informe.md` in the current directory. It does not judge
whether the content is true, only whether the structure holds. That is deliberate: a cheap
check you can run daily finds type-1 rot before the agent trips over it.

#### 2. The trail from the automatic log ([hooks/log_memoria.ps1](hooks/log_memoria.ps1))

A Claude Code hook (PostToolUse) that appends a line to an append-only `log.md` every time the
agent creates or modifies a note. Date, operation, file, description.

The format matters little. What counts is that it **does not depend on anyone's discipline**,
neither the human's nor the agent's: it fires on its own, on every write the agent makes with
its Write and Edit tools (an edit made by hand outside the agent is not logged). When something
looks wrong in memory, the log tells you when it entered and what it said. Without a trail, a
corrupt note is a mystery; with a trail, it is a diff.

#### 3. The origin citations ([docs/convencion_citations.md](docs/convencion_citations.md))

A convention: each note ends by saying **who verified it, against what source, and whether the
check can be re-run today**. A re-runnable note defends itself; one without a source depends on
faith. The document explains the format and the why, with a real example.

### What these pieces do NOT catch (and it is worth saying plainly)

The lint catches inconsistency, but not **consistent falsehood**: a well-formatted lie passes
the lint, gets logged with its date, and can even carry a flawless citations block.

The three pieces solve type-1 rot, contain type-2 (STALE markers + dated citations) and leave
type-3 flagged but unsolved. To catch a consistent falsehood you need something more expensive:
**verify the claim against the primary source of its domain**, that is, run the query or launch
the test again. That is the fourth piece. And the fourth piece is frozen on purpose.

### Why the fourth piece is frozen

The design exists: an **admission arbiter** with a generic interface
(`domain + claim + evidence -> ADMIT / REJECT / ADMIT_DEGRADED + reason`), pluggable by domain.
In my case, the accounting domain would verify against MySQL; other domains would plug in their
own source of truth.

I froze it before building it. Reviewing the whole path, I found two things:

1. Of ~100 notes in the real corpus, only 15-20 had real admission risk. The problem the arbiter
   attacks is smaller than it looked from the inside.
2. The original problem (that the right information *reaches* the agent at the moment of need,
   retrieval) was still untouched. I was about to build the fourth admission piece with zero
   retrieval pieces.

Building the arbiter would have been following inertia: the next step of the plan, not the next
step of the problem. The rule I applied to myself is the same one that governs the notes:
**governance applies to the roadmap too**. It thaws the day there is evidence that the manual
method (verify on use, not on save) is not enough.

### Where this comes from

From the TechAcces project: a fictitious company with real accounting (~17,000 journal lines in
MySQL) on which I develop swarms of Claude agents with continuous evaluation. Two months of daily
sessions generate a lot of memory, and the problems above are not hypothetical: all three kinds
of rot showed up for real.

An anecdote that captures the spirit: on its first pass over the real corpus, the linter reported
two problems... that were **bugs in the linter itself** (it did not understand legitimate
cross-repository references and marked as broken the links cited as examples inside code). The
linter was fixed, not the corpus. The watchdog is watched too: nothing is taken as good without
checking, not even the verifier.

More than a framework, this is three small pieces and a criterion. Copy them and adapt them to
your corpus. And keep the question that gives rise to them: *who watches what your agent remembers?*

### Related projects

This harness is one piece of a larger body of work on multi-agent systems. The sibling pieces:

- [claude-code-context-management](https://github.com/jleonceo/claude-code-context-management): the direct sibling of this repo. Here we govern *what* the agent remembers; there, *how much* of it loads each session, so the context files (CLAUDE.md and MEMORY.md) do not bloat the context.
- [llm-eval-contable](https://github.com/jleonceo/llm-eval-contable): the same philosophy (measure before you trust) applied to a skill, what it is and how it is examined.
- [accounting-agent-swarm](https://github.com/jleonceo/accounting-agent-swarm): the system whose knowledge this harness governs, with its drops explained.
- [gobernanza-skills-analiticas](https://github.com/jleonceo/gobernanza-skills-analiticas): the five rules for governing skills, each with its real scar.
- [orquestacion-enjambres-ia](https://github.com/jleonceo/orquestacion-enjambres-ia): multi-agent routing, which agent handles each request without breaking as it grows.
- [verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia): state coherence checked by pure arithmetic, without AI.
- [tu-primer-asistente-ia-web](https://github.com/jleonceo/tu-primer-asistente-ia-web): what an AI assistant is, for absolute beginners.
- [tesoreria-forecast-ia](https://github.com/jleonceo/tesoreria-forecast-ia): cash-flow forecasting by decomposition with backtesting, plus ratios and aging.
- [control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia): accounting fraud detection with arithmetic, inside an internal-control framework.

---

Construido por / Built by [Juan Luis León Rodríguez](https://juanluisleon.vercel.app) · junio 2026 · Licencia [MIT](LICENSE)
