# Convención de citas: cada nota dice de dónde viene

La tercera pieza no es código: es una convención. Cada nota de memoria termina con un
bloque que responde tres preguntas: **quién verificó esto, contra qué fuente, y si se
puede volver a comprobar**.

```markdown
> **Origen:** <cómo nació esta nota: incidente, análisis, decisión del propietario>
> **Verificado por:** <quién o qué lo comprobó, y cuándo>
> **Fuente:** <la fuente primaria: la query SQL, el fichero, el informe, la URL>
> **Re-ejecutable:** <sí/no, y cómo volver a comprobarlo hoy>
```

## Por qué importa

Una nota sin cita es una afirmación flotante: dentro de un mes nadie sabrá si fue un
dato medido, una suposición o un error que se coló. Con la cita, cualquier lector (humano
o agente) puede hacer dos cosas que sin ella son imposibles:

1. **Ponderar la confianza.** No pesa lo mismo "verificado con query en la base de datos
   el 11/06" que "impresión tras una conversación".
2. **Re-verificar al usar.** Si la nota es re-ejecutable, el agente puede comprobar que
   sigue siendo verdad *antes* de actuar sobre ella: la memoria dice lo que era cierto
   cuando se escribió, no lo que es cierto hoy.

## Ejemplo real (anonimizado)

```markdown
---
name: descuadre-conocido-redondeo
description: 78 asientos con descuadre de -0,01 € por redondeo — esperado, no es bug
metadata:
  type: project
---

Los 78 asientos de nómina con descuadre de -0,01 € (y el global de -0,34 €) son un
artefacto conocido del redondeo en el cálculo. No abrir investigación cada vez que
aparezcan: están identificados y aceptados.

> **Origen:** investigación del descuadre global del diario (mayo 2026)
> **Verificado por:** query de distribución sobre el diario completo, no un caso suelto
> **Fuente:** SELECT num_asiento, SUM(debe)-SUM(haber) ... HAVING diferencia != 0
> **Re-ejecutable:** sí, la misma query, contra la base de datos en vivo
```

La idea viene de observar cómo GitHub Copilot ancla sus respuestas a citas de código:
la afirmación vale lo que vale su ancla.

## Qué NO resuelve

La cita documenta la verificación, no la ejecuta. Una nota puede llevar un bloque de
cita perfectamente formateado y ser falsa (fuente mal citada, verificación que nunca
ocurrió). El lint comprueba la estructura; la veracidad solo la garantiza volver a
ejecutar la comprobación contra la fuente. Por eso el campo clave es `Re-ejecutable`.
