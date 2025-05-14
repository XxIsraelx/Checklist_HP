import flet as ft
import gspread
import json
from google.oauth2.service_account import Credentials
import time
import locale
from flet import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os


load_dotenv()

def send_email(motorista, placa, km_atual, km_proxima):
    try:
        # Configurações do e-mail
        sender_email = os.getenv(sender_email)  # Substitua pelo seu e-mail
        receiver_email = os.getenv(receiver_email)  # E-mail de destino (pode ser o do motorista ou outro)
        password = os.getenv(password)  # Senha do seu e-mail

        # Configura o servidor SMTP (usando o Gmail como exemplo)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Cria a mensagem de e-mail
        subject = "Relatório de Checklist do Caminhão"
        body = f"""
        Relatório de Checklist do Caminhão:

        Motorista: {motorista}
        Placa: {placa}
        KM Atual: {km_atual}
        KM da Próxima Troca: {km_proxima}

        Detalhes adicionais podem ser encontrados no formulário enviado.
        """

        # Criação do objeto MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        print("Tentando conectar ao servidor SMTP...")

        # Conexão ao servidor SMTP e envio do e-mail
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Inicia a criptografia TLS
        print("Conexão estabelecida. Tentando fazer login...")

        server.login(sender_email, password)  # Login no servidor SMTP
        print("Login bem-sucedido! Enviando o e-mail...")

        server.sendmail(sender_email, receiver_email, msg.as_string())  # Envia o e-mail
        server.quit()  # Fecha a conexão com o servidor SMTP

        print("E-mail enviado com sucesso!")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Erro de autenticação: {e}")
    except smtplib.SMTPConnectError as e:
        print(f"Erro ao conectar com o servidor SMTP: {e}")
    except smtplib.SMTPException as e:
        print(f"Erro no envio do e-mail: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ID da planilha
SHEET_ID = "1i-rMVsXIvx8Dr6q6X1hsXTRWxFpYHUeWwB98p9oFdYI"

# Carrega o conteúdo da chave do JSON da variável de ambiente
creds_json = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)

# Autenticação usando o dicionário da chave
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

# Autoriza e cria o cliente para acessar a planilha
client = gspread.authorize(creds)

# Acesso à planilha
sheet = client.open_by_key(SHEET_ID).sheet1
# Antes de enviar dados, adiciona os cabeçalhos (apenas uma vez)
def add_headers():
    headers = [
        "Data/Hora", "Motorista", "Placa", "KM Atual", "KM Próxima Troca",
        "Estado do Pneu", "Comentário do Pneu", "Nível do Óleo", "Comentário do Óleo",
        "Reservatório de Água", "Comentário do Reservatório",
        "Teste de Freios", "Comentário do Teste de Freios",
        "Lanternas e Iluminação", "Comentário das Lanternas",
        "Bateria", "Comentário da Bateria",
        "Lataria/Visual", "Comentário da Lataria",
        "Vazamentos", "Comentário dos Vazamentos",
        "Tacógrafo", "Comentário do Tacógrafo",
        "Thermo King", "Comentário do Thermo King",
        "Condição do Baú", "Comentário da Condição do Baú",
        "Ferramentas", "Comentário das Ferramentas",
        "Observações"
    ]
    
    # Verifique se os cabeçalhos já existem para não adicionar novamente
    if sheet.row_count == 0:
        sheet.append_row(headers)

add_headers()

# Lista de motoristas e placas de caminhões (pode ser alterado conforme necessário)
motoristas = [
    "Anderson Alves", "André", "Danisete", "Erick", "Fernando", 
    "Gilmar", "Igor", "Israel", "Joao Victor", "Jilson", "Marco Antonio", 
    "Manoel", "Mario", "Nilton", "Reginaldo", "Washigton", "Vitor Hugo", 
    "Josue", "Juliano", "Oseias", "Valdinei"
]

placas = [
    "2E21", "8H52", "3833", "0048", "2645", "1270",
    "1079", "6D17", "7J38", "7246", "9004", "1528",
    "9C47", "0D86", "9543", "8847", "6179", "8G63",
    "6062", "2H13", "9701", "3125", "9H71", "3J16" 
]

def main(page: ft.Page):
    page.title = "Checklist"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = "adaptive"

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'portuguese')

    items = [
        {"name": "Estado do Pneu", "checked": False, "comment": ""},
        {"name": "Nível do Óleo", "checked": False, "comment": ""},
        {"name": "Reservatório de Água", "checked": False, "comment": ""},
        {"name": "Teste de Freios", "checked": False, "comment": ""},
        {"name": "Lanternas e Iluminação", "checked": False, "comment": ""},
        {"name": "Bateria", "checked": False, "comment": ""},
        {"name": "Lataria/Visual", "checked": False, "comment": ""},
        {"name": "Vazamentos", "checked": False, "comment": ""},
        {"name": "Tacógrafo", "checked": False, "comment": ""},
        {"name": "Thermo King", "checked": False, "comment": ""},
        {"name": "Condição do Baú", "checked": False, "comment": ""},
        {"name": "Ferramentas", "checked": False, "comment": ""},
    ]

    def create_checklist():
        checklist_controls = []
        for item in items:
            checkbox = ft.Checkbox(label=item["name"], value=item["checked"])
            checkbox.on_change = lambda e, idx=item["name"]: toggle_item(idx, e.control.value)
            
            comment_input = ft.TextField(
                label="O que aconteceu?", 
                visible=item["checked"], 
                width=250,
                border_color="#696969",
                border_radius=10
            )
            item["comment_input"] = comment_input
            
            checklist_controls.append(
                ft.Column(
                    controls=[checkbox, comment_input],
                    spacing=5
                )
            )
        return checklist_controls

    def toggle_item(item_name, checked):
        for item in items:
            if item["name"] == item_name:
                item["checked"] = checked
                item["comment_input"].visible = checked
                item["comment_input"].value = "" 
        page.update()  # Atualiza a página para refletir as mudanças

    # Campo de observação livre
    observacao_field = ft.TextField(
        label="Observações gerais (opcional)",
        multiline=True,
        min_lines=2,
        max_lines=4,
        width=500,
        border_color="#696969",
        border_radius=10
    )


    # Campos KM atual e KM da próxima troca de óleo
    km_current_field = ft.TextField(
        label="KM Atual", 
        width=200,
        border_color="#696969",  # Cor da borda
        border_radius=10,
        on_change=lambda e: validate_km()  # Verifica ao alterar o valor
    )
    
    km_next_field = ft.TextField(
        label="KM da Troca", 
        width=250,
        border_color="#696969",  # Cor da borda
        border_radius=10,
        on_change=lambda e: validate_km()  # Verifica ao alterar o valor
    )

    # Campos KM row (para adicionar na tela)
    km_row = ft.Row(
        controls=[ 
            ft.Container(
                content=km_current_field,
                padding=10,  # Padding aqui
                alignment=ft.alignment.center,  
            ),
            ft.Container(
                content=km_next_field,
                padding=10,  # Padding aqui
                alignment=ft.alignment.center,  
            )
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=15
    )

    submit_button = ft.ElevatedButton(
        text="Enviar", 
        on_click=lambda e: show_confirm_pop_up(),  # Abre o pop-up de confirmação ao clicar
        disabled=True,  # Desabilitado inicialmente
        tooltip="Os campos KM atual e KM da próxima troca de óleo são obrigatórios."
    )

    cancel_button = ft.ElevatedButton(
        text="Cancelar", 
        on_click=lambda e: show_cancel_confirmation_dialog(),
    )

    # Função para exibir o pop-up de confirmação de cancelamento
    def show_cancel_confirmation_dialog():
        dialog = AlertDialog(
            title=Text("Deseja cancelar o envio do formulário?"),
            content=Text("Você tem certeza que deseja cancelar?"),
            actions=[
                ft.TextButton(text="Sim", on_click=lambda e: cancel_form(dialog)),  # Cancela e fecha o app
                ft.TextButton(text="Não", on_click=lambda e: close_dialog(dialog)),  # Fecha o pop sem cancelar
            ]
        )
        page.add(dialog)
        dialog.open = True
        page.update()

    def cancel_form(dialog):
        # Fecha a aplicação se o usuário clicar "Sim"
        dialog.open = False
        page.update()
        page.window.destroy()

    def close_dialog(dialog):
        # Apenas fecha o pop-up
        dialog.open = False
        page.update()

    # Função para exibir o pop-up de confirmação de envio
    def show_confirm_pop_up():
        global motorista_dropdown, placa_dropdown

        motorista_dropdown = ft.TextField(
            label="Digite o nome do Motorista",
            width=300,
        )



        placa_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(p) for p in placas],
            width=250,
            value=None,
            label="Placa do caminhão"
        )

        dialog = AlertDialog(
            title=ft.Text("Confirmar envio", size=18, weight=FontWeight.BOLD),
            content=ft.Column(
                controls=[
                    ft.Text("Escolha o motorista:", size=15),
                    motorista_dropdown,
                    ft.Text("Escolha a placa do caminhão:", size=15),
                    placa_dropdown,
                ],
                spacing=10
            ),
            actions=[
                ft.TextButton(text="Enviar", on_click=lambda e: send_form(dialog)),
                ft.TextButton(text="Cancelar", on_click=lambda e: close_dialog(dialog)),
            ],
        )

        page.add(dialog)
        dialog.open = True
        page.update()


    def send_form(dialog):
        # Obtenha os dados do formulário
        motorista = motorista_dropdown.value  # Motorista selecionado (valor real)
        placa = placa_dropdown.value  # Placa selecionada (valor real)
        km_atual = km_current_field.value
        km_proxima = km_next_field.value
    
        # Prepara a linha com os dados a serem adicionados
        data_hora = time.strftime("%d/%m/%Y %H:%M")  # Data e hora atual
    
        # Lista para armazenar os feedbacks dos itens
        item_data = []
    
        # Verifica os itens do checklist e define os valores conforme solicitado
        for item in items:
            if item["checked"]:  # Se o item foi marcado
                comment = item["comment_input"].value.strip()
                if comment == "":  # Se o usuário não escreveu nada
                    item_data.append("NÃO OK")
                else:
                    item_data.append(comment)  # Envia o que o usuário escreveu
            else:
                item_data.append("OK")  # Se o item não foi marcado, envia "OK"
    
        # A linha com os dados que será enviada para a planilha
        row = [
            data_hora, motorista, placa, km_atual, km_proxima,
            *item_data,
            observacao_field.value  # Aqui você adiciona a observação do usuário
        ]
    
        # Adiciona a nova linha à planilha
        sheet.append_row(row)

        send_email(motorista, placa, km_atual, km_proxima)

        # Feedback para o usuário
        page.add(ft.Text("Formulário Enviado!"))
        close_dialog(dialog)  # Fecha o pop-up após o envio



    def close_dialog(dialog):
        # Apenas fecha o pop-up
        dialog.open = False
        page.update()

    # Ajustes responsivos para dispositivos móveis
    def responsive_layout():
        # Verifique a largura da tela
        if page.width < 600:  # Largura típica de dispositivos móveis
            # Diminuir a largura dos campos de entrada em 10% para mobile
            new_width = km_current_field.width * 0.9
            km_next_field.width = new_width
            km_current_field.width = new_width

            # Centralizar os botões de enviar e cancelar para mobile
            submit_button.width = 200  # Ajuste conforme necessário
            cancel_button.width = 200  # Ajuste conforme necessário
            submit_button.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            cancel_button.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        else:
            # Para telas maiores, reverter para o tamanho original
            km_current_field.width = 200
            km_next_field.width = 250
            submit_button.width = 150
            cancel_button.width = 150
            submit_button.horizontal_alignment = ft.CrossAxisAlignment.START
            cancel_button.horizontal_alignment = ft.CrossAxisAlignment.START

        page.update()

    # Conecte o evento ao redimensionamento da tela
    page.on_resized = lambda e: responsive_layout()  # Chama a função responsiva ao redimensionar

    # Inicialize o layout responsivo
    responsive_layout()

    # Adicionando data e hora no canto superior direito
    def update_time(e=None):
        # Obtém a data e hora atual no formato desejado em português
        current_time = time.strftime("%A, %d de %B de %Y %H:%M")  # Formato: Dia da semana, dia do mês, mês, ano, hora:minuto
        date_time_text.value = current_time
        page.update()

    # Exibir a hora atual
    date_time_text = ft.Text("", size=12, weight=FontWeight.BOLD)
    update_time()  # Chama a função para exibir a hora inicial

    # Atualiza a hora a cada minuto (60 segundos)
    page.on_timer = update_time  # Atualiza a hora a cada intervalo

    # Validação para os campos KM
    def validate_km():
        km_atual_value = km_current_field.value
        km_proxima_value = km_next_field.value

        # Verifica se algum dos campos de KM está vazio
        if km_atual_value == "" or km_proxima_value == "":
            submit_button.disabled = True  # Desabilita o botão de envio
            submit_button.tooltip = "Os campos KM atual e KM da próxima troca de óleo são obrigatórios."
            page.update()
            return  # Não prossegue com a validação se algum campo estiver vazio

        try:
            # Tenta converter os valores para float (considerando números decimais também)
            km_atual_value = float(km_atual_value)
            km_proxima_value = float(km_proxima_value)

            # Verifica se o KM da próxima troca é maior que o KM atual
            if km_proxima_value <= km_atual_value:
                return  # Não prossegue com o envio se houver erro

            # Se passou nas validações, habilita o botão de envio
            submit_button.disabled = False
            submit_button.tooltip = ""  # Limpa o tooltip de erro
            page.update()
        
        except ValueError:
            # Se algum valor não for convertido corretamente (por exemplo, letras em vez de números)
            show_alert("Valor informado inválido", "Por favor, insira números válidos para os campos KM.")
            submit_button.disabled = True  # Desabilita o botão de envio em caso de erro
            submit_button.tooltip = "Os campos KM devem ser numéricos."
            page.update()

    def show_alert(title, message):
        # Função para exibir o pop-up de erro
        dialog = AlertDialog(
            title=Text(title),
            content=Text(message),
            actions=[
                ft.TextButton(text="OK", on_click=lambda e: close_alert(dialog))  # Usando a função close_alert
            ]
        )
        page.add(dialog)
        dialog.open = True
        page.update()

    def close_alert(dialog):
        # Função para fechar o alerta
        dialog.open = False
        page.update()  # Atualiza a página para refletir a mudança

    # Layout da página
    page.add(
        ft.Column(
            [
                ft.Row(
                    controls=[date_time_text],
                    alignment=ft.alignment.top_right,  # Coloca no canto superior direito
                ),
                ft.Text("Selecione alguma irregularidade", size=15, weight=FontWeight.BOLD),
                *create_checklist(),
                ft.Text("Observações gerais", size=15, weight=FontWeight.BOLD),
                observacao_field,
                ft.Text("Acompanhamento Óleo", size=15, weight=FontWeight.BOLD),
                km_row,  # Linha com os campos KM
                ft.Row(controls=[submit_button, cancel_button], spacing=10, alignment=ft.MainAxisAlignment.CENTER),  # Botões centralizados
            ],
            alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER,
        )
    )

# Alteração: Permitir conexões externas com "host='0.0.0.0'"
ft.app(target=main, view=WEB_BROWSER, port=8550)
