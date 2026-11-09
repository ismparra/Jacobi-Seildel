# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado actual

El repositorio (`Jacobi-Seildel` en el remoto de GitHub, con esa ortografía) aún no tiene código, sistema de build, pruebas ni linter. Solo contiene `README.md`, un `.gitignore` de plantilla Python (sugiere Python, pero el lenguaje/framework de la interfaz no está definido en los requerimientos) y `Requerimientos/Protocolo de investigación Metodos numericos.pdf`, que es la fuente de verdad del alcance. Cuando se añada código, actualizar este archivo con los comandos de ejecución, pruebas (incluido cómo correr una sola) y la estructura de módulos.

## Proyecto (según el protocolo de investigación)

Tarea de Métodos Numéricos, Unidad IV (docente: Jorge Avalos Carrillo, entrega 03/11/2026, equipo de 4 personas). Se debe construir una **interfaz para resolver sistemas de ecuaciones lineales `A·x = b` con los métodos de Jacobi y Gauss-Seidel** y compararlos. Todos los documentos y la UI están en español.

### Funcionalidad requerida

- **Selección de método:** Jacobi, Gauss-Seidel o Ambos (comparación).
- **Error permitido** elegido por el usuario; es el criterio de paro, basado en el **error relativo aproximado** entre dos iteraciones consecutivas. El número de iteraciones debe variar según el error pedido.
- **Validación de linealidad:** si una ecuación es no lineal (p. ej. `x²`, `x·y`, seno/coseno de una incógnita), mostrar una alerta y **no calcular**.
- **Control de convergencia:** si el método no converge, mostrar un mensaje de error. La dominancia diagonal de `A` garantiza convergencia; si no se cumple, el método puede o no converger, y la interfaz debe avisar cuando las iteraciones no se acerquen a la solución.
- **Resultados:** solución, número de iteraciones y tiempo de ejecución de cada método.
- **Comparación (modo Ambos):** misma aproximación inicial y mismo error para ambos métodos; indicar cuál fue más eficiente (menor tiempo y menor número de iteraciones) y registrar en una tabla comparativa.
- **Herramientas de apoyo:** botones para limpiar, agregar ecuaciones y cargar un ejemplo.

### Fuera de alcance

Solo ecuaciones lineales; no se incluyen otros métodos numéricos ni sistemas no lineales.

### Fundamento matemático

- Jacobi: cada incógnita nueva usa solo valores de la iteración anterior.
- Gauss-Seidel: usa los valores nuevos tan pronto se calculan dentro de la misma iteración (normalmente converge en menos iteraciones; las pruebas deben confirmarlo cuando ambos convergen).
- Pruebas previstas con sistemas de distintos tamaños y distintos errores permitidos.
