import tkinter as tk
from tkinter import messagebox, ttk

class MenuGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Tk()
        self.root.title("Menu Interativo")
        self.root.geometry("350x500")
        # self.root.minsize(600, 500)
        self.root.configure(bg="#2b2b2b")

        self.autopick_telas = None
        self._criar_interface()

    def _criar_interface(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        titulo = tk.Label(self.root, text="Menu de Configuração", font=("Helvetica", 16, "bold"), fg="white", bg="#2b2b2b")
        titulo.grid(row=0, column=0, pady=10, sticky="n")

        estilo_frame = ttk.Style()
        estilo_frame.configure("Custom.TLabelframe", background="#3c3f41", foreground="white")
        estilo_frame.configure("Custom.TLabelframe.Label", font=("Arial", 10, "bold"))

        self.frame_autopick = ttk.LabelFrame(self.root, text="Configurações por Tela", style="Custom.TLabelframe")
        self.frame_autopick.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self._criar_opcoes_menu(self.frame_autopick)

        self.botao_confirmar = tk.Button(self.root, text="Iniciar", command=self._confirmar_selecao,
                                         bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.botao_confirmar.grid(row=2, column=0, pady=(0, 10))

    def _criar_opcoes_menu(self, parent):
        self.autopick_telas = {}
        telas = [('Tela 1', {}), ('Tela 2', {}), ('Tela 3', {})]
        opcoes = [
            ('joias', 'Pick Joias'),
            ('limpa_pk', 'Limpar PK'),
            ('pickKanturu', 'Pick Kant.'),
            ('atlans', 'Pick Atlans'),
            ('sd_small', 'SD Small'),
            ('sd_media', 'SD Media'),
            ('ref_gem', 'Ref. Gem'),
            ('ref_peq', 'Ref. Peq'),
            ('upar', 'AutoUp'),
            ('buf', 'Buf'),
            ('pk', 'Pklizar'),
            ('recrutar', 'Recrutar')
        ]

        for idx, (tela_nome, _) in enumerate(telas):
            frame_tela = tk.Frame(parent, bg="#3c3f41")
            frame_tela.grid(row=0, column=idx, padx=10, pady=5, sticky="n")
            tk.Label(frame_tela, text=tela_nome, font=("Arial", 10, "bold"), bg="#3c3f41", fg="white").pack()

            self.autopick_telas[tela_nome] = {k: tk.IntVar() for k, _ in [('ativo', 'Ativo')] + opcoes}

            def gerar_callback(tela):
                return lambda *_: self.autopick_telas[tela]['ativo'].set(1)

            tk.Checkbutton(frame_tela, text='Ativo', variable=self.autopick_telas[tela_nome]['ativo'],
                           font=("Arial", 8), bg="#3c3f41", fg="white", selectcolor="#4CAF50",
                           command=gerar_callback(tela_nome)).pack(anchor='w')

            for var_name, label in opcoes:
                cb = tk.Checkbutton(frame_tela, text=label, variable=self.autopick_telas[tela_nome][var_name],
                                    font=("Arial", 8), bg="#3c3f41", fg="white", selectcolor="#4CAF50",
                                    command=gerar_callback(tela_nome))
                cb.pack(anchor='w')

    def _confirmar_selecao(self):
        autopick_selecionado = {
            '[1/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 1']),
            '[2/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 2']),
            '[3/3] MUCABRASIL': self._get_autopick_selecoes(self.autopick_telas['Tela 3'])
        }

        if all(not tela['ativo'] for tela in autopick_selecionado.values()):
            messagebox.showwarning("Seleção Inválida", "Ative pelo menos uma tela.")
            return

        self.app.menu_autopick = autopick_selecionado
        print("Configuração aplicada com sucesso.")
        self.root.quit()

    def _get_autopick_selecoes(self, tela_vars):
        return {
            'ativo': tela_vars['ativo'].get(),
            'joias': tela_vars['joias'].get(),
            'limpa_pk': tela_vars['limpa_pk'].get(),
            'pickKanturu': tela_vars['pickKanturu'].get(),
            'atlans': tela_vars['atlans'].get(),
            'sd_small': tela_vars['sd_small'].get(),
            'sd_media': tela_vars['sd_media'].get(),
            'ref_gem': tela_vars['ref_gem'].get(),
            'ref_peq': tela_vars['ref_peq'].get(),
            'upar': tela_vars['upar'].get(),
            'buf': tela_vars['buf'].get(),
            'pk': tela_vars['pk'].get(),
            'recrutar': tela_vars['recrutar'].get()
        }

    def run(self):
        self.root.mainloop()
