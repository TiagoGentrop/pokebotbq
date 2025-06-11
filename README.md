# PokéAgent BQ 🤖

Um agente inteligente construído com Google Vertex AI e o Agent Development Kit (ADK), capaz de fornecer informações detalhadas sobre o universo Pokémon e gerenciar uma base de dados de treinadores e suas equipes no Google BigQuery.

## ✨ Funcionalidades

* **Consultas à PokeAPI:**
    * Obtém tipos, status, habilidades, linha evolutiva e sprites de qualquer Pokémon.
    * Busca entradas da Pokédex para versões específicas dos jogos.
* **Gerenciamento de Treinadores no BigQuery:**
    * Adiciona e remove treinadores.
    * Adiciona, remove e evolui Pokémon nas equipes dos treinadores.
    * Lista todos os treinadores e as equipes de um treinador específico.
* **Interação Inteligente:**
    * Capaz de buscar o ID de um treinador pelo nome antes de executar uma ação.
    * Fluxos de conversa guiados para operações sensíveis, como a exclusão de um treinador.

## 🛠️ Tecnologias Utilizadas

* **Python 3.11+**
* **Google Vertex AI** (para o modelo de linguagem Gemini)
* **Google Agent Development Kit (ADK)**
* **Google BigQuery** (como banco de dados)
* **PokeAPI** (como fonte de dados externa)
* **SQLAlchemy** com o conector nativo do BigQuery

## 🚀 Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/TiagoGentrop/pokebotbq.git](https://github.com/TiagoGentrop/pokebotbq.git)
    cd pokebotbq
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv pokebot_env
    # Windows
    .\pokebot_env\Scripts\activate
    # macOS/Linux
    source pokebot_env/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Autentique com o Google Cloud:**
    ```bash
    gcloud auth application-default login
    ```

5.  **Configure o ambiente:**
    * Renomeie o arquivo `.env.example` para `.env`.
    * Preencha as variáveis de ambiente (`GOOGLE_CLOUD_PROJECT`, `BIGQUERY_DATASET`, etc.) com seus próprios valores.

6.  **Execute o script de setup do BigQuery:**
    * Copie o conteúdo do arquivo `setup_bigquery.sql` e execute-o no console do BigQuery para criar as tabelas.

7.  **Inicie o agente:**
    ```bash
    adk web
    ```
    Acesse `http://localhost:8000` no seu navegador.
