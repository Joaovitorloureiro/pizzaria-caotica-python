# Pizzaria Caótica — Concorrência em Python

Atividade da disciplina **Programação Distribuída e Concorrente** — Ciências da Computação, Universidade de Vila Velha (UVV).
Desenvolvido em dupla: João Vitor de Carvalho Loureiro e Murilo Cipriano Carvalho.

## O problema
Uma pizzaria simulada no padrão **produtor-consumidor**:
- **Chefs (produtores):** "preparam a pizza" calculando um número primo a partir de 10^14 (trabalho pesado de CPU), assam no forno e colocam o pedido na fila.
- **Forno:** comporta no máximo 3 pizzas ao mesmo tempo (`threading.Semaphore(3)`).
- **Fila de pedidos:** `queue.Queue(maxsize=30)`; o chef bloqueia se a fila estiver cheia.
- **Entregadores (consumidores):** esperam em `threading.Condition` até haver pedido na fila.
- **Fim do expediente:** `threading.Event`; contadores protegidos por `threading.Lock`.

Configurações testadas: 1, 2, 4 e 8 chefs (com o mesmo número de entregadores), 40 pedidos, mediana de 3 execuções.

## Arquivos
| Arquivo | Versão |
|---|---|
| `passo1_threads.py` | Versão 1 — só `threading` (limitada pelo GIL) |
| `passo2_processos.py` | Versão 2 — o cálculo pesado vai para `concurrent.futures.ProcessPoolExecutor`; fila, semáforo e condição continuam iguais |

## Resultado (8 núcleos físicos)
| Chefs | Speedup com threads | Speedup com processos |
|---|---|---|
| 8 | 1,12x | 6,72x |

Com threads, o GIL deixa só uma thread executar bytecode por vez, então o speedup praticamente não cresce. Com processos, a fração serial estimada pela **Lei de Amdahl** caiu de 0,93 para 0,06.

## Como executar
Requisito: Python 3.

```bash
python passo1_threads.py
python passo2_processos.py
```
