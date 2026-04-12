import json
import re
import unicodedata
import os

def normalizar_chave(texto):
    """Limpa o termo para garantir a união perfeita entre ficheiros."""
    if not texto: return ""
    # Remover acentos
    nfkd = unicodedata.normalize('NFKD', str(texto))
    t = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    # Remover classes gramaticais e marcas de país
    t = re.sub(r'\[.*?\]|\s+s\.[mf]\.|\s+n\s+[mf]|\(.*?\)', '', t)
    return t.replace(';', '').strip()

def consolidar():
    master = {}        # Chave normalizada -> Dados do termo
    term_to_id = {}    # Chave normalizada -> ID Medicina
    id_to_chaves = {}  # ID Medicina -> Lista de chaves normalizadas que o partilham

    # 1. PRÉ-PROCESSAR MEDICINA (ID -> INFO)
    med_info_id = {}
    if os.path.exists("medicina/medicina.json"):
        with open("medicina/medicina.json", "r", encoding="utf-8") as f:
            med_data = json.load(f)
            for k, v in med_data.items():
                mid = str(v.get('id', ''))
                if not mid: continue
                if mid not in med_info_id:
                    med_info_id[mid] = {"trads": {}, "cats": set(), "notas": set()}
                # Atualizar info (sem sobrepor cegamente para evitar o erro do 'a termo')
                target = med_info_id[mid]
                target["trads"].update(v.get('traducoes', {}))
                if v.get('area'): target["cats"].add(v['area'])
                if v.get('nota'): target["notas"].add(v['nota'])

    # 2. MAPEAMENTO PRINCIPAL (medicina_portugues.json)
    if os.path.exists("medicina/medicina_portugues.json"):
        with open("medicina/medicina_portugues.json", "r", encoding="utf-8") as f:
            for termo_pt, mid in json.load(f).items():
                mid = str(mid)
                chave = normalizar_chave(termo_pt)
                if not chave: continue
                
                term_to_id[chave] = mid
                if mid not in id_to_chaves: id_to_chaves[mid] = set()
                id_to_chaves[mid].add(chave)
                
                if chave not in master:
                    master[chave] = {
                        "termo": termo_pt.split('[')[0].strip(),
                        "definicoes": [], "traducoes": {}, "categorias": set(), "fontes": set()
                    }
                
                # Injetar dados da Medicina (ID)
                master[chave]["fontes"].add("medicina/medicina_portugues.json")
                if mid in med_info_id:
                    info = med_info_id[mid]
                    master[chave]["traducoes"].update(info["trads"])
                    # Correção Crítica: O PT deve ser o termo do dicionário PT, não o do ID duplicado
                    master[chave]["traducoes"]["pt"] = termo_pt
                    for c in info["cats"]: master[chave]["categorias"].add(c)
                    for n in info["notas"]: 
                        if n not in master[chave]["definicoes"]: master[chave]["definicoes"].append(n)

    # 3. PROCESSAR TODOS OS OUTROS GLOSSÁRIOS
    # Dicionário de ficheiros e a sua chave de conteúdo
    fontes_extra = {
        "Glossario_enfermagem/glossario_enfermagem.json": "definicao",
        "glossario_ministerio/conceitos_ministerio.json": "Descricao",
        "glossario_tematico/glossario_tematico_conceitos.json": "definicao",
        "glossario_termos/glossario_termos.json": "significado",
        "glossario_neologismos/glossario_neologismos.json": "descricao",
        "Dmultilingue/abreviaturas/abreviaturas_dicionario.json": "nota",
        "WIPO/wipo.json": "Descricao",
        "ICNP/cipe.json": "descricao",
        "glossario_medico/glossario_medico.json": "definicao"
    }

    for fname, def_key in fontes_extra.items():
        if not os.path.exists(fname): continue
        with open(fname, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
            # Normalizar iteração (lista ou dicionário)
            itens = dados if isinstance(dados, list) else dados.values() if "cipe" in fname else dados.items()
            
            for item in itens:
                if isinstance(item, tuple): # Chave: Valor
                    t_orig, info = item
                elif isinstance(item, dict): # Objeto (CIPE ou Lista)
                    t_orig = item.get("termo") or item.get("designacao") or ""
                    info = item
                else: continue
                
                chave = normalizar_chave(t_orig)
                if not chave: continue

                # Se este termo partilha um ID com outros, atualizamos todos os "irmãos"
                alvos = [chave]
                if chave in term_to_id:
                    mid = term_to_id[chave]
                    alvos = list(id_to_chaves[mid])
                
                for t_chave in alvos:
                    if t_chave not in master:
                        master[t_chave] = {"termo": t_orig, "definicoes": [], "traducoes": {}, "categorias": set(), "fontes": set()}
                    
                    entry = master[t_chave]
                    entry["fontes"].add(fname)
                    
                    if isinstance(info, dict):
                        # Definição
                        d = info.get(def_key)
                        if d and d not in entry["definicoes"]: entry["definicoes"].append(d)
                        # Categorias/Eixo
                        cat = info.get("area") or info.get("Categoria") or info.get("eixo")
                        if cat: entry["categorias"].add(str(cat))
                        # Traduções
                        tr = info.get("traducoes") or info.get("Traducoes")
                        if isinstance(tr, dict): entry["traducoes"].update({k.lower(): v for k, v in tr.items()})
                    else:
                        # Caso seja apenas uma string (abreviaturas)
                        if info not in entry["definicoes"]: entry["definicoes"].append(str(info))

    # 4. TRATAMENTO ESPECIAL: conceitos_dicionario.json (Catalão -> PT)
    if os.path.exists("Dmultilingue/conceitos/conceitos_dicionario.json"):
        with open("Dmultilingue/conceitos/conceitos_dicionario.json", "r", encoding="utf-8") as f:
            for info in json.load(f).values():
                tr = info.get("traducoes", {})
                pt = tr.get("pt") or tr.get("pt [PT]") or tr.get("pt [BR]")
                if pt:
                    pt_limpo = pt.split(';')[0].split(' n ')[0].strip()
                    chave = normalizar_chave(pt_limpo)
                    if chave in master:
                        if info.get("definicao"): master[chave]["definicoes"].append(info["definicao"])
                        master[chave]["fontes"].add("Dmultilingue/conceitos/conceitos_dicionario.json")

    # 5. CONVERTER SETS PARA LISTAS E GUARDAR
    for k in master:
        master[k]["categorias"] = sorted(list(master[k]["categorias"]))
        master[k]["fontes"] = sorted(list(master[k]["fontes"]))

    with open("DICIONARIO_MESTRE_FINAL.json", "w", encoding="utf-8") as f:
        json.dump(master, f, indent=4, ensure_ascii=False)
    
    print(f"Consolidação concluída: {len(master)} termos.")

consolidar()