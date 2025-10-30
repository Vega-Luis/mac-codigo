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
    DECLARACION_VARIABLE = auto()
    DECLARACION = auto()
    PARAMETROS = auto()
    SECCION_CODIGO = auto()
    INVOCACION = auto()
    INDEXACION = auto()
    TERMINO = auto()

class NodoArbol:
    def __init__(self, tipo, contenido=None, nodos=None):
        self.tipo = tipo
        self.contenido = contenido
        self.nodos = nodos or []

    def __repr__(self):
        return f"NodoArbol({self.tipo.name}, contenido={self.contenido}, hijos={len(self.nodos)})"
    
    def imprimir(self, prefijo="", es_ultimo=True):
        tipo_nombre = self.tipo.name if self.tipo else "(sin tipo)"
        texto = f"{tipo_nombre}: {self.contenido}" if self.contenido else tipo_nombre

        # Determina el símbolo del nodo actual
        conector = "└── " if es_ultimo else "├── "
        print(prefijo + conector + texto)

        # Calcula el prefijo para los hijos
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")

        # Imprime los hijos
        for i, nodo in enumerate(self.nodos):
            if nodo:
                es_ultimo_hijo = (i == len(self.nodos) - 1)
                nodo.imprimir(nuevo_prefijo, es_ultimo_hijo)



class ArbolSintaxisAbstracta:
    def __init__(self):
        self.raiz = None

    def imprimir(self):
        if self.raiz:
            print("Árbol de Sintaxis Abstracta (ASA):")
            self.raiz.imprimir()
        else:
            print("El ASA está vacío.")
