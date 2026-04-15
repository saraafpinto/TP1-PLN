import json
import re
import unicodedata
import os

def normalizar_chave(texto):
    """Normaliza o termo para comparação (sem acentos, minúsculas)."""
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    t = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    t = re.sub(r'\[.*?\]|\s+s\.[mf]\.|\s+n\s+[mf]\b|\s+n\s+pl\b|\s+adj\b|\s+v\s+intr\b|\s+v\s+tr\b|\s+v\s+tr/intr\b|\s+-[a-z]\b|\(.*\)', '', t)
    return t.strip()

def criar_estrutura_base(termo_exibicao):
    """Retorna o template do dicionário com listas para acumulação."""
    return {
        "termo_principal": termo_exibicao,
        "genero": "",
        "siglas": [],
        "categorias": [],
        "definicoes": [],
        "termos_populares": [],
        "pesquisa": [],
        "inf_encicl": "",
        "sinonimos": [],
        "variantes": [],
        "notas_extras": [],
        "traducoes": {}, 
        "remissoes": [],
        "fontes": []
    }

def limpar_vazios(dicionario):
    """Apaga todas as chaves que estiverem vazias ([], "", {})."""
    if isinstance(dicionario, dict):
        novo_dic = {}
        for k, v in dicionario.items():
            v_limpo = limpar_vazios(v)
            if v_limpo or v_limpo is False or v_limpo == 0: 
                novo_dic[k] = v_limpo
        return novo_dic
    elif isinstance(dicionario, list):
        lista_limpa = [limpar_vazios(item) for item in dicionario]
        return [item for item in lista_limpa if item or item is False or item == 0]
    else:
        return dicionario

def consolidar_final():
    master_dict = {}

    # --- 1. PROCESSAR FICHEIROS PT (Listas e Dicionários de Objetos) ---
    fontes_pt = [
        ("Glossario_enfermagem/glossario_enfermagem.json", "definicao"),
        ("glossario_ministerio/conceitos_ministerio.json", "definicao"),
        ("glossario_neologismos/glossario_neologismos.json", "definição"),
        ("glossario_tematico/glossario_tematico_conceitos.json", "definicao"),
        ("glossario_termos/glossario_termos.json", "termo popular"),
        ("ICNP/cipe.json", "definicao"),
        ("ossos/ossos_conceitos.json", "definicao"),
    ]

    for filename, field_def in fontes_pt:
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            # Universalizador: transforma Listas e Dicionários numa lista iterável uniforme
            if isinstance(dados, dict):
                items = dados.items()
            else:
                # Se for lista, o "termo" (a chave principal) está dentro do objeto
                items = [(item.get("termo", ""), item) for item in dados if isinstance(item, dict)]
            
            for termo, info in items:
                chave = normalizar_chave(termo)
                if not chave: continue
                
                if chave not in master_dict:
                    master_dict[chave] = criar_estrutura_base(termo)
                
                ent = master_dict[chave]
                if filename not in ent["fontes"]: ent["fontes"].append(filename)
                
                if isinstance(info, dict):
                    
                    # Acumular definições
                    if filename == "glossario_termos/glossario_termos.json":
                        pop = info.get("termo popular")
                        # O teu código junta-os com "/", por isso guardamos a string direta
                        if pop and pop not in ent["termos_populares"]: 
                            ent["termos_populares"].append(pop)
                    else:
                        d = info.get(field_def)
                        if d and d not in ent["definicoes"]: 
                            ent["definicoes"].append(d)
                            
                    d = info.get(field_def)
                    if d and d not in ent["definicoes"]: ent["definicoes"].append(d)
                    
                    # Acumular Categorias, Siglas e Género
                    cat = info.get("categoria") or info.get("area") or info.get("eixo")
                    if cat and cat not in ent["categorias"]: ent["categorias"].append(cat)
                    if info.get("sigla") and info["sigla"] not in ent["siglas"]: ent["siglas"].append(info["sigla"])
                    if not ent["genero"] and info.get("genero"): ent["genero"] = info["genero"]
                    
                    # CORREÇÃO: Sinónimos (Apanha singular e plural)
                    sins = info.get("sinonimos") or info.get("sinonimo") or []
                    if isinstance(sins, str): sins = [sins]
                    for s in sins:
                        if s and s not in ent["sinonimos"]: ent["sinonimos"].append(s)

                    if info.get("inf_encicl") and not ent["inf_encicl"]: 
                        ent["inf_encicl"] = info.get("inf_encicl")
                    
                    # Notas podem vir como lista (temático) ou string
                    notas = info.get("notas") or info.get("nota") or []
                    if isinstance(notas, str): notas = [notas]
                    for n in notas:
                        if n and n not in ent["notas_extras"]: ent["notas_extras"].append(n)
                        
                    # Remissões (temático)
                    remissas = info.get("remissa") or []
                    for r in remissas:
                        if r and r not in ent["remissoes"]: ent["remissoes"].append(r)

                    if info.get("pesquisa") and info["pesquisa"] not in ent["pesquisa"]: ent["pesquisa"].append(info["pesquisa"])

                    # Traduções
                    trads_fonte = info.get("traducoes") or info.get("traducao") or {}
                    if isinstance(trads_fonte, dict):
                        for lang, valor_trad in trads_fonte.items():
                            if not valor_trad: continue
                            
                            # Normalização das chaves das línguas (espanhol -> es, ingles -> en)
                            lang_limpa = lang.lower()
                            if lang_limpa in ["inglês", "ingles", "ing"]: lang_limpa = "en"
                            if lang_limpa in ["espanhol", "esp"]: lang_limpa = "es"
                            
                            if lang_limpa not in ent["traducoes"]: ent["traducoes"][lang_limpa] = []
                            
                            termo_limpo = re.sub(r'\s*\[.*?\]', '', str(valor_trad)).strip()
                            if termo_limpo and termo_limpo not in ent["traducoes"][lang_limpa]:
                                ent["traducoes"][lang_limpa].append(termo_limpo)


    # --- 2. PROCESSAR WIPO E MULTILINGUE (Verificação e Enriquecimento) ---
    fontes_multi = ["WIPO/wipo.json", "Dmultilingue/conceitos/dicionario_conceitos.json", "medicina/medicina.json"]
    
    for filename in fontes_multi:
        with open(filename, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            # WIPO é um dict, Multilingue é uma list
            lista_iteravel = dados.items() if isinstance(dados, dict) else [(item.get("termo", ""), item) for item in dados]
                
            for termo_estrangeiro, info in lista_iteravel:
                trads = info.get("traducoes", {})
                
                # O termo PT pode estar nas traduções, ou ser a própria chave (se for o dicionario_conceitos)
                pt_raw = trads.get("PT") or trads.get("pt [PT]") or trads.get("pt")

                if not pt_raw or str(pt_raw).strip() == "" or str(pt_raw).lower() == "none":
                    continue
                
                pt_term = ""
                pt_sinonimos = []
                
                # A CORREÇÃO MÁGICA: O pt_raw agora pode ser um dicionário (vindo do WIPO novo) ou uma string!
                if isinstance(pt_raw, dict):
                    pt_term = pt_raw.get("termo", "")
                    pt_sinonimos = pt_raw.get("sinonimos", [])
                else:
                    pt_term = str(pt_raw).split(' - ')[0].strip()

                if not pt_term: 
                    continue

                chave_pt = None
                termo_para_criar = pt_term.split(',')[0].split(';')[0].strip()
                
                if filename == "medicina/medicina.json":
                    pt_limpo = pt_term.replace('\n', ' ')
                    pt_limpo = re.sub(r'\s+', ' ', pt_limpo).strip()
                    
                    partes = pt_limpo.split(';')
                    candidatos = []

                    for p in partes:
                        if "[Pt" in p or "[PT" in p:
                            m = re.search(r'(.*?)\s*\[Pt', p, re.IGNORECASE)
                            if m: candidatos.append(m.group(1).strip())
                        else:
                            candidatos.append(re.sub(r'\[.*?\]', '', p).strip())

                    for cand in candidatos:
                        ch = normalizar_chave(cand)
                        if ch in master_dict:
                            chave_pt = ch
                            termo_para_criar = cand
                            break
                    
                    if not chave_pt and candidatos:
                        termo_para_criar = candidatos[0]
                        chave_pt = normalizar_chave(termo_para_criar)

                else:
                    chave_pt = normalizar_chave(termo_para_criar)
                
                # --- SÓ TRABALHA SE TIVERMOS UMA CHAVE VÁLIDA ---
                if chave_pt and isinstance(chave_pt, str): 
    
                    if chave_pt not in master_dict:
                        master_dict[chave_pt] = criar_estrutura_base(termo_para_criar)

                    ent = master_dict[chave_pt]
                    if filename not in ent["fontes"]: ent["fontes"].append(filename)
                    
                    # ========================================================
                    # ========================================================
                    # SE FOR O MEDICINA -> GUARDA DEFINIÇÕES, CATEGORIAS E GÉNERO
                    # O WIPO e o Multilingue apenas contribuem com Traduções e Sinónimos!
                    # ========================================================
                    # ========================================================
                    if filename == "medicina/medicina.json":
                        d = info.get("definicao") or info.get("Definicao") or info.get("descricao")
                        if d and d not in ent["definicoes"]: ent["definicoes"].append(d)
                        
                        c = info.get("categoria") or info.get("Categoria") or info.get("categoria_lexica") or info.get("area_tematica")
                        if c and c not in ent["categorias"]: ent["categorias"].append(c)

                        if not ent["genero"] and info.get("genero"): 
                            ent["genero"] = info.get("genero")

                    # Injeta sinónimos da chave raiz E os sinónimos extraídos da língua PT do WIPO
                    sins = info.get("sinonimos") or info.get("sinonimo") or []
                    if isinstance(sins, str): sins = [sins]
                    sins.extend(pt_sinonimos) # AQUI ENTRAM OS SINÓNIMOS NOVOS DO PT!
                    
                    for s in sins:
                        if s and s not in ent["sinonimos"]: ent["sinonimos"].append(s)
                        
                    notas = info.get("notas") or info.get("nota") or []
                    if isinstance(notas, str): notas = [notas]
                    for n in notas:
                        if n and n not in ent["notas_extras"]: ent["notas_extras"].append(n)

                    # ========================================================
                    # TRADUÇÕES E CHAVES ESTRANGEIRAS
                    # ========================================================
                    codigos_linguas = ['oc', 'eu', 'gl', 'es', 'en', 'fr', 'pt', 'nl', 'ar', 'ca', 'it', 'de', 'ru', 'ja', 'ko', 'zh']
                    for lang, val in trads.items():
                        if not val: continue
                        
                        l_std = lang.replace(" [PT]", "").replace(" [BR]", "_br").lower()
                        
                        # NOVO: val pode ser um dicionário com sinonimos (WIPO) ou apenas string
                        val_termo = ""
                        val_sinonimos = []
                        if isinstance(val, dict):
                            val_termo = val.get("termo", "")
                            val_sinonimos = val.get("sinonimos", [])
                        else:
                            val_termo = str(val)
                        
                        # --- LIMPEZA DO VALOR PRINCIPAL ---
                        val_limpo = val_termo.strip()
                        
                        for cod in codigos_linguas:
                            val_limpo = re.sub(rf'^.*?\b{cod}\b\s+', '', val_limpo, flags=re.IGNORECASE)

                        val_limpo = val_limpo.split(' - ')[0].strip()
                        
                        if l_std not in ent["traducoes"]: 
                            ent["traducoes"][l_std] = []
                            
                        termo_limpo = re.sub(r'\s*\[.*?\]', '', val_limpo).strip()
                        if termo_limpo and termo_limpo not in ent["traducoes"][l_std]:
                            ent["traducoes"][l_std].append(termo_limpo)
                            
                        # INJETAR OS SINÓNIMOS ESTRANGEIROS DIRETAMENTE NA LISTA DA LÍNGUA
                        for s_trad in val_sinonimos:
                            s_trad_limpo = s_trad.strip()
                            if s_trad_limpo and s_trad_limpo not in ent["traducoes"][l_std]:
                                ent["traducoes"][l_std].append(s_trad_limpo)
                    
                    # Salvar a chave do WIPO (que é o termo em Inglês!)
                    if filename == "WIPO/wipo.json" and termo_estrangeiro:
                        if "en" not in ent["traducoes"]: ent["traducoes"]["en"] = []
                        if termo_estrangeiro not in ent["traducoes"]["en"]: ent["traducoes"]["en"].append(termo_estrangeiro)

                    # Salvar a chave do Multilingue (que é o termo em Catalão/Italiano!)
                    if filename == "Dmultilingue/conceitos/dicionario_conceitos.json" and termo_estrangeiro:
                        ca_val = str(termo_estrangeiro).strip()
                        ca_val = re.sub(r'^\d+\s+', '', ca_val)
                        for cod in codigos_linguas:
                            ca_val = re.sub(rf'^.*?\b{cod}\b\s+', '', ca_val, flags=re.IGNORECASE)
                        ca_val = ca_val.split(' - ')[0].strip()
                        
                        if "ca" not in ent["traducoes"]: 
                            ent["traducoes"]["ca"] = []
                        if ca_val and ca_val not in ent["traducoes"]["ca"]:
                            ent["traducoes"]["ca"].append(ca_val)

    # --- 3. LIMPEZA FINAL E ORDENAÇÃO ---
    for chave in master_dict:
        master_dict[chave]["definicoes"] = list(dict.fromkeys(master_dict[chave]["definicoes"]))
        master_dict[chave]["termos_populares"] = list(dict.fromkeys(master_dict[chave]["termos_populares"])) 
        master_dict[chave]["fontes"] = sorted(list(set(master_dict[chave]["fontes"])))
        master_dict[chave]["categorias"] = sorted(list(set(master_dict[chave]["categorias"])))
        master_dict[chave]["siglas"] = sorted(list(set(master_dict[chave]["siglas"])))
        
   
    master_dict_ordenado = dict(sorted(master_dict.items()))

    dicionario_limpo = limpar_vazios(master_dict_ordenado)

    def gravar_json(filename, dicionario):
        # 1. Gera a string JSON com a indentação normal
        json_str = json.dumps(dicionario, indent=4, ensure_ascii=False)
        
        # 2. Achatar listas e dicionários vazios (caso algum escape à limpeza)
        json_str = re.sub(r'\[\s*\]', '[]', json_str)
        json_str = re.sub(r'\{\s*\}', '{}', json_str)
        
        # 3. Achatar listas com apenas 1 elemento de texto
        # Transforma: [ \n "termo" \n ]  ->  ["termo"]
        json_str = re.sub(r'\[\s*("[^"]+")\s*\]', r'[\1]', json_str)
        
        # 4. Gravar no ficheiro final
        with open(filename, 'w', encoding='utf-8') as f_out:
            f_out.write(json_str)
        
    gravar_json("DICIONARIO_GIGANTE_FINAL.json", dicionario_limpo)

    print(f"Sucesso! Dicionário consolidado com {len(dicionario_limpo)} termos únicos.")

if __name__ == "__main__":
    consolidar_final()