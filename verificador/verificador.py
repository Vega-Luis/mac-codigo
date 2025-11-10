from utils.arbol import TipoNodo, NodoArbol


class VerificadorSemantico:
    """
    Verificador semántico para el lenguaje MacCódigo.
    Recorre el ASA, valida tipos, maneja alcances y decora el árbol con tipos.
    
    Versión mejorada con:
    - Constantes booleanas predefinidas (mayonesa/ketchup)
    - Mensajes de error con línea y columna
    - Validación estricta de operaciones con booleanos
    - Mejor manejo de ámbitos anidados
    """

    def __init__(self, arbol_sintaxis, verbose=False):
        self.asa = arbol_sintaxis
        self.errores = []
        self.verbose = verbose

        # Pila de ámbitos: lista de diccionarios (nombre -> tipo)
        # Inicializar con constantes booleanas predefinidas
        self.pila_ambitos = [{
            "mayonesa": "salsa",  # true
            "ketchup": "salsa",   # false
        }]
        
        # Registro de funciones: nombre -> (tipo_retorno, [(tipo, nombre_param)])
        self.funciones = {}

        # Árbol de ámbitos para impresión anidada
        self.ambitos_arbol = {
            "nombre": "Global",
            "tipo": "GLOBAL",
            "simbolos": {
                "mayonesa": "salsa (const)",
                "ketchup": "salsa (const)",
            },
            "hijos": [],
        }
        self._stack_ambitos_arbol = [self.ambitos_arbol]

        # Tipos permitidos en MacCódigo
        self.TIPOS_PRIMITIVOS = ["torta", "lechuga", "pepinillo", "tomate", "salsa"]
        self.TIPOS_COMPUESTOS = ["hamburguesa", "cajita", "cajita_lechuga"]

        # Reglas de compatibilidad y coerción
        self.COMPATIBLES = {
            ("torta", "lechuga"): "lechuga",
            ("lechuga", "torta"): "lechuga",
            ("tomate", "salsa"): "tomate",
            ("salsa", "tomate"): "tomate",
        }

        # Operadores aritméticos (no permitidos con booleanos)
        self.OPERADORES_ARITMETICOS = ["+", "-", "mul", "div", "mod"]
        
        # Operadores lógicos (solo para booleanos)
        self.OPERADORES_LOGICOS = ["and", "or", "not"]

    # ==========================================================
    # MÉTODO PRINCIPAL
    # ==========================================================
    def verificar(self):
        if not self.asa or not self.asa.raiz:
            self.errores.append("Error: el árbol de sintaxis abstracta está vacío.")
            return self.errores

        if self.verbose:
            print("=== INICIO DE VERIFICACIÓN SEMÁNTICA ===")

        self._verificar_programa(self.asa.raiz)

        if self.verbose:
            print("\n=== TABLAS DE SÍMBOLOS ===")
            self._imprimir_tablas_anidada()

            print("\n=== ÁRBOL DECORADO ===")
            self._imprimir_arbol(self.asa.raiz)

        return self.errores

    # ==========================================================
    # PROGRAMA
    # ==========================================================
    def _verificar_programa(self, nodo_programa):
        for nodo in nodo_programa.nodos:
            self._verificar_nodo(nodo)

    # ==========================================================
    # DESPACHADOR RECURSIVO
    # ==========================================================
    def _verificar_nodo(self, nodo):
        if nodo is None:
            return None

        if self.verbose:
            tipo = nodo.tipo.name if nodo and getattr(nodo, "tipo", None) else "(sin tipo)"
            print(f"→ Verificando nodo {tipo} ({nodo.contenido or ''})")

        # Manejo de SECCION_DECLARACIONES
        if nodo.tipo == TipoNodo.SECCION_DECLARACIONES:
            for hijo in nodo.nodos:
                self._verificar_nodo(hijo)
            return

        # Manejo de BLOQUE_DECLARACION_VARIABLE
        elif nodo.tipo == TipoNodo.BLOQUE_DECLARACION_VARIABLE:
            for hijo in nodo.nodos:
                self._verificar_nodo(hijo)
            return

        elif nodo.tipo == TipoNodo.DECLARACION_VARIABLE:
            self._verificar_declaracion_variable(nodo)
            return

        elif nodo.tipo == TipoNodo.ASIGNACION:
            self._verificar_asignacion(nodo)
            return

        elif nodo.tipo == TipoNodo.DECLARACION_FUNCION:
            self._verificar_funcion(nodo)
            return

        elif nodo.tipo == TipoNodo.RETORNO:
            self._verificar_retorno(nodo)
            return

        elif nodo.tipo == TipoNodo.CONDICIONAL:
            self._verificar_condicional(nodo)
            return

        elif nodo.tipo == TipoNodo.REPETICION:
            self._verificar_repeticion(nodo)
            return

        elif nodo.tipo in [TipoNodo.BLOQUE_INSTRUCCIONES, TipoNodo.SECCION_CODIGO]:
            nombre_ambito = nodo.contenido or nodo.tipo.name
            self._nuevo_ambito(nombre_ambito, nodo.tipo.name)
            for hijo in nodo.nodos:
                self._verificar_nodo(hijo)
            self._cerrar_ambito()
            return

        elif nodo.tipo == TipoNodo.INVOCACION:
            self._verificar_invocacion(nodo)
            return

        # Manejo de SIS (servir)
        elif nodo.tipo == TipoNodo.SIS:
            self._verificar_sis(nodo)
            return

        elif nodo.tipo == TipoNodo.EXPRESION:
            tipo = self._verificar_expresion(nodo)
            nodo.decorador = tipo
            return tipo

        # Fallback: solo para tipos no manejados explícitamente
        for hijo in nodo.nodos or []:
            self._verificar_nodo(hijo)

    # ==========================================================
    # REGLAS SEMÁNTICAS
    # ==========================================================
    def _verificar_declaracion_variable(self, nodo):
        tipo = nodo.nodos[0].contenido
        nombre = nodo.nodos[1].contenido

        if nombre in self.pila_ambitos[-1]:
            self._error(f"Variable '{nombre}' redeclarada en el mismo ámbito.", nodo.nodos[1])
        else:
            self.pila_ambitos[-1][nombre] = tipo
            # Registrar también en el árbol de ámbitos
            self._stack_ambitos_arbol[-1]["simbolos"][nombre] = tipo
            nodo.decorador = tipo
            
            # Verificar la expresión de inicialización
            if len(nodo.nodos) > 2:
                tipo_exp = self._verificar_expresion(nodo.nodos[2])
                if tipo_exp and not self._compatibles(tipo, tipo_exp):
                    self._error(
                        f"Tipos incompatibles en declaración: '{tipo}' <- '{tipo_exp}'.",
                        nodo.nodos[1]
                    )

    def _verificar_asignacion(self, nodo):
        nombre = nodo.nodos[0].contenido
        tipo_var = self._buscar_variable(nombre)

        if not tipo_var:
            self._error(f"Variable '{nombre}' no declarada antes de su uso.", nodo.nodos[0])
            return

        tipo_exp = self._verificar_expresion(nodo.nodos[1])
        if tipo_exp and not self._compatibles(tipo_var, tipo_exp):
            self._error(
                f"Tipos incompatibles en asignación: '{tipo_var}' <- '{tipo_exp}'.",
                nodo.nodos[0]
            )

        nodo.decorador = tipo_var

    def _verificar_funcion(self, nodo):
        nombre = nodo.nodos[0].contenido
        if nombre in self.funciones:
            self._error(f"Función '{nombre}' redeclarada.", nodo.nodos[0])
            return

        parametros = nodo.nodos[1]
        tipos_params = self._extraer_parametros(parametros)
        tipo_retorno = "void"
        self.funciones[nombre] = (tipo_retorno, tipos_params)
        
        # Registrar función en ámbito global
        firma = f"func({', '.join(t for t, _ in tipos_params)}) -> {tipo_retorno}"
        self.pila_ambitos[0][nombre] = firma
        self._stack_ambitos_arbol[0]["simbolos"][nombre] = firma
        
        nodo.decorador = firma

        self._nuevo_ambito(nombre, TipoNodo.DECLARACION_FUNCION.name)
        for tipo, ident in tipos_params:
            self.pila_ambitos[-1][ident] = tipo
            self._stack_ambitos_arbol[-1]["simbolos"][ident] = tipo

        # Verificar bloque interno
        if len(nodo.nodos) > 2:
            self._verificar_nodo(nodo.nodos[-1])

        self._cerrar_ambito()

    def _verificar_retorno(self, nodo):
        if not nodo.nodos:
            self._error("Retorno sin valor.", nodo)
            return
        tipo_valor = self._verificar_expresion(nodo.nodos[0])
        nodo.decorador = tipo_valor

    def _verificar_condicional(self, nodo):
        if not nodo.nodos:
            return

        cond = nodo.nodos[0]

        # CONDICION (con comparador) o expresión booleana
        if cond.tipo.name == "CONDICION":
            _ = self._verificar_expresion(cond)
            nodo.decorador = "salsa"
        else:
            tipo_cond = self._verificar_expresion(cond)
            if tipo_cond and tipo_cond != "salsa":
                self._error(
                    f"La condición de '¿si?' debe ser de tipo 'salsa' (booleano), "
                    f"pero se encontró tipo '{tipo_cond}'.",
                    cond
                )

        # Verificar bloques (entonces y opcionalmente sino)
        for i in range(1, len(nodo.nodos)):
            self._verificar_nodo(nodo.nodos[i])

    def _verificar_repeticion(self, nodo):
        """
        Verifica una estructura de repetición (bucle 'para').
        Estructura esperada:
        [identificador, (expresión_inicio)?, expresión_fin, bloque]
        """
        if not nodo or not nodo.nodos:
            return

        identificador = nodo.nodos[0]
        tipo_inicio = None
        tipo_fin = None
        bloque = None

        # Casos posibles:
        if len(nodo.nodos) == 4:
            # para i <- expr_inicio hasta expr_fin: bloque
            tipo_inicio = self._verificar_expresion(nodo.nodos[1])
            tipo_fin = self._verificar_expresion(nodo.nodos[2])
            bloque = nodo.nodos[3]

        elif len(nodo.nodos) == 3:
            # para i hasta expr_fin: bloque
            tipo_fin = self._verificar_expresion(nodo.nodos[1])
            bloque = nodo.nodos[2]

        elif len(nodo.nodos) == 2:
            # para i hasta bloque (caso muy simplificado)
            bloque = nodo.nodos[1]

        else:
            if self.verbose:
                print(f"[WARN] Repetición con estructura inesperada ({len(nodo.nodos)} hijos).")
            return

        # Validar que las expresiones numéricas sean del tipo torta o lechuga
        for i, tipo in enumerate([tipo_inicio, tipo_fin]):
            if tipo and tipo not in ["torta", "lechuga", None]:
                expr_nodo = nodo.nodos[1] if i == 0 and len(nodo.nodos) > 1 else nodo.nodos[1 if len(nodo.nodos) == 3 else 2]
                self._error(
                    f"El límite del bucle 'para' debe ser numérico (torta/lechuga), "
                    f"pero se encontró tipo '{tipo}'.",
                    expr_nodo
                )

        # Verificar bloque interno
        if bloque:
            self._verificar_nodo(bloque)

    def _verificar_invocacion(self, nodo):
        nombre_func = nodo.nodos[0].contenido
        if nombre_func not in self.funciones:
            self._error(
                f"Función '{nombre_func}' no declarada antes de su invocación.",
                nodo.nodos[0]
            )
            return

        tipo_ret, params_decl = self.funciones[nombre_func]
        params_llamada = self._contar_parametros_invocacion(nodo)

        if len(params_decl) != len(params_llamada):
            self._error(
                f"La función '{nombre_func}' espera {len(params_decl)} parámetro(s), "
                f"pero se pasaron {len(params_llamada)}.",
                nodo.nodos[0]
            )

        nodo.decorador = tipo_ret

    def _verificar_sis(self, nodo):
        """Verifica la instrucción 'servir' (output)"""
        if nodo.nodos and nodo.nodos[0].nodos:
            for param in nodo.nodos[0].nodos:
                self._verificar_expresion(param)
        nodo.decorador = "void"

    # ==========================================================
    # EXPRESIONES
    # ==========================================================
    def _verificar_expresion(self, nodo):
        if nodo is None:
            return None
        
        if not hasattr(nodo, "tipo") or nodo.tipo is None:
            return None

        # Literales
        if nodo.tipo == TipoNodo.ENTERO:
            nodo.decorador = "torta"
            return "torta"
        elif nodo.tipo == TipoNodo.FLOTANTE:
            nodo.decorador = "lechuga"
            return "lechuga"
        elif nodo.tipo == TipoNodo.STRING:
            nodo.decorador = "tomate"
            return "tomate"
        elif nodo.tipo == TipoNodo.BOOLEANO:
            nodo.decorador = "salsa"
            return "salsa"
        elif nodo.tipo == TipoNodo.CARACTER:
            nodo.decorador = "pepinillo"
            return "pepinillo"
        elif nodo.tipo == TipoNodo.IDENTIFICADOR:
            tipo = self._buscar_variable(nodo.contenido)
            if not tipo:
                self._error(f"Variable '{nodo.contenido}' no declarada antes de su uso.", nodo)
                return None
            nodo.decorador = tipo
            return tipo
        elif nodo.tipo == TipoNodo.COMPARADOR:
            nodo.decorador = "salsa"
            return "salsa"

        # Condiciones del tipo (IDENTIFICADOR, COMPARADOR, ENTERO)
        if hasattr(nodo, "tipo") and nodo.tipo and nodo.tipo.name == "CONDICION":
            # Verifica los lados y marca tipo booleano
            izq = self._verificar_expresion(nodo.nodos[0])
            der = self._verificar_expresion(nodo.nodos[-1])
            nodo.decorador = "salsa"
            return "salsa"

        # Expresiones compuestas normales
        if nodo.tipo == TipoNodo.EXPRESION and nodo.nodos:
            # Si contiene comparadores, es una expresión booleana
            if any(hijo.tipo == TipoNodo.COMPARADOR for hijo in nodo.nodos):
                nodo.decorador = "salsa"
                return "salsa"

            tipo_izq = self._verificar_expresion(nodo.nodos[0])
            
            for i in range(1, len(nodo.nodos), 2):
                if i + 1 < len(nodo.nodos):
                    operador = nodo.nodos[i]
                    operador_texto = operador.contenido if operador else ""
                    
                    tipo_der = self._verificar_expresion(nodo.nodos[i + 1])
                    
                    # VALIDACIÓN: Operadores aritméticos con booleanos
                    if operador_texto in self.OPERADORES_ARITMETICOS:
                        if tipo_izq == "salsa":
                            self._error(
                                f"No se puede usar el operador aritmético '{operador_texto}' "
                                f"con tipo booleano (salsa).",
                                operador
                            )
                        if tipo_der == "salsa":
                            self._error(
                                f"No se puede usar el operador aritmético '{operador_texto}' "
                                f"con tipo booleano (salsa).",
                                nodo.nodos[i + 1]
                            )
                    
                    # Validar compatibilidad de tipos
                    if tipo_izq and tipo_der and not self._compatibles(tipo_izq, tipo_der):
                        self._error(
                            f"Operación inválida entre tipos '{tipo_izq}' y '{tipo_der}'.",
                            operador
                        )
                    
                    tipo_izq = self._resolver_tipo(tipo_izq, tipo_der)
            
            nodo.decorador = tipo_izq
            return tipo_izq

        return None

    # ==========================================================
    # FUNCIONES AUXILIARES
    # ==========================================================
    def _buscar_variable(self, nombre):
        """Busca una variable en la pila de ámbitos (desde el más interno al más externo)"""
        for ambito in reversed(self.pila_ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def _extraer_parametros(self, nodo):
        """
        Extrae pares (tipo, identificador) de los parámetros de una función.
        Ejemplo: torta a ; torta b → [("torta", "a"), ("torta", "b")]
        """
        pares = []
        if not nodo or not nodo.nodos:
            return pares

        tipo_actual = None
        for hijo in nodo.nodos:
            if hijo.tipo == TipoNodo.TIPO_DATO:
                tipo_actual = hijo.contenido
            elif hijo.tipo == TipoNodo.IDENTIFICADOR:
                if tipo_actual is None:
                    tipo_actual = "torta"  # tipo por defecto si falta
                pares.append((tipo_actual, hijo.contenido))
                tipo_actual = None
        return pares

    def _contar_parametros_invocacion(self, nodo):
        """Cuenta los parámetros en una invocación de función"""
        if len(nodo.nodos) < 2:
            return []
        params_node = nodo.nodos[1]
        if not params_node or not params_node.nodos:
            return []
        return [self._verificar_expresion(n) for n in params_node.nodos]

    def _compatibles(self, t1, t2):
        """Verifica si dos tipos son compatibles"""
        if not t1 or not t2:
            return True
        if t1 == t2:
            return True
        return (t1, t2) in self.COMPATIBLES

    def _resolver_tipo(self, t1, t2):
        """Resuelve el tipo resultante de una operación entre dos tipos"""
        if not t1:
            return t2
        if not t2:
            return t1
        if (t1, t2) in self.COMPATIBLES:
            return self.COMPATIBLES[(t1, t2)]
        if (t2, t1) in self.COMPATIBLES:
            return self.COMPATIBLES[(t2, t1)]
        return t1

    def _nuevo_ambito(self, nombre=None, tipo=None):
        """Crea un nuevo ámbito en la pila"""
        self.pila_ambitos.append({})
        # Registrar el nuevo ámbito en el árbol
        nodo = {
            "nombre": nombre or "Ámbito",
            "tipo": tipo or "AMBITO",
            "simbolos": {},
            "hijos": [],
        }
        self._stack_ambitos_arbol[-1]["hijos"].append(nodo)
        self._stack_ambitos_arbol.append(nodo)

    def _cerrar_ambito(self):
        """Cierra el ámbito actual"""
        self.pila_ambitos.pop()
        # Cerrar el ámbito en el árbol
        if len(self._stack_ambitos_arbol) > 1:
            self._stack_ambitos_arbol.pop()

    def _error(self, mensaje, nodo=None):
        """
        Registra un error semántico con información de posición si está disponible.
        
        Parameters
        ----------
        mensaje : str
            Mensaje de error
        nodo : NodoArbol, optional
            Nodo donde ocurrió el error (para obtener línea/columna)
        """
        if nodo and hasattr(nodo, 'linea') and hasattr(nodo, 'columna'):
            error_msg = f"Error semántico (línea {nodo.linea}, col {nodo.columna}): {mensaje}"
        else:
            error_msg = f"Error semántico: {mensaje}"
        
        self.errores.append(error_msg)

    # ==========================================================
    # IMPRESIÓN DE TABLAS Y ÁRBOL DECORADO
    # ==========================================================
    def _imprimir_tablas_anidada(self):
        """Imprime las tablas de símbolos de forma anidada"""
        def imprimir(nodo, nivel=0):
            indent = "  " * nivel
            print(f"{indent}{nodo['nombre']} ({nodo['tipo']})")
            if nodo["simbolos"]:
                for nombre, tipo in nodo["simbolos"].items():
                    print(f"{indent}  {nombre:<15} -> {tipo}")
            else:
                print(f"{indent}  (Vacío)")
            for hijo in nodo["hijos"]:
                imprimir(hijo, nivel + 1)

        imprimir(self.ambitos_arbol, 0)

        if self.funciones:
            print("\nFunciones declaradas:")
            for nombre, (tipo_ret, params) in self.funciones.items():
                params_txt = ", ".join(f"{t} {n}" for t, n in params)
                print(f"  {nombre}({params_txt}) -> {tipo_ret}")

    def _imprimir_arbol(self, nodo, prefijo="", es_ultimo=True):
        """Imprime el árbol decorado de forma visual"""
        if nodo is None:
            return
        # Conectores estilo árbol con "palitos" ASCII
        conector = "`-- " if es_ultimo else "|-- "
        tipo = nodo.tipo.name if nodo and getattr(nodo, "tipo", None) else "(sin tipo)"
        contenido = nodo.contenido or ""
        base = f"{tipo}: {contenido}" if contenido else tipo
        decorador = f" [{nodo.decorador}]" if hasattr(nodo, "decorador") and nodo.decorador else ""
        print(f"{prefijo}{conector}{base}{decorador}")

        hijos = nodo.nodos or []
        if not hijos:
            return
        nuevo_prefijo = f"{prefijo}    " if es_ultimo else f"{prefijo}|   "
        for i, hijo in enumerate(hijos):
            es_ult = (i == len(hijos) - 1)
            self._imprimir_arbol(hijo, nuevo_prefijo, es_ult)