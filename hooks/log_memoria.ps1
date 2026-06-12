# log_memoria.ps1 — PostToolUse hook de Claude Code
# Añade una línea a log.md cada vez que el agente crea o modifica una nota de memoria.
# El rastro no depende de la disciplina de nadie: dispara solo, en cada Write/Edit.
# Formato de cada línea: fecha | ADD/MOD | fichero | "descripción del frontmatter"
#
# Registro en settings.json (~/.claude/settings.json):
#   "hooks": {
#     "PostToolUse": [
#       { "matcher": "Write", "hooks": [ { "type": "command",
#         "command": "powershell -NonInteractive -NoProfile -File \"<ruta>/hooks/log_memoria.ps1\"" } ] },
#       { "matcher": "Edit",  "hooks": [ { "type": "command",
#         "command": "powershell -NonInteractive -NoProfile -File \"<ruta>/hooks/log_memoria.ps1\"" } ] }
#     ]
#   }

param()

# ── EDITA ESTA RUTA: el directorio donde viven tus notas de memoria ──
$memory_dir = "$env:USERPROFILE\.claude\projects\<tu-proyecto>\memory"

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }

    $ctx = $raw | ConvertFrom-Json
    $tool_name  = $ctx.tool_name
    $file_path  = $ctx.tool_input.file_path

    if (-not $file_path) { exit 0 }

    # Normalizar separadores
    $file_path = $file_path -replace '/', '\'

    $log_path = Join-Path $memory_dir "log.md"

    # Solo ficheros .md dentro del directorio de memoria
    if (-not $file_path.StartsWith($memory_dir)) { exit 0 }
    if (-not $file_path.EndsWith(".md"))          { exit 0 }

    # No loguear el propio log ni el índice
    $filename = Split-Path $file_path -Leaf
    if ($filename -eq "log.md")    { exit 0 }
    if ($filename -eq "MEMORY.md") { exit 0 }

    # Operación: Write → ADD (fichero nuevo), Edit → MOD
    $op = if ($tool_name -eq "Write") { "ADD" } else { "MOD" }

    # Extraer description del frontmatter
    $description = "[sin descripción]"
    $content = ""

    if ($tool_name -eq "Write" -and $ctx.tool_input.content) {
        $content = $ctx.tool_input.content
    } elseif (Test-Path $file_path) {
        $content = Get-Content $file_path -Raw -Encoding UTF8
    }

    if      ($content -match 'description:\s*"([^"]+)"') { $description = $Matches[1] }
    elseif  ($content -match "description:\s*'([^']+)'") { $description = $Matches[1] }
    elseif  ($content -match 'description:\s*([^\n]+)')  { $description = $Matches[1].Trim() }

    if ($description.Length -gt 80) { $description = $description.Substring(0, 77) + "..." }

    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    $line = "$date | $op | $filename | `"$description`""

    Add-Content -Path $log_path -Value $line -Encoding UTF8

} catch {
    # Fallo silencioso — nunca bloquear el flujo de trabajo
}

exit 0
