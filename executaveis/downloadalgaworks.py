import json
import os
import subprocess
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 🛠 Configuração do Selenium
options = Options()
options.add_argument("--headless")  # Executar sem abrir o navegador
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # Capturar logs de rede

# 🔄 Inicializa o WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 📌 Credenciais de login
URL_LOGIN = "https://app.algaworks.com/login"
EMAIL = "juniormassuia@gmail.com"
SENHA = "MASSUIA123"

# 📌 URLs das aulas
URL_AULAS = [
    "https://app.algaworks.com/aulas/3626/implementando-o-endpoint-do-json-web-key-set-jwks",
    "https://app.algaworks.com/aulas/3627/externalizando-o-keystore-criando-um-protocolresolver-para-base64",
    "https://app.algaworks.com/aulas/3628/conhecendo-o-docker",
    "https://app.algaworks.com/aulas/3629/instalando-o-docker",
    "https://app.algaworks.com/aulas/3630/executando-um-container",
    "https://app.algaworks.com/aulas/3631/gerenciando-melhor-os-containers",
    "https://app.algaworks.com/aulas/3632/conhecendo-a-arquitetura-do-docker",
    "https://app.algaworks.com/aulas/3633/entendendo-o-que-sao-as-imagens-e-o-docker-hub",
    "https://app.algaworks.com/aulas/3634/gerenciando-imagens",
    "https://app.algaworks.com/aulas/3635/executando-um-container-do-mysql",
    "https://app.algaworks.com/aulas/3636/construindo-a-imagem-da-aplicacao-com-dockerfile",
    "https://app.algaworks.com/aulas/3637/criando-uma-network-e-conectando-dois-containers",
    "https://app.algaworks.com/aulas/3638/construindo-a-imagem-docker-pelo-maven",
    "https://app.algaworks.com/aulas/3639/disponibilizando-a-imagem-da-aplicacao-no-docker-hub",
    "https://app.algaworks.com/aulas/3640/conhecendo-e-usando-docker-compose",
    "https://app.algaworks.com/aulas/3641/controlando-a-ordem-de-inicializacao-com-wait-for-itsh",
    "https://app.algaworks.com/aulas/3642/escalando-um-servico-com-docker-compose",
    "https://app.algaworks.com/aulas/3643/entendendo-o-poor-mans-load-balancer-dns-round-robin",
    "https://app.algaworks.com/aulas/3644/configurando-um-proxy-reverso-com-nginx",
    "https://app.algaworks.com/aulas/3645/entendendo-o-problema-da-http-session-no-authorization-server",
    "https://app.algaworks.com/aulas/3646/adicionando-um-container-do-redis-no-arquivo-do-docker-compose",
    "https://app.algaworks.com/aulas/3647/configurando-o-spring-session-data-redis",
    "https://app.algaworks.com/aulas/3648/resolvendo-problemas-com-storage-de-authorization-codes",
    "https://app.algaworks.com/aulas/3649/introducao-ao-deployment-em-producao",
    "https://app.algaworks.com/aulas/3650/mais-organizacao-das-propriedades-do-projeto-com-spring-profiles",
    "https://app.algaworks.com/aulas/3651/dependencia-de-javamailsender-nao-satisfeita-melhorando-o-uso-da-heranca",
    "https://app.algaworks.com/aulas/3652/conhecendo-a-amazon-web-services-aws",
    "https://app.algaworks.com/aulas/3653/entendendo-alguns-conceitos-fundamentais-da-nuvem-da-aws",
    "https://app.algaworks.com/aulas/3654/monitorando-e-criando-um-alerta-de-orcamento-da-aws",
    "https://app.algaworks.com/aulas/3655/criando-o-bucket-no-amazon-s3",
    "https://app.algaworks.com/aulas/3656/criando-uma-instancia-do-mysql-no-amazon-rds",
    "https://app.algaworks.com/aulas/3657/criando-schema-e-usuario-da-aplicacao",
    "https://app.algaworks.com/aulas/3658/conhecendo-e-criando-uma-conta-no-redislabs",
    "https://app.algaworks.com/aulas/3659/criando-uma-instancia-do-redis-na-nuvem",
    "https://app.algaworks.com/aulas/3660/conhecendo-o-amazon-elastic-container-service-ecs-e-aws-fargate",
    "https://app.algaworks.com/aulas/3661/publicando-um-container-no-amazon-ecs",
    "https://app.algaworks.com/aulas/3662/subindo-a-imagem-docker-para-o-amazon-elastic-container-registry-ecr",
    "https://app.algaworks.com/aulas/3663/organizando-as-variaveis-de-ambiente-do-container-da-aplicacao",
    "https://app.algaworks.com/aulas/3664/gerenciando-as-configuracoes-com-aws-systems-manager-parameter-store",
    "https://app.algaworks.com/aulas/3665/configurando-amazon-ecs-para-rodar-nossa-aplicacao",
    "https://app.algaworks.com/aulas/3666/permitindo-a-leitura-de-parametros-do-parameter-store-pelo-servico-do-amazon-ecs",
    "https://app.algaworks.com/aulas/3667/permitindo-o-acesso-ao-mysql-pelo-security-group-do-servico-do-amazon-ecs",
    "https://app.algaworks.com/aulas/3668/inserindo-dados-no-banco-de-dados-de-producao",
    "https://app.algaworks.com/aulas/3669/conhecendo-o-elastic-load-balancing-da-amazon",
    "https://app.algaworks.com/aulas/3670/configurando-e-provisionando-um-load-balancer-na-amazon",
    "https://app.algaworks.com/aulas/3671/configurando-o-balanceamento-de-carga-no-servico-do-amazon-ecs",
    "https://app.algaworks.com/aulas/3672/registrando-um-dominio-de-internet-no-registrobr",
    "https://app.algaworks.com/aulas/3673/configurando-o-dominio-para-o-application-load-balancer",
    "https://app.algaworks.com/aulas/3674/configurando-certificado-tls-https-com-aws-certificate-manager",
    "https://app.algaworks.com/aulas/3675/configurando-o-protocolo-https-nos-links-da-api-com-hateoas",
    "https://app.algaworks.com/aulas/3676/testando-a-api-em-producao",
    "https://app.algaworks.com/aulas/2324/conclusao-e-proximos-passos",
    "https://app.algaworks.com/aulas/4389/conhecendo-o-springdoc",
    "https://app.algaworks.com/aulas/4390/removendo-o-springfox-do-projeto",
    "https://app.algaworks.com/aulas/4391/adicionando-o-springdoc-no-projeto",
    "https://app.algaworks.com/aulas/4392/configurando-multiplas-documentacoes-em-um-so-projeto",
    "https://app.algaworks.com/aulas/4393/ajustando-a-documentacao-da-api-para-suporte-a-oauth2",
    "https://app.algaworks.com/aulas/4394/descrevendo-tags-na-documentacao-e-associando-com-controllers",
    "https://app.algaworks.com/aulas/4395/descrevendo-as-operacoes-de-endpoints-na-documentacao",
    "https://app.algaworks.com/aulas/4396/descrevendo-parametros-de-entrada-na-documentacao",
    "https://app.algaworks.com/aulas/4397/descrevendo-modelos-de-representacoes-e-suas-propriedades",
    "https://app.algaworks.com/aulas/4398/descrevendo-restricoes-de-validacao-de-propriedades-do-modelo",
    "https://app.algaworks.com/aulas/4399/descrevendo-codigos-de-status-de-respostas-de-forma-global",
    "https://app.algaworks.com/aulas/4400/descrevendo-codigos-de-status-de-respostas-em-endpoints-especificos",
    "https://app.algaworks.com/aulas/4401/descrevendo-codigos-de-status-de-respostas-de-forma-global-para-cada-tipo-de-metodo-http",
    "https://app.algaworks.com/aulas/4402/descrevendo-o-modelo-de-representacao-de-problema",
    "https://app.algaworks.com/aulas/4403/referenciando-modelo-de-representacao-de-problema-com-codigos-de-status-de-erro",
    "https://app.algaworks.com/aulas/4404/desafio-descrevendo-documentacao-de-endpoints-de-grupos",
    "https://app.algaworks.com/aulas/4405/corrigindo-documentacao-com-substituicao-de-pageable",
    "https://app.algaworks.com/aulas/4406/desafio-descrevendo-documentacao-de-endpoints-de-cozinhas",
    "https://app.algaworks.com/aulas/4407/desafio-descrevendo-documentacao-de-endpoints-de-formas-de-pagamento",
    "https://app.algaworks.com/aulas/4408/desafio-descrevendo-documentacao-de-endpoints-de-pedidos",
    "https://app.algaworks.com/aulas/4409/descrevendo-parametros-de-projecoes-em-endpoints-de-consultas",
    "https://app.algaworks.com/aulas/4410/descrevendo-media-type-da-resposta-nos-endpoints",
    "https://app.algaworks.com/aulas/4411/corrigindo-documentacao-no-swagger-ui-para-upload-de-arquivos",
    "https://app.algaworks.com/aulas/4412/desafio-descrevendo-documentacao-de-endpoints-de-restaurantes",
    "https://app.algaworks.com/aulas/4413/desafio-descrevendo-documentacao-de-endpoints-de-estados",
    "https://app.algaworks.com/aulas/4414/desafio-descrevendo-documentacao-de-endpoints-de-fluxo-de-pedidos",
    "https://app.algaworks.com/aulas/4415/desafio-descrevendo-documentacao-de-endpoints-de-associacao-de-restaurantes-com-formas-de-pagamento",
    "https://app.algaworks.com/aulas/4416/desafio-descrevendo-documentacao-de-endpoints-de-associacao-de-restaurantes-com-usuarios",
    "https://app.algaworks.com/aulas/4417/desafio-descrevendo-documentacao-de-endpoints-de-produtos",
    "https://app.algaworks.com/aulas/4418/desafio-descrevendo-documentacao-de-endpoints-de-fotos-de-produtos",
    "https://app.algaworks.com/aulas/4419/desafio-descrevendo-documentacao-de-endpoints-de-associacao-de-permissoes-com-grupos",
    "https://app.algaworks.com/aulas/4420/desafio-descrevendo-documentacao-de-endpoints-de-usuarios",
    "https://app.algaworks.com/aulas/4421/desafio-descrevendo-documentacao-de-endpoints-de-associacao-de-grupos-com-usuarios",
    "https://app.algaworks.com/aulas/4422/desafio-descrevendo-documentacao-de-endpoint-de-estatisticas",
    "https://app.algaworks.com/aulas/4423/desafio-descrevendo-documentacao-de-endpoint-de-permissoes",
    "https://app.algaworks.com/aulas/4424/corrigindo-documentacao-ocultando-o-root-entry-point",
    "https://app.algaworks.com/aulas/4438/o-que-e-o-spring-authorization-server",
    "https://app.algaworks.com/aulas/4439/removendo-o-authorization-server-antigo-do-projeto",
    "https://app.algaworks.com/aulas/4440/configuracao-inicial-do-authorization-server-com-access-token-opaco",
    "https://app.algaworks.com/aulas/4441/testando-com-fluxo-client-credentials-com-postman",
    "https://app.algaworks.com/aulas/4442/inspecionando-token-opaco-usando-o-endpoint-oauth2-introspect",
    "https://app.algaworks.com/aulas/4443/configurando-o-resource-server-com-token-opaco",
    "https://app.algaworks.com/aulas/4444/armazenando-autorizacoes-no-banco-de-dados",
    "https://app.algaworks.com/aulas/4445/revogando-o-access-token-com-oauth2-revoke",
    "https://app.algaworks.com/aulas/4446/configurando-a-geracao-de-access-token-jwt-no-authorization-server",
    "https://app.algaworks.com/aulas/4447/configurando-o-resource-server-com-token-jwt",
    "https://app.algaworks.com/aulas/4448/implementando-um-cliente-com-o-fluxo-authorization-code",
    "https://app.algaworks.com/aulas/4449/testando-o-fluxo-authorization-code-pkce-s256-e-corrigindo-problemas",
    "https://app.algaworks.com/aulas/4450/implementando-um-cliente-com-o-fluxo-refresh-token",
    "https://app.algaworks.com/aulas/4451/customizando-o-token-jwt-com-dados-do-usuario",
    "https://app.algaworks.com/aulas/4452/lendo-informacoes-customizadas-do-jwt-no-resource-server",
    "https://app.algaworks.com/aulas/4453/implementado-repository-de-clients-do-oauth2-via-jdbc",
    "https://app.algaworks.com/aulas/4454/customizando-a-pagina-de-login-do-authorization-server",
    "https://app.algaworks.com/aulas/4455/customizando-a-pagina-de-consentimento-do-oauth2",
    "https://app.algaworks.com/aulas/4456/armazenando-autorizacoes-de-consentimento-no-banco-de-dados",
    "https://app.algaworks.com/aulas/4457/criando-uma-pagina-de-listagem-dos-clientes-com-consentimentos-permitidos",
    "https://app.algaworks.com/aulas/4458/revogando-consentimentos-e-autorizacoes-dos-clientes",
    "https://app.algaworks.com/aulas/4567/as-principais-mudancas-do-spring-boot-3",
    "https://app.algaworks.com/aulas/4568/removendo-componentes-incompativeis",
    "https://app.algaworks.com/aulas/4569/atualizacao-a-dependencias-e-componentes-do-spring",
    "https://app.algaworks.com/aulas/4570/alteracoes-do-jakarta-ee-e-jakarta-persistence-30",
    "https://app.algaworks.com/aulas/4571/atualizando-o-spring-doc",
    "https://app.algaworks.com/aulas/4572/atualizando-o-spring-authorization-server",
]


def fazer_login():
    """Realiza login no site da AlgaWorks"""
    print("🔑 Fazendo login...")
    driver.get(URL_LOGIN)
    # Usando WebDriverWait para aguardar o carregamento do formulário de login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Seu e-mail']")))

    # Preenche email e senha
    driver.find_element(By.XPATH, "//input[@placeholder='Seu e-mail']").send_keys(EMAIL)
    driver.find_element(By.XPATH, "//input[@placeholder='Sua senha']").send_keys(SENHA, Keys.RETURN)

    # Espera um pouco para garantir que o login foi bem-sucedido
    driver.implicitly_wait(5)  # Espera carregar a próxima página


def baixar_aula(url):
    """Acessa uma aula e tenta baixar o vídeo"""
    print(f"\n📌 Acessando aula: {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "l-page-headline__title")))

    # 🏷️ Captura o título da aula
    try:
        titulo_element = driver.find_element(By.CLASS_NAME, "l-page-headline__title")
        titulo_aula = titulo_element.text.strip()
    except Exception as e:
        print(f"⚠️ Erro ao capturar título: {e}")
        titulo_aula = "Aula_Desconhecida"

    print(f"🎬 Aula encontrada: {titulo_aula}")

    # 🗂️ Cria pasta para salvar o vídeo
    pasta_aula = f"Aulas/{titulo_aula}"
    os.makedirs(pasta_aula, exist_ok=True)

    # 🔍 1️⃣ Tenta encontrar a URL ".m3u8" no Network Logs
    logs = driver.get_log("performance")
    video_url = None

    for log in logs:
        log_json = json.loads(log["message"])
        message = log_json.get("message", {})
        params = message.get("params", {})
        request = params.get("request", {})
        request_url = request.get("url", "")

        if ".m3u8" in request_url or ".mp4" in request_url:
            print(f"🎯 Link de vídeo encontrado: {request_url}")
            video_url = request_url
            break

    # 📥 2️⃣ Se encontrou ".m3u8", faz o download com ffmpeg
    if video_url:
        baixar_m3u8(video_url, pasta_aula, titulo_aula)
        return

    # 🔍 3️⃣ Caso não tenha .m3u8 nos logs, tenta capturar do iframe
    try:
        # Usando WebDriverWait para garantir que o iframe esteja carregado
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[starts-with(@id, 'panda-')]")))
        driver.switch_to.frame(iframe)
        time.sleep(2)  # Minimiza o tempo de espera dentro do iframe

        # Procura por <video> dentro do iframe
        try:
            video_element = driver.find_element(By.TAG_NAME, "video")
            source_element = video_element.find_element(By.TAG_NAME, "source")
            video_url = source_element.get_attribute("src")

            if video_url and ".m3u8" in video_url:
                print(f"🎞️ Link m3u8 encontrado no iframe: {video_url}")
                driver.switch_to.default_content()
                baixar_m3u8(video_url, pasta_aula, titulo_aula)
                return
        except Exception as e:
            print(f"⚠️ Nenhuma URL de vídeo encontrada no iframe: {e}")

        driver.switch_to.default_content()
    except Exception as e:
        print(f"🚨 Erro ao acessar iframe: {e}")

    print("❌ Nenhum vídeo disponível para download!")


def baixar_m3u8(url, pasta, titulo):
    """Baixa o vídeo HLS (.m3u8) convertendo para MP4"""
    try:
        video_path = os.path.join(pasta, f"{titulo}.mp4")
        print(f"📥 Baixando vídeo: {video_path}")

        # Usa ffmpeg para baixar e converter o vídeo
        cmd = ["ffmpeg", "-i", url, "-c", "copy", video_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"✅ Download concluído: {video_path}")
    except Exception as e:
        print(f"❌ Erro ao baixar vídeo: {e}")


def main():
    """Executa todo o processo de login e download usando múltiplas threads"""
    try:
        fazer_login()
        for url in URL_AULAS:
            baixar_aula(url)
    finally:
        driver.quit()
        print("\n✅ Processo concluído!")


if __name__ == "__main__":
    main()
