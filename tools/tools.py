import requests 
from datetime import datetime
import sqlalchemy
import traceback
import os
import uuid 
import locale
import os
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

from ..db.connection import get_bq_client, ADMIN_PASSWORD

# Carrega as variáveis de ambiente
PROJECT_ID = os.getenv("APP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
DATASET_ID = os.getenv("BIGQUERY_DATASET")
TABLE_TREINADORES = f"`{PROJECT_ID}.{DATASET_ID}.Treinadores`"
TABLE_EQUIPE = f"`{PROJECT_ID}.{DATASET_ID}.EquipePokemons`"

def get_time():
    """Obtém a hora atual do sistema."""
    return datetime.now().strftime("%H:%M:%S")

def get_weekday():
    """Obtém o dia da semana atual em português."""
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '') # Fallback para o locale padrão
    return datetime.now().strftime("%A").capitalize()

def get_pokemon_types(poke_name: str):
    """
    Recupera os tipos de um Pokémon específico da PokeAPI.

    Args:
        poke_name (str): O nome do Pokémon a ser pesquisado (ex: "Pikachu").

    Returns:
        dict: Um dicionário com o nome e a lista de tipos do Pokémon, ou um erro.
    """
    name = poke_name.strip().lower()
    if not name:
        return {"error": "Nome do Pokémon não pode ser vazio."}
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if response.status_code == 404:
        return {"error": f"Pokémon '{poke_name}' não foi encontrado."}
    data = response.json()
    types_list = [t['type']['name'] for t in data.get('types', [])]
    return {"pokemon_name": data.get("name", name), "types": types_list}

def get_pokemon_stats(poke_name: str):
    """
    Recupera as estatísticas base (HP, ataque, etc.) de um Pokémon.

    Args:
        poke_name (str): O nome do Pokémon a ser pesquisado (ex: "Snorlax").

    Returns:
        dict: Um dicionário com as estatísticas do Pokémon, ou um erro.
    """
    name = poke_name.strip().lower()
    if not name: return {"error": "Nome do Pokémon não pode ser vazio."}
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if response.status_code != 200: return {"error": f"Erro ao buscar dados do Pokémon '{poke_name}'."}
    data = response.json()
    stats_dict = {s['stat']['name']: s['base_stat'] for s in data.get('stats', [])}
    return {"pokemon_name": data.get("name", name), "stats": stats_dict}

def get_pokemon_pokedex_entry(poke_name: str, game_version: str):
    """
    Busca a descrição da Pokédex de um Pokémon para uma versão de jogo específica.

    Args:
        poke_name (str): O nome do Pokémon (ex: "Gengar").
        game_version (str): A versão do jogo para a entrada da Pokédex (ex: "red", "sword").

    Returns:
        dict: Um dicionário com a entrada da Pokédex, ou um erro.
    """
    name = poke_name.strip().lower()
    game = game_version.strip().lower()
    if not name: return {"error": "Nome do Pokémon não pode ser vazio."}
    pokemon_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if pokemon_response.status_code != 200: return {"error": f"Pokémon '{poke_name}' não encontrado."}
    species_url = pokemon_response.json().get('species', {}).get('url')
    if not species_url: return {"error": f"URL da espécie não encontrada para '{poke_name}'."}
    species_response = requests.get(species_url)
    if species_response.status_code != 200: return {"error": f"Não foi possível obter dados da espécie."}
    flavor_texts = species_response.json().get('flavor_text_entries', [])
    for entry in flavor_texts:
        if entry['language']['name'] == 'en' and entry['version']['name'] == game:
            return {"pokemon_name": name, "game_version_queried": game, "pokedex_entry": entry['flavor_text'].replace('\n', ' ')}
    return {"error": f"Nenhuma entrada da Pokédex encontrada para '{poke_name}' no jogo '{game}'."}

def get_pokemon_sprite_url(poke_name: str):
    """
    Retorna a URL da imagem (sprite) padrão de um Pokémon.

    Args:
        poke_name (str): O nome do Pokémon (ex: "Magikarp").

    Returns:
        dict: Um dicionário com a URL do sprite, ou um erro.
    """
    name = poke_name.strip().lower()
    if not name: return {"error": "Nome do Pokémon não pode ser vazio."}
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if response.status_code != 200: return {"error": f"Pokémon '{poke_name}' não encontrado."}
    sprite_url = response.json().get('sprites', {}).get('front_default')
    if not sprite_url: return {"error": f"Sprite não encontrado para '{poke_name}'."}
    return {"pokemon_name": name, "sprite_url": sprite_url}

def get_pokemon_abilities(poke_name: str):
    """
    Recupera a lista de habilidades de um Pokémon.

    Args:
        poke_name (str): O nome do Pokémon (ex: "Alakazam").

    Returns:
        dict: Um dicionário com a lista de habilidades, ou um erro.
    """
    name = poke_name.strip().lower()
    if not name: return {"error": "Nome do Pokémon não pode ser vazio."}
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if response.status_code != 200: return {"error": f"Pokémon '{poke_name}' não encontrado."}
    data = response.json()
    abilities_list = [a['ability']['name'] for a in data.get('abilities', [])]
    return {"pokemon_name": data.get("name", name), "abilities": abilities_list}
    
def get_pokemon_evolution(poke_name: str):
    """
    Retorna a cadeia de evolução completa de um Pokémon.

    Args:
        poke_name (str): O nome do Pokémon para pesquisar sua linha evolutiva (ex: "Eevee").

    Returns:
        dict: Um dicionário contendo a árvore de evolução, ou um erro.
    """
    name = poke_name.strip().lower()
    if not name: return {"error": "Nome do Pokémon não pode ser vazio."}
    pokemon_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}/")
    if pokemon_response.status_code != 200: return {"error": f"Pokémon '{poke_name}' não encontrado para buscar evolução."}
    species_url = pokemon_response.json().get('species', {}).get('url')
    if not species_url: return {"error": f"URL da espécie não encontrada para '{poke_name}'."}
    species_response = requests.get(species_url)
    if species_response.status_code != 200: return {"error": f"Não foi possível obter dados da espécie."}
    evolution_chain_url = species_response.json().get('evolution_chain', {}).get('url')
    if not evolution_chain_url: return {"error": f"URL da cadeia de evolução não encontrada."}
    evolution_response = requests.get(evolution_chain_url)
    if evolution_response.status_code != 200: return {"error": f"Não foi possível obter dados da cadeia de evolução."}
    root_stage = evolution_response.json().get('chain')
    if not root_stage: return {"error": "Dados da cadeia de evolução incompletos."}
    return {"queried_pokemon": name, "evolution_tree_from_base": build_evolution_tree(root_stage)}

def build_evolution_tree(stage_data):
    """Função auxiliar para construir recursivamente uma árvore de evolução."""
    if not stage_data: return None
    node = {"name": stage_data.get('species', {}).get('name'), "evolves_to": []}
    for next_stage in stage_data.get('evolves_to', []):
        child_node = build_evolution_tree(next_stage)
        if child_node: node["evolves_to"].append(child_node)
    return node

def validar_proxima_evolucao(arvore_evolucao: dict, pokemon_atual: str, evolucao_desejada: str) -> bool:
    """Navega na árvore de evolução para verificar se a evolução é um passo válido."""
    fila = [arvore_evolucao] 
    while fila:
        estagio_atual = fila.pop(0)
        if estagio_atual.get("name") == pokemon_atual:
            for proxima_evolucao in estagio_atual.get("evolves_to", []):
                if proxima_evolucao.get("name") == evolucao_desejada:
                    return True
            return False
        if "evolves_to" in estagio_atual:
            fila.extend(estagio_atual["evolves_to"])
    return False

def verifica_senha(codigo_fornecido: str) -> bool:
    """Verifica se o código de confirmação fornecido está correto."""
    return codigo_fornecido == ADMIN_PASSWORD

def adicionar_treinador(nome_exibicao_param: str, nomes_pokemons_equipe: list[str]) -> str:
    """
    Adiciona um novo treinador e sua equipe inicial (opcional) ao banco de dados.

    Args:
        nome_exibicao_param (str): O nome de exibição para o novo treinador.
        nomes_pokemons_equipe (list[str]): Uma lista com os nomes dos Pokémon para a equipe inicial (máximo 6).

    Returns:
        str: Uma mensagem de sucesso com o ID do novo treinador ou uma mensagem de erro.
    """
    if not nome_exibicao_param or not nome_exibicao_param.strip():
        return "Erro: O nome do treinador não pode ser vazio."

    equipe_para_inserir = []
    pokemons_invalidos = []
    if nomes_pokemons_equipe:
        if len(nomes_pokemons_equipe) > 6:
            return "Erro: Uma equipe não pode ter mais de 6 Pokémon."
        for nome_pokemon in nomes_pokemons_equipe:
            dados_pokemon = get_pokemon_types(nome_pokemon)
            if "error" not in dados_pokemon:
                equipe_para_inserir.append(dados_pokemon)
            else:
                pokemons_invalidos.append(nome_pokemon)
    
    novo_id_treinador = str(uuid.uuid4())
    client = get_bq_client()

    try:
        # 1. Inserir o treinador
        trainer_config = QueryJobConfig(query_parameters=[
            ScalarQueryParameter("id", "STRING", novo_id_treinador),
            ScalarQueryParameter("nome", "STRING", nome_exibicao_param),
        ])
        client.query(
            f"INSERT INTO {TABLE_TREINADORES} (id_treinador, nome_treinador, data_criacao) VALUES(@id, @nome, CURRENT_TIMESTAMP())",
            job_config=trainer_config
        ).result()

        # 2. Inserir os Pokémon da equipe, um por um
        for p_data in equipe_para_inserir:
            tipos_val = p_data.get("types", [])
            pokemon_config = QueryJobConfig(query_parameters=[
                ScalarQueryParameter("id_treinador", "STRING", novo_id_treinador),
                ScalarQueryParameter("nome_p", "STRING", p_data["pokemon_name"]),
                ScalarQueryParameter("t1", "STRING", tipos_val[0] if tipos_val else None),
                ScalarQueryParameter("t2", "STRING", tipos_val[1] if len(tipos_val) > 1 else None),
            ])
            client.query(
                f"""
                INSERT INTO {TABLE_EQUIPE} (id_pokemon, id_treinador_fk, nome_pokemon, tipo_primario, tipo_secundario, data_adicao) 
                VALUES (GENERATE_UUID(), @id_treinador, @nome_p, @t1, @t2, CURRENT_TIMESTAMP())
                """,
                job_config=pokemon_config
            ).result()

        msg = f"Sucesso: Treinador '{nome_exibicao_param}' adicionado com ID {novo_id_treinador}."
        if pokemons_invalidos:
            msg += f" Pokémon inválidos ignorados: {', '.join(pokemons_invalidos)}."
        return msg

    except Exception as e:
        return f"Erro na transação ao adicionar treinador: {e}"


def procurar_treinador_por_nome(nome_treinador: str) -> dict:
    """
    Procura por treinadores com um nome específico no banco de dados.

    A busca não diferencia maiúsculas de minúsculas. Essencial para encontrar o ID de um treinador antes de usar outras ferramentas.

    Args:
        nome_treinador (str): O nome do treinador a ser procurado.

    Returns:
        dict: Um dicionário com o status da busca ('encontrado_unico', 'multiplos_encontrados', 'nao_encontrado') e os dados do(s) treinador(es).
    """
    if not nome_treinador or not nome_treinador.strip():
        return {"error": "O nome do treinador para busca não pode ser vazio."}
    
    client = get_bq_client()
    try:
        # Usamos LOWER() para fazer a busca case-insensitive
        job_config = QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("nome", "STRING", nome_treinador.lower())
            ]
        )
        query_job = client.query(
            f"SELECT id_treinador, nome_treinador FROM {TABLE_TREINADORES} WHERE LOWER(nome_treinador) = @nome",
            job_config=job_config
        )
        resultados = list(query_job.result())
        
        if not resultados:
            return {"status": "nao_encontrado", "message": f"Nenhum treinador com o nome '{nome_treinador}' foi encontrado."}
        
        # Formata a lista de treinadores encontrados
        treinadores_encontrados = [{"id": row.id_treinador, "nome": row.nome_treinador} for row in resultados]
        
        if len(treinadores_encontrados) == 1:
            return {"status": "encontrado_unico", "treinador": treinadores_encontrados[0]}
        else:
            return {"status": "multiplos_encontrados", "treinadores": treinadores_encontrados}
            
    except Exception as e:
        return {"error": f"Erro ao procurar treinador: {e}"}
    

def adicionar_pokemons(id_treinador_alvo: str, nomes_novos_pokemons: list[str]) -> str:
    """
    Adiciona um ou mais Pokémon à equipe de um treinador existente.

    A função verifica se o treinador existe e se a equipe não excederá o limite de 6 Pokémon.

    Args:
        id_treinador_alvo (str): O ID do treinador que receberá os novos Pokémon.
        nomes_novos_pokemons (list[str]): Uma lista com os nomes dos Pokémon a serem adicionados.

    Returns:
        str: Uma mensagem de sucesso ou erro.
    """
    if not id_treinador_alvo or not isinstance(id_treinador_alvo, str):
        return "Erro: O ID do treinador é inválido."
    if not nomes_novos_pokemons:
        return "Informação: Nenhum Pokémon foi fornecido para adicionar."

    equipe_para_inserir = [p for p in (get_pokemon_types(nome) for nome in nomes_novos_pokemons) if "error" not in p]
    pokemons_invalidos = [nome for nome in nomes_novos_pokemons if get_pokemon_types(nome).get("error")]

    if not equipe_para_inserir:
        return f"Erro: Nenhum dos Pokémon fornecidos é válido. Inválidos: {', '.join(pokemons_invalidos)}."

    client = get_bq_client()
    try:
        job_config = QueryJobConfig(query_parameters=[ScalarQueryParameter("id", "STRING", id_treinador_alvo)])
        
        res_treinador_job = client.query(f"SELECT nome_treinador FROM {TABLE_TREINADORES} WHERE id_treinador = @id", job_config=job_config)
        res_treinador = list(res_treinador_job.result())
        if not res_treinador:
            return f"Erro: Treinador com ID '{id_treinador_alvo}' não encontrado."
        nome_treinador_atual = res_treinador[0].nome_treinador

        count_job = client.query(f"SELECT COUNT(*) as total FROM {TABLE_EQUIPE} WHERE id_treinador_fk = @id", job_config=job_config)
        count_atual = list(count_job.result())[0].total
        if count_atual + len(equipe_para_inserir) > 6:
            return f"Erro: Adicionar {len(equipe_para_inserir)} Pokémon à equipe de '{nome_treinador_atual}' (que já tem {count_atual}) excederia o limite de 6."

        for p_data in equipe_para_inserir:
            tipos_val = p_data.get("types", [])
            insert_config = QueryJobConfig(query_parameters=[
                ScalarQueryParameter("id_treinador", "STRING", id_treinador_alvo),
                ScalarQueryParameter("nome_p", "STRING", p_data["pokemon_name"]),
                ScalarQueryParameter("t1", "STRING", tipos_val[0] if tipos_val else None),
                ScalarQueryParameter("t2", "STRING", tipos_val[1] if len(tipos_val) > 1 else None),
            ])
            client.query(f"""
                INSERT INTO {TABLE_EQUIPE} (id_pokemon, id_treinador_fk, nome_pokemon, tipo_primario, tipo_secundario, data_adicao) 
                VALUES (GENERATE_UUID(), @id_treinador, @nome_p, @t1, @t2, CURRENT_TIMESTAMP())
            """, job_config=insert_config).result()

        msg = f"Sucesso: {len(equipe_para_inserir)} Pokémon adicionados à equipe de '{nome_treinador_atual}'."
        if pokemons_invalidos:
            msg += f" Pokémon inválidos ignorados: {', '.join(pokemons_invalidos)}."
        return msg
    except Exception as e:
        return f"Erro na transação ao adicionar pokémon: {e}"


def listar_treinadores() -> str:
    """Lista todos os treinadores registrados no BigQuery."""
    client = get_bq_client()
    try:
        query_job = client.query(f"SELECT id_treinador, nome_treinador FROM {TABLE_TREINADORES} ORDER BY nome_treinador")
        resultados = list(query_job.result())
        
        if not resultados:
            return "Nenhum treinador encontrado no sistema."
        
        lista_formatada = ["Lista de Treinadores:"]
        for row in resultados:
            lista_formatada.append(f"- ID: {row.id_treinador}, Nome: {row.nome_treinador}")
        return "\n".join(lista_formatada)
    except Exception as e:
        return f"Erro ao listar treinadores: {e}"


def listar_pokemons(id_treinador_alvo: str) -> str:
    """
    Lista todos os Pokémon na equipe de um treinador específico, usando seu ID.

    Args:
        id_treinador_alvo (str): O ID do treinador cuja equipe será listada.

    Returns:
        str: Uma string formatada com a lista de Pokémon ou uma mensagem de erro/informação.
    """
    if not id_treinador_alvo or not isinstance(id_treinador_alvo, str):
        return "Erro: O ID do treinador é inválido."
    
    client = get_bq_client()
    try:
        job_config = QueryJobConfig(query_parameters=[ScalarQueryParameter("id", "STRING", id_treinador_alvo)])
        
        res_treinador_job = client.query(f"SELECT nome_treinador FROM {TABLE_TREINADORES} WHERE id_treinador = @id", job_config=job_config)
        res_treinador = list(res_treinador_job.result())
        if not res_treinador:
            return f"Erro: Treinador com ID '{id_treinador_alvo}' não encontrado."
        nome_treinador_atual = res_treinador[0].nome_treinador
        
        equipe_job = client.query(f"SELECT nome_pokemon, tipo_primario, tipo_secundario FROM {TABLE_EQUIPE} WHERE id_treinador_fk = @id ORDER BY data_adicao", job_config=job_config)
        resultados_equipe = list(equipe_job.result())

        if not resultados_equipe:
            return f"O treinador '{nome_treinador_atual}' não possui Pokémon em sua equipe."
        
        lista_formatada = [f"Equipe de {nome_treinador_atual} (ID: {id_treinador_alvo}):"]
        for i, row in enumerate(resultados_equipe):
            tipos_str = row.tipo_primario
            if row.tipo_secundario:
                tipos_str += f" / {row.tipo_secundario}"
            lista_formatada.append(f"  {i+1}. {row.nome_pokemon.capitalize()} (Tipos: {tipos_str})")
        return "\n".join(lista_formatada)
    except Exception as e:
        return f"Erro ao listar Pokémon: {e}"


def apagar_pokemon(id_treinador_alvo: str, nome_pokemon_remover: str) -> str:
    """
    Remove um Pokémon específico da equipe de um treinador.

    Args:
        id_treinador_alvo (str): O ID do treinador.
        nome_pokemon_remover (str): O nome do Pokémon a ser removido da equipe.

    Returns:
        str: Uma mensagem de sucesso ou erro.
    """
    if not id_treinador_alvo or not isinstance(id_treinador_alvo, str):
        return "Erro: O ID do treinador é inválido."
    if not nome_pokemon_remover or not nome_pokemon_remover.strip():
        return "Erro: O nome do Pokémon a remover não pode ser vazio."

    client = get_bq_client()
    try:
        job_config = QueryJobConfig(query_parameters=[
            ScalarQueryParameter("id_treinador", "STRING", id_treinador_alvo),
            ScalarQueryParameter("nome_p", "STRING", nome_pokemon_remover.lower()),
        ])
        query_job = client.query(f"DELETE FROM {TABLE_EQUIPE} WHERE id_treinador_fk = @id_treinador AND LOWER(nome_pokemon) = @nome_p", job_config=job_config)
        query_job.result()
        
        if query_job.num_dml_affected_rows > 0:
            return f"Sucesso: Pokémon '{nome_pokemon_remover}' removido da equipe."
        else:
            return f"Informação: Pokémon '{nome_pokemon_remover}' não foi encontrado na equipe do treinador especificado."
    except Exception as e:
        return f"Erro ao apagar Pokémon: {e}"


def apagar_treinador(id_treinador_alvo: str, codigo_de_confirmacao: str) -> str:
    """
    Apaga um treinador e toda a sua equipe do banco de dados.

    Esta é uma operação destrutiva e requer um código de confirmação para ser executada.

    Args:
        id_treinador_alvo (str): O ID do treinador a ser apagado.
        codigo_de_confirmacao (str): O código de segurança necessário para autorizar a exclusão.

    Returns:
        str: Uma mensagem de sucesso ou erro.
    """
    if not verifica_senha(codigo_de_confirmacao):
        return "Erro: Código de confirmação incorreto. A operação foi cancelada."
    if not id_treinador_alvo or not isinstance(id_treinador_alvo, str):
        return "Erro: O ID do treinador é inválido."

    client = get_bq_client()
    try:
        # CORREÇÃO: Executamos os deletes sequencialmente com parâmetros.
        job_config = QueryJobConfig(query_parameters=[ScalarQueryParameter("id", "STRING", id_treinador_alvo)])

        # 1. Apagar os Pokémon da equipe (tabela filha)
        client.query(f"DELETE FROM {TABLE_EQUIPE} WHERE id_treinador_fk = @id", job_config=job_config).result()

        # 2. Apagar o treinador (tabela mãe)
        delete_trainer_job = client.query(f"DELETE FROM {TABLE_TREINADORES} WHERE id_treinador = @id", job_config=job_config)
        delete_trainer_job.result()

        if delete_trainer_job.num_dml_affected_rows > 0:
            return f"Sucesso: Treinador com ID '{id_treinador_alvo}' e toda a sua equipe foram apagados."
        else:
            return f"Informação: Nenhum treinador com ID '{id_treinador_alvo}' foi encontrado para apagar."

    except Exception as e:
        return f"Erro na transação ao apagar treinador: {e}"


def evoluir_pokemon(id_treinador: str, nome_pokemon_atual: str, nome_pokemon_evolucao: str) -> str:
    """
    Evolui um Pokémon da equipe de um treinador para sua próxima forma.

    A função valida se a evolução é válida usando a PokeAPI antes de atualizar o banco de dados.

    Args:
        id_treinador (str): O ID do treinador que possui o Pokémon.
        nome_pokemon_atual (str): O nome do Pokémon que irá evoluir.
        nome_pokemon_evolucao (str): O nome do Pokémon para o qual ele deve evoluir.

    Returns:
        str: Uma mensagem de sucesso ou erro.
    """
    if not id_treinador or not isinstance(id_treinador, str): return "Erro: O ID do treinador é inválido."
    nome_atual_lower = nome_pokemon_atual.strip().lower()
    nome_evolucao_lower = nome_pokemon_evolucao.strip().lower()
    
    dados_evolucao_api = get_pokemon_evolution(nome_atual_lower)
    if "error" in dados_evolucao_api: return f"Erro de API: {dados_evolucao_api['error']}"
    
    arvore_completa = dados_evolucao_api.get("evolution_tree_from_base")
    if not validar_proxima_evolucao(arvore_completa, nome_atual_lower, nome_evolucao_lower): return f"Erro de Lógica: A evolução de '{nome_pokemon_atual}' para '{nome_pokemon_evolucao}' não é um passo válido."
    
    dados_tipos_api = get_pokemon_types(nome_evolucao_lower)
    if "error" in dados_tipos_api: return f"Erro de API ao buscar tipos: {dados_tipos_api['error']}"
    
    tipos_val = dados_tipos_api.get("types", [])
    novo_tipo1 = tipos_val[0] if tipos_val else None
    novo_tipo2 = tipos_val[1] if len(tipos_val) > 1 else None
    
    client = get_bq_client()
    try:
        job_config = QueryJobConfig(query_parameters=[
            ScalarQueryParameter("novo_nome", "STRING", nome_evolucao_lower.capitalize()),
            ScalarQueryParameter("t1", "STRING", novo_tipo1),
            ScalarQueryParameter("t2", "STRING", novo_tipo2),
            ScalarQueryParameter("id_treinador", "STRING", id_treinador),
            ScalarQueryParameter("nome_antigo", "STRING", nome_atual_lower),
        ])
        query_job = client.query(f"""
            UPDATE {TABLE_EQUIPE}
            SET nome_pokemon = @novo_nome, tipo_primario = @t1, tipo_secundario = @t2
            WHERE id_treinador_fk = @id_treinador AND LOWER(nome_pokemon) = @nome_antigo
        """, job_config=job_config)
        query_job.result()

        if query_job.num_dml_affected_rows > 0:
            return f"Sucesso! O Pokémon '{nome_pokemon_atual.capitalize()}' evoluiu para '{nome_pokemon_evolucao.capitalize()}'!"
        else:
            return f"Erro: O treinador não possui um Pokémon chamado '{nome_pokemon_atual}' em sua equipe para evoluir."
    except Exception as e:
        return f"Erro ao tentar evoluir Pokémon no banco de dados: {e}"