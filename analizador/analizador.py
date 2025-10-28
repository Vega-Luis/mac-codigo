from explorador.explorador import TipoComponente, ComponenteLexico
from utils.arbol import TipoNodo, NodoArbol, ArbolSintaxisAbstracta
from utils.tipo_datos import TipoDatos
from explorador.explorador import ExploradorMacCodigo


class AnalizadorMacCodigo:
    """
    Analizador sintáctico para el lenguaje MacCódigo.
    Construye un árbol de sintaxis abstracta (ASA) siguiendo
    la gramática del lenguaje.
    """

    def __init__(self, lista_componentes: list):
        self.componentes_lexicos = lista_componentes
        self.cantidad = len(lista_componentes)
        self.posicion = 0
        self.componente_actual = lista_componentes[0] if lista_componentes else None
        self.asa = ArbolSintaxisAbstracta()

    # === MÉTODO PRINCIPAL ===
    def analizar(self):
        self.asa.raiz = self.__analizar_programa()

    # === GRAMÁTICA PRINCIPAL ===
    def __analizar_programa(self):
        """
        Programa ::= (Asignacion | Condicional | Repeticion | Funcion | InstruccionSimple)*
        """
        nodos = []

        while self.componente_actual is not None:
            texto = self.componente_actual.texto

            if texto == "receta":
                nodos.append(self.analizar_funcion())

            elif texto in ["¿si?", "¡de otro modo!"]:
                nodos.append(self.analizar_condicional())

            elif texto in ["para", "hasta"]:
                nodos.append(self.analizar_repeticion())

            elif texto in ["servir", "cocinar", "entregar", "hambriento", "satisfecho"]:
                nodos.append(self.analizar_instruccion_simple())

                # Fin del programa
                if texto == "satisfecho":
                    self.__siguiente()
                    break

            elif self.componente_actual.tipo in [
                TipoComponente.IDENTIFICADOR,
                TipoComponente.ASIGNACION,
                TipoComponente.TIPO,
            ]:
                nodos.append(self.analizar_asignacion())

            else:
                # ignorar símbolos sueltos
                self.__siguiente()

        return NodoArbol(TipoNodo.PROGRAMA, nodos=nodos)

    # === ASIGNACIÓN ===
    def analizar_asignacion(self):
        """
        Asignacion ::= (TIPO)? Identificador <- (Literal | Expresion | { Asignacion* })
        """
        nodos = []

        # Si hay un TIPO antes del identificador (p.ej. 'torta id <- 101'), lo saltamos
        if self.componente_actual and self.componente_actual.tipo == TipoComponente.TIPO:
            tipo_nombre = self.componente_actual.texto
            self.__siguiente()

        identificador = self.verificar_identificador()
        nodos.append(identificador)

        self.verificar("<-")
        self.__siguiente()

        # Si viene un bloque entre llaves
        if self.componente_actual and self.componente_actual.texto == "{":
            bloque = self.analizar_bloque_instrucciones()
            nodos.append(bloque)

        # Literal simple
        elif self.componente_actual.tipo in (
            TipoComponente.ENTERO,
            TipoComponente.FLOTANTE,
            TipoComponente.STRING,
            TipoComponente.BOOLEANO,
            TipoComponente.CARACTER,
        ):
            literal = self.analizar_literal()
            nodos.append(literal)

        # Expresión (identificadores, operadores, etc.)
        else:
            nodos.append(self.analizar_expresion())

        return NodoArbol(TipoNodo.ASIGNACION, nodos=nodos)

    # === CONDICIONAL ===
    def analizar_condicional(self):
        """
        Condicional ::= ¿si? (Condicion) { Instruccion* } (¡de otro modo! { Instruccion* })?
        """
        nodos = []
        self.verificar("¿si?")
        self.__siguiente()

        self.verificar("(")
        self.__siguiente()

        condicion = self.analizar_condicion()
        nodos.append(condicion)

        self.verificar(")")
        self.__siguiente()

        bloque_si = self.analizar_bloque_instrucciones()
        nodos.append(bloque_si)

        if self.componente_actual and self.componente_actual.texto == "¡de otro modo!":
            self.__siguiente()
            bloque_else = self.analizar_bloque_instrucciones()
            nodos.append(bloque_else)

        return NodoArbol(TipoNodo.CONDICIONAL, nodos=nodos)

    # === REPETICIÓN ===
    def analizar_repeticion(self):
        """
        Repeticion ::= para (Condicion) { Instruccion* }
        """
        nodos = []
        self.verificar("para")
        self.__siguiente()

        self.verificar("(")
        self.__siguiente()

        condicion = self.analizar_condicion()
        nodos.append(condicion)

        self.verificar(")")
        self.__siguiente()

        bloque = self.analizar_bloque_instrucciones()
        nodos.append(bloque)

        return NodoArbol(TipoNodo.REPETICION, nodos=nodos)

    # === FUNCIÓN ===
    def analizar_funcion(self):
        """
        Funcion ::= receta Identificador (Parametros) { Instruccion* }
        """
        nodos = []
        self.verificar("receta")
        self.__siguiente()

        identificador = self.verificar_identificador()
        nodos.append(identificador)

        self.verificar("(")
        self.__siguiente()

        parametros = self.analizar_parametros_definicion()
        nodos.append(parametros)

        self.verificar(")")
        self.__siguiente()

        bloque = self.analizar_bloque_instrucciones()
        nodos.append(bloque)

        return NodoArbol(TipoNodo.FUNCION, nodos=nodos)

    # === BLOQUE DE INSTRUCCIONES ===
    def analizar_bloque_instrucciones(self):
        """
        BloqueInstrucciones ::= { (Instruccion (',' Instruccion)*)? }
        """
        nodos = []
        self.verificar("{")
        self.__siguiente()

        while self.componente_actual and self.componente_actual.texto != "}":
            # Ignorar comas, punto y coma, o tokens vacíos
            if self.componente_actual.texto in [",", ";"]:
                self.__siguiente()
                continue
            nodos.append(self.analizar_instruccion())

        self.verificar("}")
        self.__siguiente()

        return NodoArbol(TipoNodo.BLOQUE_INSTRUCCIONES, nodos=nodos)

    # === INSTRUCCIONES ===
    def analizar_instruccion(self):
        """
        Instruccion ::= Asignacion | Condicional | Repeticion
        """
        if self.componente_actual.texto == "¿si?":
            return self.analizar_condicional()
        elif self.componente_actual.texto == "para":
            return self.analizar_repeticion()
        elif self.componente_actual.tipo in [TipoComponente.IDENTIFICADOR, TipoComponente.TIPO]:
            return self.analizar_asignacion()
        else:
            # ignorar separadores u otros tokens sueltos
            self.__siguiente()
            return NodoArbol(TipoNodo.EXPRESION, contenido="")

    # === CONDICIONES / EXPRESIONES / LITERALES ===
    def analizar_condicion(self):
        """
        Condicion ::= Valor Comparador Valor
        """
        nodos = [self.analizar_valor()]
        self.verificar_tipo(TipoComponente.COMPARADOR)
        nodos.append(NodoArbol(TipoNodo.COMPARADOR, contenido=self.componente_actual.texto))
        self.__siguiente()
        nodos.append(self.analizar_valor())

        return NodoArbol(TipoNodo.CONDICION, nodos=nodos)

    def analizar_expresion(self):
        """
        Expresion ::= Valor (Operador Valor)*
        """
        nodos = [self.analizar_valor()]
        while self.componente_actual and self.componente_actual.tipo == TipoComponente.OPERADOR:
            op = NodoArbol(TipoNodo.OPERADOR, contenido=self.componente_actual.texto)
            self.__siguiente()
            nodos.append(op)
            nodos.append(self.analizar_valor())
        return NodoArbol(TipoNodo.EXPRESION, nodos=nodos)

    def analizar_valor(self):
        if self.componente_actual.tipo == TipoComponente.IDENTIFICADOR:
            return self.verificar_identificador()
        return self.analizar_literal()

    def analizar_literal(self):
        tipo = self.componente_actual.tipo
        mapa = {
            TipoComponente.ENTERO: TipoNodo.ENTERO,
            TipoComponente.FLOTANTE: TipoNodo.FLOTANTE,
            TipoComponente.STRING: TipoNodo.STRING,
            TipoComponente.BOOLEANO: TipoNodo.BOOLEANO,
            TipoComponente.CARACTER: TipoNodo.CARACTER,
        }
        nodo = NodoArbol(mapa.get(tipo), contenido=self.componente_actual.texto)
        self.__siguiente()
        return nodo

    # === PARÁMETROS ===
    def analizar_parametros_definicion(self):
        """
        ParametrosDefinicion ::= Identificador (',' Identificador)*
        """
        nodos = []
        if self.componente_actual.texto == ")":
            return NodoArbol(TipoNodo.PARAMETROS, nodos=nodos)
        nodos.append(self.verificar_identificador())
        while self.componente_actual.texto == ",":
            self.__siguiente()
            nodos.append(self.verificar_identificador())
        return NodoArbol(TipoNodo.PARAMETROS, nodos=nodos)

    def analizar_instruccion_simple(self):
        """
        InstruccionSimple ::= PALABRA_CLAVE ( STRING | IDENTIFICADOR )*
        """
        palabra = self.componente_actual.texto
        nodo_principal = NodoArbol(TipoNodo.EXPRESION, contenido=palabra)
        self.__siguiente()

        # Captura argumentos entre paréntesis si existen
        if self.componente_actual and self.componente_actual.texto == "(":
            self.__siguiente()
            hijos = []
            while self.componente_actual and self.componente_actual.texto != ")":
                if self.componente_actual.tipo in (
                    TipoComponente.STRING,
                    TipoComponente.IDENTIFICADOR,
                    TipoComponente.ENTERO,
                    TipoComponente.FLOTANTE,
                ):
                    hijos.append(self.analizar_valor())
                else:
                    self.__siguiente()
            nodo_principal.nodos = hijos
            if self.componente_actual and self.componente_actual.texto == ")":
                self.__siguiente()

        return nodo_principal

    # === VERIFICACIONES ===
    def verificar(self, texto):
        if self.componente_actual is None:
            raise Exception(f"Se esperaba '{texto}', pero se llegó al final del archivo.")
        if self.componente_actual.texto != texto:
            raise Exception(f"Se esperaba '{texto}', pero se encontró '{self.componente_actual.texto}'.")

    def verificar_tipo(self, tipo):
        if self.componente_actual is None:
            raise Exception(f"Se esperaba componente tipo '{tipo}', pero no hay más tokens.")
        if self.componente_actual.tipo != tipo:
            raise Exception(f"Se esperaba tipo '{tipo}', pero se encontró '{self.componente_actual.tipo}'.")

    def verificar_identificador(self):
        if self.componente_actual.tipo not in [TipoComponente.IDENTIFICADOR, TipoComponente.TIPO]:
            raise Exception(f"Se esperaba un identificador o tipo, se encontró '{self.componente_actual.texto}'.")
        nodo = NodoArbol(TipoNodo.IDENTIFICADOR, contenido=self.componente_actual.texto)
        self.__siguiente()
        return nodo

    def __siguiente(self):
        self.posicion += 1
        if self.posicion < self.cantidad:
            self.componente_actual = self.componentes_lexicos[self.posicion]
        else:
            self.componente_actual = None
