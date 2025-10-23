from enum import Enum, auto

class TipoNodo(Enum):
    PROGRAMA = auto()
    ASIGNACION = auto()
    CONDICIONAL = auto()
    REPETICION = auto()
    FUNCION = auto()
    BLOQUE_INSTRUCCIONES = auto()
    EXPRESION = auto()
    CONDICION = auto()
    COMPARADOR = auto()
    OPERADOR = auto()
    ENTERO = auto()
    FLOTANTE = auto()
    STRING = auto()
    BOOLEANO = auto()
    CARACTER = auto()
    IDENTIFICADOR = auto()
    PARAMETROS = auto()

class NodoArbol:
    def __init__(self, tipo, contenido=None, nodos=None):
        self.tipo = tipo
        self.contenido = contenido
        self.nodos = nodos or []

    def __repr__(self):
        return f"NodoArbol({self.tipo.name}, contenido={self.contenido}, hijos={len(self.nodos)})"

    def imprimir(self, nivel=0):
        sangria = "  " * nivel
        tipo_nombre = self.tipo.name if self.tipo else "(sin tipo)"
        if self.contenido:
            print(f"{sangria}{tipo_nombre}: {self.contenido}")
        else:
            print(f"{sangria}{tipo_nombre}")
        for nodo in self.nodos:
            if nodo:  # evita imprimir nodos None
                nodo.imprimir(nivel + 1)


class ArbolSintaxisAbstracta:
    def __init__(self):
        self.raiz = None

    def imprimir(self):
        if self.raiz:
            print("Árbol de Sintaxis Abstracta (ASA):")
            self.raiz.imprimir()
        else:
            print("El ASA está vacío.")
