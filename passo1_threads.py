import threading
import queue
import time
import random
import timeit

TOTAL_PEDIDOS = 40
MAX_FILA = 30
BASE_NUMERO = 10**14     
VAGAS_FORNO = 3
REPETICOES = 3            


def eh_primo(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


class Chef(threading.Thread):
    """PRODUTOR: gera a pizza (numero primo), assa no forno e enfileira."""

    def __init__(self, id_chef, fila, forno_sem, condition, lock, estado):
        super().__init__(daemon=True)
        self.id_chef = id_chef
        self.fila = fila
        self.forno_sem = forno_sem
        self.condition = condition
        self.lock = lock
        self.estado = estado

    def run(self):
        while True:
            with self.lock:
                if self.estado["produzidos"] >= TOTAL_PEDIDOS:
                    break
                self.estado["produzidos"] += 1

            numero = BASE_NUMERO + random.randint(1, 10_000_000)
            while not eh_primo(numero):
                numero += random.randint(1, 1000)

            # SEMAFORO: forno comporta no maximo 3 pizzas simultaneas
            self.forno_sem.acquire()
            time.sleep(0.02)          # tempo de forno
            self.forno_sem.release()

            # FILA: entrega o pedido ao consumidor
            self.fila.put(numero)
            with self.condition:
                self.condition.notify_all()


class Entregador(threading.Thread):
    """CONSUMIDOR: espera na Condition e retira pedidos da fila."""

    def __init__(self, id_entregador, fila, condition, expediente, estado):
        super().__init__(daemon=True)
        self.id_entregador = id_entregador
        self.fila = fila
        self.condition = condition
        self.expediente = expediente
        self.estado = estado

    def run(self):
        while True:
            with self.condition:
                while self.fila.empty():
                    if self.expediente.is_set():
                        return
                    self.condition.wait(timeout=0.1)
                if self.fila.empty():
                    if self.expediente.is_set():
                        return
                    continue
                pizza = self.fila.get()
            with self.estado["lock_entregas"]:
                self.estado["entregues"] += 1
            self.fila.task_done()


def simular_pizzaria(num_chefs, num_entregadores):
    fila = queue.Queue(maxsize=MAX_FILA)
    forno_sem = threading.Semaphore(VAGAS_FORNO)
    condition = threading.Condition()
    expediente = threading.Event()          # EVENTO: fim do expediente
    lock = threading.Lock()
    estado = {"produzidos": 0, "entregues": 0,
              "lock_entregas": threading.Lock()}

    inicio = timeit.default_timer()

    chefs = [Chef(i, fila, forno_sem, condition, lock, estado)
             for i in range(num_chefs)]
    entregadores = [Entregador(i, fila, condition, expediente, estado)
                    for i in range(num_entregadores)]

    for e in entregadores:
        e.start()
    for c in chefs:
        c.start()

    for c in chefs:
        c.join()

    fila.join()

    expediente.set()
    with condition:
        condition.notify_all()

    for e in entregadores:
        e.join(timeout=3)

    tempo = timeit.default_timer() - inicio
    return tempo, estado["produzidos"], estado["entregues"]



if __name__ == "__main__":
    configuracoes = [(1, 1), (2, 2), (4, 4), (8, 8)]
    tempos = []
    linhas_saida = []

    print("=== VERSAO 1: THREADING (GIL ativo) ===")
    print(f"TOTAL_PEDIDOS={TOTAL_PEDIDOS}  BASE_NUMERO=10^14  "
          f"FORNO={VAGAS_FORNO}  MAX_FILA={MAX_FILA}  "
          f"mediana de {REPETICOES} execucoes\n")

    for c, e in configuracoes:
        medicoes = []
        for _ in range(REPETICOES):
            t, prod, entr = simular_pizzaria(c, e)
            medicoes.append(t)
        medicoes.sort()
        tempo = medicoes[len(medicoes) // 2]
        tempos.append(tempo)
        linha = (f"{c} chef(s) + {e} entregador(es): {tempo:.4f}s  "
                 f"(produzidas: {prod} | entregues: {entr})")
        print(linha)
        linhas_saida.append(linha)

    speedups = [tempos[0] / t for t in tempos]

    print("\nChefs | Entregadores | Threads | Tempo(s) | Speedup")
    print("-" * 52)
    for i, (c, e) in enumerate(configuracoes):
        print(f"  {c}   |      {e}       |   {c+e:>2}    | {tempos[i]:>7.4f}  | {speedups[i]:.4f}")


