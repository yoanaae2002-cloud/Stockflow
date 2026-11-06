# Stockflow

## Fase 1. Condición de carrera

En esta primera fase se ha implementado un sistema de ventas concurrente utilizando hilos (`threading`), donde cada hilo representa una caja registradora.

Los pedidos se reparten entre las diferentes cajas y cada una comprueba si existe stock suficiente antes de realizar una venta.

### Sección crítica

La sección crítica se encuentra en la comprobación y modificación del inventario:

```python
if Inventario[producto] >= unidades:
    cantidad = Inventario[producto]
    time.sleep(3)
    Inventario[producto] = cantidad - unidades
```

### Problema detectado

Al no utilizar mecanismos de sincronización, varios hilos pueden consultar simultáneamente las mismas unidades disponibles.

Esto puede provocar que dos cajas consideren que existe stock suficiente para realizar sus ventas, aunque entre ambas intenten vender más unidades de las disponibles.

Además, al guardar el stock en la variable `cantidad`, los hilos pueden terminar sobrescribiendo los cambios realizados por otros hilos.

### Conclusión

Provocamos intencionadamente una condición de carrera mediante pausas con `time.sleep()`, facilitando que varios hilos accedan simultáneamente al inventario.

En esta fase no se utiliza ningún mecanismo de bloqueo (`Lock`), ya que el objetivo es observar los problemas que genera el acceso concurrente a un recurso compartido.

# Simulación de tienda con hilos
 
Simulación de una tienda con varias cajas, almacenes y revisores que trabajan
a la vez sobre un inventario compartido.
 
## Mecanismos de sincronización usados
 
| Fase | Mecanismo | Para qué se usa |
|---|---|---|
| 2 | Lock | Proteger el inventario (exclusión mutua) |
| 3 | Semaphore | Limitar a `NUM_TERMINALES` los cobros simultáneos |
| 4 | Condition | Hacer esperar a las cajas sin stock hasta que haya reposición |
| 5 | Barrier | No cerrar hasta que todos los revisores terminen |
| 6 | RLock | Permitir que un método protegido llame a otro método protegido |
 
## Fase 6: refactorización con RLock
 
### Qué se hizo
 
Todo el inventario se movió a la clase `GestorInventario`. El diccionario y su
mecanismo de sincronización ahora son atributos privados de la clase, y los
hilos solo usan sus métodos (`retirar`, `reponer`, `consultar_stock`...).
 
### Operación protegida que llama a otra protegida
 
- `consultar_stock()` está protegida con el lock.
- `hay_stock()` está protegida con el lock y **llama a** `consultar_stock()`.
- `retirar()` está protegida y **llama a** `hay_stock()` varias veces.
Es decir, un mismo hilo entra en una sección protegida y, estando dentro, entra
en otra sección protegida del mismo gestor.
 
### Por qué RLock es necesario
 
Con un `Lock` normal, el mismo hilo **no puede adquirirlo dos veces**. Lo que
pasaría con `retirar()`:
 
1. El hilo entra en `retirar()` y adquiere el lock.
2. Dentro llama a `hay_stock()`, que intenta adquirir **el mismo lock**.
3. El lock ya está ocupado (por ese mismo hilo), así que `hay_stock()` espera a
   que se libere.
4. Pero solo lo liberaría `retirar()`, que está parado esperando a `hay_stock()`.
El hilo se bloquea a sí mismo para siempre: es un **interbloqueo (deadlock)**
de un solo hilo.
 
Un `RLock` (lock reentrante) recuerda **qué hilo lo tiene y cuántas veces lo ha
adquirido**. Si el mismo hilo lo vuelve a pedir, lo deja pasar y aumenta un
contador interno; el lock solo queda libre para los demás hilos cuando ese
contador vuelve a cero. Otros hilos siguen sin poder entrar, así que la
exclusión mutua se mantiene.
 
### Qué se sustituyó
 
Se sustituyó el `Lock` que protegía el inventario por un `RLock`. La
`Condition` de la Fase 4 se construye sobre ese mismo `RLock`
(`threading.Condition(self._lock)`), de modo que `with self._condicion` y
`with self._lock` adquieren **el mismo candado** y no hay dos mecanismos
distintos protegiendo los mismos datos.
 
El `Semaphore` y el `Barrier` no cambian: no protegen el inventario, así que
no necesitan ser reentrantes.
 
## Ejecución
 
```
python fase6_gestor.py
```
 
Requiere `datos.py` en la misma carpeta.
 