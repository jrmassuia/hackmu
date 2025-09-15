import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  # Biblioteca para manipular imagens

class MenuGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Tk()
        self.root.title("Menu")
        self.root.geometry("250x300")  # Reduzir a resolução da janela
        self.root.minsize(250, 370)  # Tamanho mínimo da janela
        self.root.configure(bg="#f0f0f0")  # Cor de fundo

        # Variável para armazenar a opção geral selecionada
        self.opcao_geral = tk.StringVar(value='autopick')

        self.autopick_telas = None
        self._criar_interface()

    def _criar_interface(self):
        frame_hack = tk.Frame(self.root, bg="#f0f0f0")
        frame_hack.pack(pady=5, fill='x')  # Reduzir o espaçamento

        tk.Label(frame_hack, text="Escolha um hack:", bg="#f0f0f0", font=("Arial", 9)).grid(row=0, column=0, columnspan=3, sticky='w')

        opcoes_menu_geral = [
            ('Pick(1)', 'autopick'),
            ('SD(2)', 'sd'),
            ('Refinar(3)', 'refinar'),
            ('Upar(4)', 'upar'),
            ('Pote(5)', 'pote')
        ]

        # Ajustar para que apenas três Radiobuttons fiquem por linha
        for idx, (texto, valor) in enumerate(opcoes_menu_geral):
            row = idx // 3  # Divisão inteira para controlar a linha (3 por linha)
            col = idx % 3   # Alternar entre coluna 0, 1 e 2
            tk.Radiobutton(frame_hack, text=texto, variable=self.opcao_geral, value=valor, font=("Arial", 8)).grid(row=row+1, column=col, padx=5, pady=2)

        self.frame_autopick = tk.Frame(self.root)
        self._criar_opcoes_menu(self.frame_autopick)
        self.frame_autopick.pack(pady=5, fill='both', expand=True)

        self.botao_confirmar = tk.Button(self.root, text="Iniciar", command=self._confirmar_selecao, bg="#4CAF50", fg="white", font=("Arial", 10))
        self.botao_confirmar.pack(pady=10)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _criar_opcoes_menu(self, parent):
        self.autopick_telas = {}
        tk.Label(parent, text="Opções:", font=("Arial", 9)).grid(row=0, column=0, columnspan=1, sticky='w')

        telas = [('Tela 1', {}), ('Tela 2', {}), ('Tela 3', {})]

        for idx, (tela_nome, tela_vars) in enumerate(telas):
            self.autopick_telas[tela_nome] = {
                'ativo': tk.IntVar(),
                'joias': tk.IntVar(),
                'limpa_pk': tk.IntVar(),
                'k3': tk.IntVar(),
                'atlans': tk.IntVar(),
                'sd_small': tk.IntVar(),
                'sd_media': tk.IntVar(),
                'ref_gem': tk.IntVar(),
                'ref_peq': tk.IntVar()
            }
            tk.Label(parent, text=tela_nome, font=("Arial", 8)).grid(row=1, column=idx, padx=5, sticky='w')

            tk.Checkbutton(parent, text='Ativar', variable=self.autopick_telas[tela_nome]['ativo'], font=("Arial", 7)).grid(row=2, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='Joias', variable=self.autopick_telas[tela_nome]['joias'], font=("Arial", 7)).grid(row=3, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='Limpa PK', variable=self.autopick_telas[tela_nome]['limpa_pk'], font=("Arial", 7)).grid(row=4, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='K3', variable=self.autopick_telas[tela_nome]['k3'], font=("Arial", 7)).grid(row=5, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='Atlans', variable=self.autopick_telas[tela_nome]['atlans'], font=("Arial", 7)).grid(row=6, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='SD Small', variable=self.autopick_telas[tela_nome]['sd_small'], font=("Arial", 7)).grid(row=7, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='SD Media', variable=self.autopick_telas[tela_nome]['sd_media'], font=("Arial", 7)).grid(row=8, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='Ref. Gem', variable=self.autopick_telas[tela_nome]['ref_gem'], font=("Arial", 7)).grid(row=9, column=idx, padx=5, sticky='w')
            tk.Checkbutton(parent, text='Ref. Peq', variable=self.autopick_telas[tela_nome]['ref_peq'], font=("Arial", 7)).grid(row=10, column=idx, padx=5, sticky='w')

    def _confirmar_selecao(self):
        opcao_geral = self.opcao_geral.get()

        if opcao_geral == '':
            messagebox.showwarning("Seleção Inválida", "Por favor, selecione uma opção.")
            return

        # if opcao_geral == 'autopick':
        autopick_selecionado = {
            '[1/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 1']),
            '[2/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 2']),
            '[3/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 3'])
        }
        if all(not selecionado['ativo'] for selecionado in autopick_selecionado.values()):
            messagebox.showwarning("Seleção Inválida", "Por favor, ative pelo menos uma tela para o Autopick.")
            return

        self.app.menu_autopick = autopick_selecionado
        # else:
        #     self.app.menu_autopick = {}

        self.app.menu_geral = opcao_geral
        self.root.quit()

    def _get_autopick_selecoes(self, tela_vars):
        return {
            'ativo': tela_vars['ativo'].get(),
            'joias': tela_vars['joias'].get(),
            'limpa_pk': tela_vars['limpa_pk'].get(),
            'k3': tela_vars['k3'].get(),
            'atlans': tela_vars['atlans'].get(),
            'sd_small': tela_vars['sd_small'].get(),
            'sd_media': tela_vars['sd_media'].get(),
            'ref_gem': tela_vars['ref_gem'].get(),
            'ref_peq': tela_vars['ref_peq'].get()
        }

    def run(self):
        self.root.mainloop()
