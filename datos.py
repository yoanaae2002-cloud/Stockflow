"""
StockFlow - Banco de datos para las tres fases de ampliación (2.º DAM).

Este archivo contiene únicamente datos. La gestión de los hilos, estados,
ventas, cancelaciones, devoluciones, cobros y bloqueos corresponde al alumnado.

Se conserva el conjunto de datos original de StockFlow y se añaden:
    CANCELACIONES      -> Fase I
    DEVOLUCIONES       -> Fase II
    PEDIDOS_COMPUESTOS -> Fase III

IMPORTANTE:
- Todos utilizan TIEMPO_COBRO y TIEMPO_REPOSICION de este archivo.
- Los instantes de las solicitudes son segundos desde el INICIO común.
- CANCELACIONES propone coincidencias temporales sobre pedidos existentes, pero
  el planificador de hilos no garantiza su estado exacto en un instante.
- PRUEBAS_CANCELACION_ESTADO especifica situaciones adicionales controladas
  que DEBEN poder demostrarse, sin depender de la velocidad del ordenador.
- Se incluyen operaciones que deben rechazarse. No se debe alterar este archivo
  para conseguir que todas las solicitudes sean aceptadas.
"""

# ============================================================================
# DATOS ORIGINALES DE STOCKFLOW (SE MANTIENEN)
# ============================================================================

STOCK_INICIAL = {
    "Teclado mecanico": 18,
    "Teclado inalambrico": 12,
    "Raton gaming": 20,
    "Raton oficina": 25,
    "Monitor 24 pulgadas": 10,
    "Monitor 27 pulgadas": 8,
    "Auriculares USB": 16,
    "Auriculares Bluetooth": 14,
    "Webcam Full HD": 11,
    "Microfono USB": 9,
    "SSD 500 GB": 15,
    "SSD 1 TB": 12,
    "Memoria USB 64 GB": 30,
    "Disco externo 2 TB": 7,
    "Hub USB-C": 13,
    "Cable HDMI": 35,
    "Cable USB-C": 40,
    "Cargador USB-C 65W": 18,
    "Base refrigeradora": 10,
    "Soporte monitor": 9,
    "Router WiFi": 6,
    "Switch 8 puertos": 8,
    "Adaptador USB Ethernet": 12,
    "Impresora laser": 5,
    "Toner negro": 10,
}

# Formato: (id_pedido, producto, unidades)
PEDIDOS = [
    ("PED-001", "Teclado mecanico", 4),
    ("PED-002", "Raton gaming", 5),
    ("PED-003", "Monitor 24 pulgadas", 3),
    ("PED-004", "SSD 1 TB", 4),
    ("PED-005", "Cable HDMI", 8),
    ("PED-006", "Auriculares USB", 5),
    ("PED-007", "Teclado mecanico", 6),
    ("PED-008", "Monitor 27 pulgadas", 3),
    ("PED-009", "SSD 500 GB", 5),
    ("PED-010", "Raton oficina", 8),
    ("PED-011", "Webcam Full HD", 4),
    ("PED-012", "Cable USB-C", 10),
    ("PED-013", "Hub USB-C", 5),
    ("PED-014", "Monitor 24 pulgadas", 4),
    ("PED-015", "Auriculares Bluetooth", 6),
    ("PED-016", "Disco externo 2 TB", 3),
    ("PED-017", "Memoria USB 64 GB", 12),
    ("PED-018", "Teclado inalambrico", 5),
    ("PED-019", "Raton gaming", 7),
    ("PED-020", "Cargador USB-C 65W", 6),
    ("PED-021", "SSD 1 TB", 5),
    ("PED-022", "Base refrigeradora", 4),
    ("PED-023", "Monitor 27 pulgadas", 4),
    ("PED-024", "Switch 8 puertos", 4),
    ("PED-025", "Router WiFi", 3),
    ("PED-026", "Toner negro", 4),
    ("PED-027", "Impresora laser", 2),
    ("PED-028", "Adaptador USB Ethernet", 5),
    ("PED-029", "Cable HDMI", 12),
    ("PED-030", "Auriculares USB", 7),
    ("PED-031", "Webcam Full HD", 5),
    ("PED-032", "SSD 500 GB", 7),
    ("PED-033", "Microfono USB", 4),
    ("PED-034", "Soporte monitor", 4),
    ("PED-035", "Cable USB-C", 15),
    ("PED-036", "Teclado mecanico", 7),
    ("PED-037", "Raton oficina", 10),
    ("PED-038", "Hub USB-C", 6),
    ("PED-039", "Disco externo 2 TB", 4),
    ("PED-040", "Router WiFi", 4),
]

# Formato: (id_albaran, producto, unidades)
REPOSICIONES = [
    ("ALB-001", "Monitor 24 pulgadas", 8),
    ("ALB-002", "Monitor 27 pulgadas", 6),
    ("ALB-003", "SSD 1 TB", 10),
    ("ALB-004", "Disco externo 2 TB", 6),
    ("ALB-005", "Router WiFi", 5),
    ("ALB-006", "Impresora laser", 4),
    ("ALB-007", "Auriculares USB", 10),
    ("ALB-008", "Webcam Full HD", 8),
    ("ALB-009", "Raton gaming", 10),
    ("ALB-010", "Teclado mecanico", 12),
    ("ALB-011", "Microfono USB", 6),
    ("ALB-012", "Toner negro", 8),
]

NUM_TERMINALES = 3
NUM_REVISORES = 4
NUM_CAJAS = 6

# Duraciones comunes de simulación (segundos reales).
# Cobro: duración de uso de un terminal, no tiempo de espera de stock.
# Reposición: tiempo de preparación ANTES de aplicar cada albarán.
TIEMPO_COBRO = 1.0
TIEMPO_REPOSICION = 2.0

# ============================================================================
# FASE I - CANCELACIONES EN TIEMPO REAL
# ============================================================================

# Formato: (id_solicitud, id_pedido, segundo_de_solicitud)
# Los segundos se interpretan desde el inicio común de la simulación.
# La aceptación depende del estado REAL del pedido cuando llegue la solicitud.
# Hay solicitudes tempranas, tardías, repetidas y a pedidos inexistentes.
CANCELACIONES = [
    ("CAN-001", "PED-001", 0.25),  # Primer lote: cancelar mientras se tramita
    ("CAN-002", "PED-002", 0.45),  # Primer lote: solicitud sobre pedido activo
    ("CAN-003", "PED-003", 0.65),  # Primer lote: puede competir por terminal
    ("CAN-004", "PED-007", 1.35),  # Siguiente pedido de la primera caja
    ("CAN-005", "PED-008", 1.55),  # Siguiente pedido de la segunda caja
    ("CAN-006", "PED-001", 1.75),  # Segunda cancelación sobre PED-001
    ("CAN-007", "PED-999", 2.00),  # Pedido inexistente, debe rechazarse
    ("CAN-008", "PED-040", 8.00),  # Solicitud tardía, no necesariamente válida
]

# Pruebas de aceptación por ESTADO (se añaden a la simulación temporal).
# Formato: (id_prueba, id_pedido_existente, estado_en_que_se_solicita)
# No son instrucciones de implementación; son casos que deben poder
# reproducirse en una ejecución de prueba, independientemente del ordenador.
# Un estado "EN_COBRO" indica que se ha iniciado el cobro, pero todavía no
# se ha confirmado la venta. En ese caso debe aplicarse la política de
# cancelación que se describe en el enunciado (verificación de consistencia).
PRUEBAS_CANCELACION_ESTADO = [
    ("TEST-CAN-01", "PED-001", "PENDIENTE"),
    ("TEST-CAN-02", "PED-040", "ESPERANDO_STOCK"),
    ("TEST-CAN-03", "PED-002", "EN_COBRO"),
    ("TEST-CAN-04", "PED-003", "COMPLETADO"),
]

# ============================================================================
# FASE II - DEVOLUCIONES CONCURRENTES
# ============================================================================

# Formato: (id_devolucion, id_pedido_original, unidades, segundo_de_solicitud)
# La devolución solo será válida si existe una venta efectivamente completada
# y no se devuelve más cantidad que la vendida en total.
# Incluye solicitudes simultáneas sobre la misma venta, exceso de unidades,
# pedido inexistente y devolución repetida por identificador.
DEVOLUCIONES = [
    ("DEV-001", "PED-002", 2, 2.00),
    ("DEV-002", "PED-002", 2, 2.00),  # Compiten por la misma venta
    ("DEV-003", "PED-002", 3, 2.10),  # Puede superar saldo devolvible
    ("DEV-004", "PED-010", 3, 2.50),
    ("DEV-005", "PED-001", 2, 3.00),  # Puede estar cancelado (Fase I)
    ("DEV-006", "PED-999", 1, 3.50),  # Venta inexistente
    ("DEV-004", "PED-010", 3, 4.00),  # Identificador duplicado
    ("DEV-007", "PED-019", 1, 4.50),
]

# ============================================================================
# FASE III - PEDIDOS MULTIPRODUCTO ATÓMICOS
# ============================================================================

# Formato: (id_pedido_compuesto, {producto: unidades})
# Se procesan como nuevos pedidos, además de los pedidos originales.
# Un pedido compuesto solo puede completarse si se pueden vender TODOS
# sus productos; no se permiten ventas parciales de la cesta.
# Incluye cestas con productos comunes, orden inverso, independientes,
# y una cesta que no dispone inicialmente de todas las unidades.
PEDIDOS_COMPUESTOS = [
    ("PED-M001", {"Teclado mecanico": 2, "Raton gaming": 3}),
    ("PED-M002", {"Raton gaming": 2, "Teclado mecanico": 1}),
    ("PED-M003", {"Cable HDMI": 2, "Memoria USB 64 GB": 3}),
    ("PED-M004", {"Monitor 24 pulgadas": 12, "SSD 1 TB": 2}),
    ("PED-M005", {"SSD 1 TB": 2, "Monitor 24 pulgadas": 1}),
    ("PED-M006", {"Impresora laser": 2, "Router WiFi": 2}),
]
