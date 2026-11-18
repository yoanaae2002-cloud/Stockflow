import threading
import time
from datos import (STOCK_INICIAL, NUM_CAJAS, NUM_TERMINALES, NUM_REVISORES, PEDIDOS, REPOSICIONES,TIEMPO_COBRO,TIEMPO_REPOSICION,CANCELACIONES)


NUM_ALMACENES = 1
ESTADOS = {}
for pedido in PEDIDOS:
    id_pedido,producto,unidades = pedido
    ESTADOS[id_pedido] = "PENDIENTE"

# ======================================================================
# ORDEN GLOBAL DE RECURSOS: 1º inventario, 2º terminales, 3º barrera.
# Ningún hilo mantiene uno mientras pide otro (evita deadlock).
# ======================================================================


class GestorInventario:
    """Todo lo que toca el inventario pasa por esta clase.
    Para añadir una operación nueva: usar 'with self._lock:' y listo.
    Si llama a otro método protegido, funciona gracias al RLock."""

    def __init__(self, stock_inicial, num_almacenes):
        self._inventario = stock_inicial.copy()

        # RLock y NO Lock: retirar() llama a hay_stock()
        self._lock = threading.RLock()

       
        self._condicion = threading.Condition(self._lock)

        # Cuántos almacenes pueden aún traer mercancía. Sin esto, una caja
        # que espere un producto sin reposición dormiría para siempre.
        self._almacenes_activos = num_almacenes

    def consultar_stock(self, producto):
        with self._lock:
            return self._inventario[producto]

    def hay_stock(self, producto, unidades):
        with self._lock:  # reentrada
            return self.consultar_stock(producto) >= unidades

    def retirar(self, caja, numero, producto, unidades):
        """Devuelve las unidades que quedan, o None si no hay stock y ya no
        llegarán reposiciones.  quedan puede ser 0, por eso fuera se
        comprueba 'is not None' y NO 'if quedan'."""
        with self._condicion:

            # REGLA: while y NO if. Hay que volver a comprobar al despertar.
            while not self.hay_stock(producto, unidades) and self._almacenes_activos > 0:
                ESTADOS[numero] = "ESPERANDO_STOCK"

                print(f"{caja}: Sin stock de {producto} ({numero}), esperando reposición...")

                # wait() suelta el lock mientras duerme.
                self._condicion.wait()

            if self.hay_stock(producto, unidades):
                self._inventario[producto] -= unidades
                return self._inventario[producto]

            return None

    def reponer(self, almacen, numero, producto, unidades):
        with self._condicion:
            self._inventario[producto] += unidades

            # notify_all y NO notify: cada caja comprueba su propio producto.
            self._condicion.notify_all()

  
        print(f"{almacen}: Repuestas {unidades} unidades de {producto} ({numero})")

    def almacen_termina(self):
        with self._condicion:
            self._almacenes_activos -= 1

            # Despierta a las cajas por si ya no puede llegar más stock
            self._condicion.notify_all()

    def catalogo(self):
        with self._lock:
            return list(self._inventario.keys())

    def resumen(self):
        with self._lock:
            copia = self._inventario.copy()

        print("\nINVENTARIO FINAL:")
        for producto, unidades in copia.items():
            print(f"{producto}: {unidades}")
        for pedido, estado in ESTADOS.items():
             print(f"{pedido}: {estado}")


gestor = GestorInventario(STOCK_INICIAL, NUM_ALMACENES)

semaforo_terminales = threading.Semaphore(NUM_TERMINALES)


def cierre():
    # Acción de la barrera: la ejecuta UN solo hilo, cuando ya han llegado
    # todos los revisores y antes de liberarlos.
    print("\nTodos los revisores han terminado. Cierre autorizado.")
    gestor.resumen()



barrera_revision = threading.Barrier(NUM_REVISORES, action=cierre)


def procesar_venta(caja, pedidos):
    


    for numero, producto, unidades in pedidos:


        # El lock del inventario ya está SOLTADO cuando retirar() devuelve.
        quedan = gestor.retirar(caja, numero, producto, unidades)


        

        if quedan is not None and (ESTADOS[numero] != "CANCELADO"):
            print(f"{caja}: Hay stock suficiente para {producto} ({numero})")

            # NO meter el cobro dentro de retirar(): mantendría el lock del
            # inventario durante el sleep y abriría la puerta al deadlock.
            print(f"{caja}: Esperando terminal de cobro...")
            with semaforo_terminales:
                
                ESTADOS[numero] = "EN_COBRO"
                print(f"{caja}: OBTIENE un terminal ({numero})")
                time.sleep(TIEMPO_COBRO)  #duración del cobro
                print(f"{caja}: LIBERA el terminal ({numero})")



            ESTADOS[numero] = "COMPLETADO"
            print(f"{caja}: Venta realizada correctamente, quedan {quedan} unidades de {producto}")


        else:
            ESTADOS[numero] = "SIN STOCK"
            print(f"{caja}: Stock insuficiente para {producto} ({numero}), no habrá más reposiciones")


lock_cancelacion = threading.Lock()
def cancelar_pedido(id_solicitud,id_pedido,segundo_solicitud):
    with lock_cancelacion:
        for pedido,estado in ESTADOS.items():
            if pedido == id_pedido:

                if estado == "PENDIENTE":
                    print(f"{id_solicitud} : Cancelando pedido {pedido}")
                    time.sleep(segundo_solicitud)
                    ESTADOS[pedido] = "CANCELADO"
                    print(f"Pedido  {pedido} cancelado correctamente")

        
            



def procesar_reposicion(almacen, reposiciones):

    for numero, producto, unidades in reposiciones:
        time.sleep(TIEMPO_REPOSICION)  #duración de cada reposición
        gestor.reponer(almacen, numero, producto, unidades)

    # Solo se ejecuta al terminar TODOS los albaranes de este almacén
    gestor.almacen_termina()


def revisar_catalogo(revisor, productos):

    for producto in productos:
        time.sleep(0.5) 

        #criterio de revisión 
        if gestor.consultar_stock(producto) >= 0:
            print(f"{revisor}: {producto} revisado correctamente")
        else:
            print(f"{revisor}: ERROR, stock negativo en {producto}")

    print(f"{revisor}: Ha terminado su revisión, espera en la barrera...")

    # Se llega aquí SIN ningún lock cogido. Cuando llega el último revisor,
    # la barrera ejecuta cierre() una sola vez y libera a todos.
    barrera_revision.wait()


hilos = []

for i in range(NUM_CAJAS):
    pedidos_caja = PEDIDOS[i::NUM_CAJAS]
    hilo = threading.Thread(target=procesar_venta, args=("Caja " + str(i + 1), pedidos_caja))
    hilos.append(hilo)
    hilo.start()

for i in range(NUM_ALMACENES):
    reposiciones_almacen = REPOSICIONES[i::NUM_ALMACENES]
    hilo = threading.Thread(target=procesar_reposicion, args=("Almacén " + str(i + 1), reposiciones_almacen))
    hilos.append(hilo)
    hilo.start()

for cancelacion in CANCELACIONES:
    id_solicitud,id_pedido,segundo_solicitud = cancelacion
    hilo = threading.Thread(target=cancelar_pedido, args=(id_solicitud,id_pedido,segundo_solicitud) )
    hilos.append(hilo)
    hilo.start()



# Los revisores empiezan DESPUÉS de estos join(), así que durante la
# revisión el inventario ya no cambia.
for hilo in hilos:
    hilo.join()

print("\n--- REVISIÓN FINAL DEL CATÁLOGO ---")

catalogo = gestor.catalogo()
revisores = []

for i in range(NUM_REVISORES):
    productos_revisor = catalogo[i::NUM_REVISORES]
    hilo = threading.Thread(target=revisar_catalogo, args=("Revisor " + str(i + 1), productos_revisor))
    revisores.append(hilo)
    hilo.start()

for hilo in revisores:
    hilo.join()

