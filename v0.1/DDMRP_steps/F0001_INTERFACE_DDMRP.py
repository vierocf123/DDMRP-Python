import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Optional, Dict, Any
import datetime

def aviso_final():
    # mostra uma caixa de aviso
    messagebox.showinfo("DDMRP", "Execução concluída com sucesso!")

def ler_parametros_gui() -> Optional[Dict[str, Any]]:
    """
    Abre uma GUI para coletar 3 inteiros e um caminho de pasta.
    Retorna um dicionário {'var1': int, 'var2': int, 'var3': int, 'pasta': str}
    ou None se o usuário cancelar.
    """
    # --- callbacks e validações internas ---
    def escolher_pasta():
        pasta = filedialog.askdirectory(title="Selecione a pasta")
        if pasta:
            var_pasta.set(pasta)

    def validar_inteiro(valor: str, nome: str):
        try:
            return int(valor)
        except ValueError:
            messagebox.showerror("Valor inválido", f"O campo '{nome}' deve ser um inteiro.")
            return None

    def confirmar():
        v1 = validar_inteiro(var1.get(), "Variável 1")
        if v1 is None: return
        v2 = validar_inteiro(var2.get(), "Variável 2")
        if v2 is None: return
        v3 = validar_inteiro(var3.get(), "Variável 3")
        if v3 is None: return

        pasta = var_pasta.get().strip()
        if not pasta:
            messagebox.showerror("Pasta não informada", "Selecione um caminho de pasta.")
            return
        if not os.path.isdir(pasta):
            messagebox.showerror("Pasta inválida", "O caminho informado não é uma pasta válida.")
            return

        resultados["value"] = {"dia": v1, "mes": v2, "ano": v3, "pasta": pasta}
        root.destroy()

    def cancelar():
        resultados["value"] = None
        root.destroy()

    # --- janela ---
    root = tk.Tk()
    root.title("Parâmetros do Script")
    root.resizable(False, False)

    conteudo = ttk.Frame(root, padding=12)
    conteudo.grid(row=0, column=0, sticky="nsew")

    #pega a data de hoje
    hoje = datetime.date.today()

    var1 = tk.StringVar(value=str(hoje.day))
    var2 = tk.StringVar(value=str(hoje.month))
    var3 = tk.StringVar(value=str(hoje.year))
    var_pasta = tk.StringVar()

    ttk.Label(conteudo, text="DIA:").grid(row=0, column=0, sticky="w", pady=(0,4))
    ttk.Entry(conteudo, textvariable=var1, width=20).grid(row=0, column=1, sticky="ew", pady=(0,4))

    ttk.Label(conteudo, text="MÊS:").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(conteudo, textvariable=var2, width=20).grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(conteudo, text="ANO:").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(conteudo, textvariable=var3, width=20).grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(conteudo, text="Diretório:").grid(row=3, column=0, sticky="w", pady=4)
    linha_pasta = ttk.Frame(conteudo)
    linha_pasta.grid(row=3, column=1, sticky="ew", pady=4)
    ttk.Entry(linha_pasta, textvariable=var_pasta, width=32).pack(side="left", fill="x", expand=True)
    ttk.Button(linha_pasta, text="Procurar…", command=escolher_pasta).pack(side="left", padx=(6,0))

    botoes = ttk.Frame(conteudo)
    botoes.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8,0))
    ttk.Button(botoes, text="Cancelar", command=cancelar).pack(side="right", padx=(0,6))
    ttk.Button(botoes, text="Confirmar", command=confirmar).pack(side="right")

    conteudo.columnconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    resultados: Dict[str, Any] = {"value": None}
    root.mainloop()
    return resultados["value"]


# Execução direta para teste rápido
if __name__ == "__main__":
    dados = ler_parametros_gui()
