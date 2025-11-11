# mac-codigo

El lenguaje **Mac Código** surge como una propuesta innovadora que combina la enseñanza de la programación con un enfoque lúdico y pedagógico. La temática seleccionada, basada en el sistema de conteo de calorías, permite representar la **complejidad algorítmica** de forma intuitiva, ya que cada instrucción equivale a un valor en “calorías” que refleja el costo computacional. Esta metáfora facilita la comprensión de un concepto abstracto mediante un elemento cotidiano y fácil de relacionar..

Asimismo, se adaptaron los términos y estructuras del lenguaje al entorno de una cocina de McDonald 's, lo cual aporta un componente divertido y cercano al usuario. Los tipos de datos llevan nombres alusivos a elementos de este contexto, generando una correspondencia clara entre la terminología empleada y las estructuras de programación que representan. Además, se incorporó el tipo de dato **“registro”**, poco común en lenguajes tradicionales, para resaltar la flexibilidad del lenguaje y su capacidad de agrupar información diversa.

En conjunto, la motivación detrás de Mac Código es ofrecer una herramienta didáctica que haga más accesible el aprendizaje de la **lógica de programación y la complejidad algorítmica**, especialmente en etapas tempranas de formación o en comunidades donde el lenguaje técnico puede ser una barrera. Con ello, se busca fomentar la comprensión y el interés en la programación a través de un enfoque intuitivo, divertido y significativo.

## Estructura de Carpetas y Archivos

```text
compilador/
│
├── ejemplos/                # Ejemplos de código en lenguaje MacCódigo
│   ├── ejemplo1.mac
│   ├── ejemplo2.mac
│   └── ...
|
|── analizador/
|  |──__init__.py
|  |──analizador.py
|
| ── explorador/
|  |──__ init__.py
|  |──explorador.py
|
|── utils/
|  |──arbol.py
|  |──tipo_datos.py
│
├── .gitignore
├── LICENSE
├── README.md                # Documentación principal del proyecto
└── maccodigo.py            # Etapa de exploración (scanner / lexer)
```

## Uso del compilador
Ejecuta el compilador pasando un archivo fuente en MacCódigo (`.jama`). El
proceso recorre las etapas de análisis léxico, sintáctico y verificación
semántica.

```bash
python maccodigo.py ejemplos/saludo.jama
```

Si no se detectan errores semánticos, se puede generar el código Python
equivalente del programa usando las siguientes opciones:

- `--mostrar-python`: imprime el código traducido en la consola.
- `--emit-python <archivo>` / `-o <archivo>`: escribe el resultado en un
  archivo de tu elección.

Como se puede ver en el siguiente ejemplo
```bash
python maccodigo.py ejemplos/saludo.jama --mostrar-python -o salida.py
```

