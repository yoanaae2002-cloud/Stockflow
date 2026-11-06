# StockFlow · Gestión concurrente del stock de una tienda

Práctica UD2 · Programación de Servicios y Procesos · 2º DAM

## Descripción general

StockFlow simula una tienda en la que varias **cajas** procesan pedidos mientras
uno o varios **almacenes** reponen mercancía. Todos trabajan sobre el mismo
inventario, así que hay que sincronizar los hilos para que el stock nunca quede
en valores incoherentes. Al terminar, varios **revisores** comprueban el
catálogo y solo cuando todos acaban se muestra el resumen final.

El proyecto ha evolucionado por fases, desde una primera versión con una
condición de carrera hasta una solución sincronizada con `Lock`, `RLock`,
`Semaphore`, `Condition` y `Barrier`.

## Cómo ejecutar la aplicación

Requiere Python 3 y no necesita librerías externas.

```
python main.py
```

La ejecución dura unos 52 segundos con la configuración por defecto:
1 almacén (`NUM_ALMACENES = 1`), cobro de 1 s, reposición de 4 s y revisión
de 0.5 s por producto. Estos valores se cambian directamente en `main.py`
(`NUM_ALMACENES` al principio del archivo y los `time.sleep()` en
`procesar_venta`, `procesar_reposicion` y `revisar_catalogo`). Las demás
constantes (`NUM_CAJAS`, `NUM_TERMINALES`, `NUM_REVISORES`) se leen de
`datos.py`, que no se ha modificado.

## Estructura de archivos

```
Stockflow/
├── main.py       Programa principal (versión final, Fase 7)
├── datos.py      Datos de partida entregados (no modificado)
├── README.md     Esta documentación
└── .gitignore
```

## Fase 1: la condición de carrera inicial

La primera versión (rama `feature/race-condition`) no usa ningún `Lock`. Cada
caja hace esto:

```python
if Inventario[producto] >= unidades:
    cantidad = Inventario[producto]
    time.sleep(3)
    Inventario[producto] = cantidad - unidades
```

### Sección crítica

Es todo el bloque de comprobar el stock y descontar las unidades. Las dos
operaciones tienen que ejecutarse juntas, sin que otro hilo las intercale.

### Qué falla

Varios hilos pueden leer el mismo stock a la vez. Si dos cajas ven que hay
unidades suficientes y las dos descuentan, entre ambas venden más de lo que
había. Además, como el stock se guarda en la variable `cantidad`, una caja puede
sobrescribir el cambio que acaba de hacer otra (una actualización perdida).

### Resultado observado

El **Router WiFi** empieza con 6 unidades y los pedidos PED-025 (3 unidades) y
PED-040 (4 unidades) suman 7. En las 3 ejecuciones de la Fase 1:

- Las dos cajas dijeron "Hay stock suficiente" y **vendieron las dos**.
- Se realizaron las 40 ventas y no se rechazó ninguna.
- El stock final del Router WiFi fue **2**, un valor incoherente: se vendieron 7
  unidades de 6 disponibles y, además, la cuenta no cuadra.

Para facilitar que ocurra se usan pausas con `time.sleep()`, que alargan el
tiempo entre leer y escribir el stock.

## Mecanismos de sincronización

| Mecanismo | Dónde se usa | Para qué |
|---|---|---|
| `Lock` (Fase 2) | Inventario | Exclusión mutua: solo un hilo comprueba y descuenta a la vez |
| `Semaphore` (Fase 3) | Terminales de cobro | Limita a `NUM_TERMINALES` los cobros simultáneos |
| `Condition` (Fase 4) | Reposición | Las cajas sin stock esperan sin gastar CPU hasta que llega mercancía |
| `Barrier` (Fase 5) | Revisión final | Nadie cierra hasta que todos los revisores terminan |
| `RLock` (Fase 6) | Clase `GestorInventario` | Permite que un método protegido llame a otro método protegido |

`Lock` y `Semaphore` resuelven problemas distintos: el `Lock` protege un dato
compartido (solo entra uno), mientras que el `Semaphore` limita un recurso del
que hay varias unidades (3 terminales para 6 cajas).

### Lock

Protege conjuntamente la comprobación del stock y el descuento. Todo lo que no
necesita protección (el cobro, los `print`, las esperas) se hace fuera.

### Semaphore

`Semaphore(NUM_TERMINALES)`. Cada caja lo adquiere para cobrar y lo libera al
terminar, y el programa muestra cuándo obtiene y libera un terminal.

### Condition

Cuando una caja no tiene stock, llama a `wait()` y se duerme, soltando el lock
mientras tanto. No hay bucle de espera activa. Cuando el almacén repone, llama
a `notify_all()` y todas las cajas dormidas se despiertan y **vuelven a
comprobar** si hay stock, por eso se usa `while` y no `if`: otra caja puede
haberse llevado las unidades antes.

El almacén también avisa cuando termina todas sus reposiciones
(`almacenes_activos`). Así, una caja que espera un producto que ya no se va a
reponer no se queda dormida para siempre: se despierta, lo da por insuficiente
y sigue.

### Barrier

`Barrier(NUM_REVISORES, action=cierre)`. Cada revisor comprueba su parte del
catálogo (el reparto es `catalogo[i::NUM_REVISORES]`) y llega a la barrera. Cuando
llega el último, la barrera ejecuta `cierre()` una sola vez, que muestra el
resumen final, y libera a todos.

## Fase 6: por qué RLock es necesario

Todo el inventario está en la clase `GestorInventario`. Tiene operaciones
protegidas que llaman a otras operaciones protegidas del mismo gestor:

- `consultar_stock()` está protegida con el lock.
- `hay_stock()` está protegida y **llama a** `consultar_stock()`.
- `retirar()` está protegida y **llama a** `hay_stock()`.

Con un `Lock` normal, el mismo hilo **no puede adquirirlo dos veces**:

1. El hilo entra en `retirar()` y adquiere el lock.
2. Dentro llama a `hay_stock()`, que intenta adquirir el mismo lock.
3. El lock ya está ocupado (por ese mismo hilo), así que `hay_stock()` espera.
4. Solo lo liberaría `retirar()`, que está parado esperando a `hay_stock()`.

El hilo se bloquea a sí mismo para siempre. Un `RLock` recuerda qué hilo lo tiene
y cuántas veces lo ha adquirido: si el mismo hilo lo pide otra vez, lo deja
pasar, y solo queda libre para los demás hilos cuando el contador vuelve a cero.
La exclusión mutua se mantiene, porque otros hilos siguen sin poder entrar.

La `Condition` se construye sobre ese mismo `RLock`
(`threading.Condition(self._lock)`), de modo que `with self._condicion` y
`with self._lock` adquieren el mismo candado y no hay dos mecanismos distintos
protegiendo los mismos datos. El `Semaphore` y el `Barrier` no protegen el
inventario, así que no necesitan ser reentrantes.

## Fase 7: prevención de deadlock

### Recursos que usa cada operación

| Operación | Recurso | ¿Mantiene el lock durante algo lento? |
|---|---|---|
| `retirar` (caja) | RLock / Condition del inventario | No, `wait()` lo suelta mientras duerme |
| Cobro (caja) | Semaphore de terminales | No, se hace sin el lock del inventario |
| `reponer` (almacén) | RLock / Condition del inventario | No, el `sleep` y el `print` van fuera |
| `almacen_termina` | RLock / Condition del inventario | No |
| `consultar_stock`, `catalogo`, `resumen` | RLock del inventario | No, `resumen` copia dentro e imprime fuera |
| Revisión | Barrier | No, se llega a la barrera sin ningún lock |

### Orden de recursos

Si un hilo necesitara varios recursos a la vez, debe pedirlos siempre en este
orden: **1º inventario, 2º terminales, 3º barrera**. Además, en este programa
ningún hilo mantiene un recurso mientras pide otro: `retirar()` termina y suelta
el lock del inventario antes de que la caja pida un terminal.

La única excepción a "no hacer E/S con el lock cogido" es el `print` de "esperando
reposición" en `retirar()`, que tiene que salir antes de dormirse. Es muy breve y
`wait()` suelta el lock enseguida.

### Posible deadlock

Si la caja cobrara **dentro** de la sección crítica del inventario, o si el
cobro necesitara volver a tocar el inventario estando ya con un terminal:

- La Caja A tiene el lock del inventario y espera un terminal.
- Las cajas B, C y D tienen los 3 terminales y necesitan el lock del inventario
  para confirmar la venta.
- A espera un terminal que tienen B, C y D, y B, C y D esperan un lock que tiene A.

Nadie puede avanzar: es una espera circular.

Otros dos casos parecidos que también se evitan:

- **Esperar en la barrera con el lock cogido.** Los demás revisores no podrían
  consultar el stock y la barrera nunca se completaría.
- **Una caja esperando una reposición que nunca llega.** Se evita con
  `almacenes_activos`.

### Cómo se evita

1. **Se rompe la espera circular**: el cobro se hace fuera del lock del
   inventario, así que nadie retiene el lock y pide un terminal a la vez.
2. **Orden coherente** de adquisición si hicieran falta varios recursos.
3. **Locks cortos**: sin `sleep`, cobros ni E/S dentro de los bloques protegidos
   (salvo el `print` indicado arriba).
4. **`wait()` libera el lock** mientras la caja duerme, así el almacén puede
   entrar a reponer.

## Pruebas realizadas y resultados

Las pruebas de la Fase 1 y la Fase 2 se hicieron ejecutando cada versión 3 veces.
Las de la versión final se hicieron ejecutando `main.py` 3 veces con la
configuración por defecto. El resultado fue el mismo en todas las ejecuciones.

| Prueba obligatoria | Resultado |
|---|---|
| Mostrar una condición de carrera antes de sincronizar | Fase 1: el Router WiFi termina con 2 unidades y se venden 7 de 6 disponibles |
| Comprobar que Lock corrige el acceso concurrente al stock | Fase 2 (3 ejecuciones): el Router WiFi termina con **3** unidades, se rechaza la venta que no cabe (39 ventas realizadas y 1 rechazada) y no hay stocks negativos |
| Más cajas que terminales | 6 cajas y 3 terminales: nunca hay más de **3** terminales en uso a la vez |
| Una venta que espera a una reposición | La Caja 4 espera con el pedido PED-040 (4 unidades de Router WiFi) porque solo quedan 3 |
| Una reposición permite continuar a una caja en espera | Al llegar ALB-005 (+5 unidades) la Caja 4 se despierta, comprueba y completa la venta |
| Los revisores esperan en la Barrier | Los 4 revisores muestran "espera en la barrera" antes de "Cierre autorizado" |
| Varias ejecuciones sin stock negativo | 3 ejecuciones: 40 cobros, 0 ventas rechazadas, 0 errores, 0 stocks negativos y resumen impreso una sola vez |

### Notas sobre la salida

- La salida **no es idéntica** entre ejecuciones, porque depende de cómo
  planifique los hilos el sistema operativo. El resultado final sí lo es.
- El mensaje "esperando reposición" puede repetirse: la caja se despierta con
  cada reposición, comprueba su producto y, si todavía no hay stock, vuelve a
  dormirse.
- A veces dos mensajes de cajas distintas aparecen en la misma línea, porque
  varios hilos hacen `print` a la vez. No afecta al resultado.

## Trabajo con Git

Se ha seguido GitFlow. Cada funcionalidad se desarrolló en una rama `feature`
creada desde `develop` y se integró en `develop` al terminar:

| Rama | Contenido |
|---|---|
| `feature/race-condition` | Fase 1: condición de carrera |
| `feature/lock-inventario` | Fase 2: Lock |
| `feature/semaphore-terminales` | Fase 3: Semaphore |
| `feature/condition-reposicion` | Fase 4: Condition |
| `feature/barrier-inventario` | Fase 5: Barrier |
| `feature/rlock-gestor` | Fase 6: clase y RLock |
| `feature/documentacion` | Fase 7 y documentación |

`main` contiene la versión final, integrada desde `develop`.