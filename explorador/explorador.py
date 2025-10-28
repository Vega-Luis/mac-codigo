import re
from enum import Enum, auto as autogen


class TipoComponente(Enum):
    """
    Definición  del conjunto de categorías léxicas para el lenguaje MacCódigo.

    Este enum define los tipos de componentes léxicos que el explorador
    puede identificar.
    """

    COMENTARIO = autogen()
    PALABRA_CLAVE = autogen()
    FUNCION = autogen()
    CONDICIONAL = autogen()
    REPETICION = autogen()
    ASIGNACION = autogen()
    TIPO = autogen()
    OPERADOR = autogen()
    COMPARADOR = autogen()
    ENTERO = autogen()
    FLOTANTE = autogen()
    CARACTER = autogen()
    STRING = autogen()
    BOOLEANO = autogen()
    PUNTUACION = autogen()
    BLANCOS = autogen()
    IDENTIFICADOR = autogen()
    ERROR = autogen()


class ComponenteLexico:
    """
    Representa un componente léxico identificado en el código fuente.

    Parametros
    ----------
    tipo : TipoComponente
        El tipo del componente léxico (según el enum TipoComponente).
    texto : str
        El texto exacto del componente tal como aparece en el código fuente.
    fila : int
        La línea en la que se encuentra el componente.
    col : int
        La columna en la que comienza el componente.
    """

    def __init__(self, tipo, texto, fila, col):
        self.tipo = tipo
        self.texto = texto
        self.linea = fila
        self.columna = col

    def __str__(self):
        """
        Representa el componente léxico como una cadena legible.
        """
        return f"{self.tipo.name:<15} <{self.texto}> (línea {self.linea}, col {self.columna})"


class ExploradorMacCodigo:
    """
    Explorador léxico para el lenguaje MacCódigo.

    Se encarga de explorar el código fuente, identificar componentes léxicos y
    reportar errores.

    Parametros
    ----------
    fuente : str
        El código fuente a explorar.
    """

    # Descriptores de componentes (regex por prioridad)
    descriptores = [
        (TipoComponente.COMENTARIO, r'^#.*'),  # comentarios estilo # ...
        (TipoComponente.PALABRA_CLAVE, r'^(hambriento|satisfecho|cocinar|servir|ingrediente|receta|entregar|para|hasta|de otro modo)\b'),
        (TipoComponente.CONDICIONAL, r'^(¿si\?|¡de otro modo!)'),
        (TipoComponente.REPETICION, r'^(para|hasta)\b'),
        (TipoComponente.ASIGNACION, r'^<-'),
        (TipoComponente.OPERADOR, r'^(mul|div|mod|\+|-)\b'),
        (TipoComponente.OPERADOR, r'^!!'),

        (TipoComponente.COMPARADOR, r'^(=|!=|<=|>=|<|>)'),
        (TipoComponente.TIPO, r'^(torta|lechuga|pepinillo|tomate|salsa|hamburguesa|cajita)\b'),
        (TipoComponente.OPERADOR, r'^(mul|div|mod|\+|-)'),
        (TipoComponente.FLOTANTE, r'^-?\d+\.\d+'),
        (TipoComponente.ENTERO, r'^-?\d+'),
        (TipoComponente.CARACTER, r"^'[^']'"),
        (TipoComponente.STRING, r'^"[^"\n]*"'),
        (TipoComponente.IDENTIFICADOR, r'^[A-Za-z_][A-Za-z0-9_]*'),
        (TipoComponente.PUNTUACION, r'^[():,.\[\]{};]'),
        (TipoComponente.BLANCOS, r'^\s+'),
        (TipoComponente.ERROR, r'^.'),  # cualquier cosa no reconocida
    ]

    def __init__(self, fuente: str):
        self.lineas = fuente.splitlines()
        self.componentes = []
        self.errores = []

    def explorar(self):
        """
        Explora el código fuente línea por línea, identificando componentes
        léxicos y errores.

        Retorna
        -------
        List[ComponenteLexico]
            Una lista de componentes léxicos identificados en el código fuente.
        """
        for i, contenido_linea in enumerate(self.lineas, start=1):
            col = 1
            linea_restante = contenido_linea
            while linea_restante:
                detectado = False
                for tipo, patron in self.descriptores:
                    emp = re.match(patron, linea_restante)
                    if emp:
                        token = emp.group(0)

                        if tipo == TipoComponente.ERROR:
                            self.errores.append(
                                f"Error léxico en línea {i}, columna {col}: '{token}' no válido"
                            )
                            self.componentes.append(ComponenteLexico(tipo, token, i, col))

                        elif tipo not in [TipoComponente.BLANCOS, TipoComponente.COMENTARIO]:
                            self.componentes.append(ComponenteLexico(tipo, token, i, col))

                        col += len(token)
                        linea_restante = linea_restante[len(token):]
                        detectado = True
                        break

                if not detectado:
                    simbolo = linea_restante[0]
                    self.errores.append(f"Error léxico en línea {i}, columna {col}: '{simbolo}' no es válido")
                    self.componentes.append(ComponenteLexico(TipoComponente.ERROR, simbolo, i, col))
                    col += 1
                    linea_restante = linea_restante[1:]

        return self.componentes

    def imprimir_componentes(self):
        """
        Imprime los componentes léxicos identificados en el código fuente.
        """
        print("== Componentes Léxicos ==")
        for c in self.componentes:
            print(c)

    def imprimir_errores(self):
        """
        Imprime los errores léxicos encontrados durante la exploración.
        """
        if self.errores:
            print("\n== Errores Encontrados ==")
            for e in self.errores:
                print(e)
            print(f"\nErrores totales: {len(self.errores)}")
        else:
            print("\nSin errores léxicos.")
