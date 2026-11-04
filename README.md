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