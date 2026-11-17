"""
Coleta nativamente digital na API pública da Wikipedia (MediaWiki Action API).

Sem chave. Coleta, para uma página-semente e seus vizinhos de links recíprocos:
histórico de edições, links entre os artigos, e as edições em outros idiomas.
"""

import os
import re
import time
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set

import requests

# A Wikimedia dá 200 req/min a quem se identifica com contato no User-Agent e 10 req/min a quem não.
# https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits
USER_AGENT = os.getenv(
    "WIKIPEDIA_USER_AGENT",
    "metodos-digitais-a2/1.0 (https://github.com/GuOliv2306/trabalho_A2) python-requests",
)
TIMEOUT = 30
MIN_INTERVAL = 0.4  # segundos entre chamadas (~150 req/min, abaixo do limite de 200)
MAX_RETRIES = 4
CANDIDATE_CAP = 300  # shortcut: só os 300 primeiros vizinhos recíprocos disputam o recorte; subir se a semente for muito central


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def _get(s: requests.Session, url: str, params: Dict[str, Any]) -> requests.Response:
    """GET educado: espaça as chamadas e, em 429/503, espera o Retry-After antes de tentar de novo."""
    for attempt in range(MAX_RETRIES):
        time.sleep(MIN_INTERVAL)
        r = s.get(url, params=params, timeout=TIMEOUT)
        if r.status_code not in (429, 503) or attempt == MAX_RETRIES - 1:
            r.raise_for_status()
            return r
        retry_after = r.headers.get("Retry-After", "")
        time.sleep(min(int(retry_after) if retry_after.isdigit() else 5 * 2 ** attempt, 60))
    raise AssertionError("unreachable")


def _query(s: requests.Session, lang: str, **params) -> Iterator[Dict[str, Any]]:
    """Itera as respostas de action=query seguindo a paginação (`continue`)."""
    base = {"action": "query", "format": "json", "formatversion": 2, **params}
    cont: Dict[str, Any] = {}
    while True:
        data = _get(s, f"https://{lang}.wikipedia.org/w/api.php", {**base, **cont}).json()
        if "error" in data:
            raise RuntimeError(f"Wikipedia API: {data['error'].get('info', data['error'])}")
        yield data
        if "continue" not in data:
            return
        cont = data["continue"]


def _chunks(items: Sequence[str], size: int = 50) -> Iterator[Sequence[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def fetch_page_info(s: requests.Session, lang: str, titles: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """{título: {pageid, length, pageviews_30d}} para páginas existentes (segue redirects)."""
    out: Dict[str, Dict[str, Any]] = {}
    for chunk in _chunks(list(titles)):
        for data in _query(s, lang, prop="pageviews|info", titles="|".join(chunk), pvipdays=30, redirects=1):
            for p in data.get("query", {}).get("pages", []):
                if p.get("missing") or p.get("invalid"):
                    continue
                row = out.setdefault(p["title"], {"title": p["title"], "pageid": p["pageid"],
                                                  "length": p.get("length", 0), "pageviews_30d": 0})
                # a API entrega os pageviews em lotes: só soma quando o campo vem nesta resposta
                row["pageviews_30d"] += sum(v or 0 for v in p.get("pageviews", {}).values())
    return out


def fetch_links(s: requests.Session, lang: str, title: str, only: Optional[Sequence[str]] = None) -> Set[str]:
    """Links de saída (artigos) de `title`; com `only`, apenas os que apontam para esses títulos."""
    found: Set[str] = set()
    for chunk in (_chunks(list(only)) if only else [None]):
        extra = {"pltitles": "|".join(chunk)} if chunk else {}
        for data in _query(s, lang, prop="links", titles=title, plnamespace=0, pllimit="max", **extra):
            for p in data.get("query", {}).get("pages", []):
                found.update(l["title"] for l in p.get("links", []))
    return found


def fetch_backlinks(s: requests.Session, lang: str, title: str) -> Set[str]:
    """Artigos (sem redirects) que apontam para `title`."""
    found: Set[str] = set()
    for data in _query(s, lang, prop="linkshere", titles=title, lhnamespace=0, lhshow="!redirect", lhlimit="max"):
        for p in data.get("query", {}).get("pages", []):
            found.update(l["title"] for l in p.get("linkshere", []))
    return found


def fetch_revisions(s: requests.Session, lang: str, title: str, limit: int) -> List[Dict[str, Any]]:
    """As `limit` revisões mais recentes (mais nova primeiro), cruas."""
    revs: List[Dict[str, Any]] = []
    for data in _query(s, lang, prop="revisions", titles=title, rvlimit=min(500, limit),
                       rvprop="ids|timestamp|user|size|comment|tags|flags"):
        for p in data.get("query", {}).get("pages", []):
            revs.extend(p.get("revisions", []))
        if len(revs) >= limit:
            break
    return revs[:limit]


def fetch_bots(s: requests.Session, lang: str, users: Iterable[str]) -> Set[str]:
    """Usuários que têm hoje a flag de bot."""
    bots: Set[str] = set()
    for chunk in _chunks(sorted(set(users))):
        for data in _query(s, lang, list="users", ususers="|".join(chunk), usprop="groups"):
            bots.update(u["name"] for u in data.get("query", {}).get("users", []) if "bot" in u.get("groups", []))
    return bots


def parse_revisions(raw: List[Dict[str, Any]], bots: Set[str]) -> List[Dict[str, Any]]:
    """Normaliza revisões (mais nova primeiro): tipo de ator e variação de tamanho."""
    rows = []
    for i, r in enumerate(raw):
        user = r.get("user")
        if r.get("userhidden") or user is None:
            user, actor = None, "hidden"
        elif r.get("anon") or re.match(r"~\d{4}-", user):  # "~AAAA-N" = conta temporária (IP mascarado)
            actor = "anon"
        elif user in bots:
            actor = "bot"
        else:
            actor = "registered"
        older = raw[i + 1] if i + 1 < len(raw) else None
        if older:
            size_diff = r.get("size", 0) - older.get("size", 0)
        else:  # sem pai = criação do artigo; com pai fora da amostra, não dá para saber
            size_diff = r.get("size", 0) if not r.get("parentid") else None
        rows.append({
            "revid": r["revid"],
            "parentid": r.get("parentid"),
            "timestamp": r["timestamp"],
            "user": user,
            "actor_type": actor,
            "size": r.get("size", 0),
            "size_diff": size_diff,
            "minor": bool(r.get("minor")),
            "comment": r.get("comment", ""),
            "tags": list(r.get("tags", [])),
        })
    return rows


def pick_neighbors(links: Set[str], backlinks: Set[str], views: Dict[str, int], max_pages: int) -> List[str]:
    """Vizinhos recíprocos (linkam e são linkados pela semente), os mais vistos primeiro."""
    reciprocal = links & backlinks
    return sorted(reciprocal, key=lambda t: (-views.get(t, 0), t))[:max_pages]


def fetch_editions(s: requests.Session, lang: str, title: str, langs: Sequence[str]) -> List[Dict[str, Any]]:
    """Tamanho e audiência do mesmo artigo nas edições linguísticas pedidas (inclui a de origem)."""
    by_lang = {lang: title}
    for data in _query(s, lang, prop="langlinks", titles=title, lllimit="max"):
        for p in data.get("query", {}).get("pages", []):
            by_lang.update({l["lang"]: l["title"] for l in p.get("langlinks", [])})
    editions = []
    for code in dict.fromkeys([lang, *langs]):
        if code not in by_lang:
            continue
        info = fetch_page_info(s, code, [by_lang[code]])
        for row in info.values():
            editions.append({"lang": code, "title": row["title"], "length": row["length"],
                             "pageviews_30d": row["pageviews_30d"]})
    return editions


def collect_topic(seed: str, lang: str = "pt", max_pages: int = 10, rev_limit: int = 500,
                  edition_langs: Sequence[str] = ("en", "es", "fr", "de"),
                  titles: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """
    Coleta um tema a partir de uma página-semente.

    Recorte: com `titles`, semente + essa lista curada (títulos inexistentes voltam em
    `not_found`); sem, semente + vizinhos de link recíproco mais vistos nos últimos 30 dias.
    Levanta LookupError se a semente não existir.
    """
    s = _session()
    seed_info = fetch_page_info(s, lang, [seed])
    if not seed_info:
        raise LookupError(f"Artigo '{seed}' não encontrado em {lang}.wikipedia.org")
    seed_title = next(iter(seed_info))

    curated, titles = titles, [seed_title]
    pages = dict(seed_info)
    not_found: List[str] = []
    if curated:
        for t in curated:
            info = fetch_page_info(s, lang, [t])  # um por vez: redirects mudam o título e não dá para casar em lote
            not_found += [] if info else [t]
            for resolved, row in info.items():
                if resolved not in pages:
                    pages[resolved] = row
                    titles.append(resolved)
    elif max_pages > 1:
        links = fetch_links(s, lang, seed_title)
        backlinks = fetch_backlinks(s, lang, seed_title)
        candidates = sorted(links & backlinks)[:CANDIDATE_CAP]
        info = fetch_page_info(s, lang, candidates)
        neighbors = pick_neighbors(set(info), set(info), {t: r["pageviews_30d"] for t, r in info.items()},
                                   max_pages - 1)
        titles += [t for t in neighbors if t != seed_title]
        pages.update({t: info[t] for t in neighbors})

    raw = {t: fetch_revisions(s, lang, t, rev_limit) for t in titles}
    registered = {r["user"] for revs in raw.values() for r in revs if r.get("user") and not r.get("anon")}
    bots = fetch_bots(s, lang, registered)

    link_pairs = []
    if len(titles) > 1:
        for t in titles:
            link_pairs += [(t, target) for target in sorted(fetch_links(s, lang, t, only=titles)) if target != t]

    return {
        "lang": lang,
        "seed": seed_title,
        "pages": [pages[t] for t in titles],
        "revisions": {t: parse_revisions(raw[t], bots) for t in titles},
        "links": link_pairs,
        "editions": fetch_editions(s, lang, seed_title, edition_langs),
        "not_found": not_found,
    }


# ===== HISTÓRICO PARA EXPERIMENTOS NATURAIS =====

REVERT_WINDOW = 15  # quantas versões anteriores olhar para reconhecer uma reversão


def fetch_history(s: requests.Session, lang: str, title: str, start: str, end: str) -> List[Dict[str, Any]]:
    """Todas as revisões de `title` entre `start` e `end` (da mais antiga para a mais nova), com o sha1 do conteúdo."""
    revs: List[Dict[str, Any]] = []
    for data in _query(s, lang, prop="revisions", titles=title, rvlimit="max", rvdir="newer",
                       rvstart=f"{start}T00:00:00Z", rvend=f"{end}T00:00:00Z", rvprop="ids|timestamp|user|flags|sha1"):
        for p in data.get("query", {}).get("pages", []):
            revs.extend(p.get("revisions", []))
    return revs


def fetch_creation(s: requests.Session, lang: str, title: str) -> Optional[str]:
    """Data da primeira revisão do artigo."""
    for data in _query(s, lang, prop="revisions", titles=title, rvlimit=1, rvdir="newer", rvprop="timestamp"):
        for p in data.get("query", {}).get("pages", []):
            for r in p.get("revisions", []):
                return r["timestamp"]
        break
    return None


def fetch_langlinks(s: requests.Session, lang: str, titles: Sequence[str], target: str) -> Dict[str, str]:
    """{título em `lang`: título do mesmo artigo em `target`}, só para os que existem lá."""
    out: Dict[str, str] = {}
    for chunk in _chunks(list(titles)):
        for data in _query(s, lang, prop="langlinks", titles="|".join(chunk), lllang=target, lllimit="max"):
            for p in data.get("query", {}).get("pages", []):
                for link in p.get("langlinks", []):
                    out[p["title"]] = link["title"]
    return out


def detect_reverts(sha1s: Sequence[Optional[str]], window: int = REVERT_WINDOW) -> List[bool]:
    """
    Reversão por identidade: a revisão devolve o artigo a um conteúdo idêntico ao de uma das
    `window` versões anteriores. Repetir a versão imediatamente anterior é edição nula, não reversão.
    Independe das tags do MediaWiki, então vale para qualquer época.
    """
    out = []
    for i, sha in enumerate(sha1s):
        previous = sha1s[max(0, i - window):i]
        out.append(bool(sha is not None and previous and previous[-1] != sha and sha in previous))
    return out


def monthly_counts(raw: List[Dict[str, Any]], bots: Set[str], start: str, end: str):
    """Contagens por mês (meses sem edição entram como zero): pessoas, registradas, anônimas, robôs, reversões."""
    import pandas as pd
    months = pd.date_range(start, end, freq="MS", inclusive="left")
    raw = sorted(raw, key=lambda r: r["timestamp"])
    rows = []
    for r, reverted in zip(raw, detect_reverts([r.get("sha1") for r in raw])):
        user = r.get("user")
        anon = bool(r.get("anon") or (user and re.match(r"~\d{4}-", user)))
        bot = bool(user in bots) and not anon
        rows.append({"month": r["timestamp"][:7], "anon_edits": int(anon), "bot_edits": int(bot),
                     "registered_edits": int(not anon and not bot), "human_edits": int(not bot), "reverts": int(reverted)})
    columns = ["human_edits", "registered_edits", "anon_edits", "bot_edits", "reverts"]
    counts = pd.DataFrame(rows, columns=["month"] + columns).groupby("month")[columns].sum()
    counts = counts.reindex(months.strftime("%Y-%m"), fill_value=0)
    counts.insert(0, "month", [m.date() for m in months])
    return counts.reset_index(drop=True)


def collect_history_pairs(seed: str, treated_lang: str, control_langs: Sequence[str], start: str, end: str,
                          max_candidates: int = 40, rng_seed: int = 0) -> Dict[str, Any]:
    """
    Histórico mensal dos mesmos artigos em vários idiomas, para um experimento natural.

    Artigos: sorteio (reprodutível) entre os links da página-semente que existem em todos os
    idiomas de controle. Sorteio, e não "os mais vistos": os mais vistos costumam estar protegidos.
    Devolve `units` (pair, lang, title, created) e `monthly` (uma linha por artigo, idioma e mês).
    """
    import random

    import pandas as pd
    s = _session()
    links = sorted(fetch_links(s, treated_lang, seed))
    if not links:
        raise LookupError(f"Artigo '{seed}' não encontrado ou sem links em {treated_lang}.wikipedia.org")
    random.Random(rng_seed).shuffle(links)
    titles_by_lang = {lang: fetch_langlinks(s, treated_lang, links, lang) for lang in control_langs}
    pairs = [t for t in links if all(t in titles_by_lang[lang] for lang in control_langs)][:max_candidates]

    units, histories = [], {}
    for pair in pairs:
        for lang in [treated_lang, *control_langs]:
            title = pair if lang == treated_lang else titles_by_lang[lang][pair]
            histories[(pair, lang)] = fetch_history(s, lang, title, start, end)
            units.append({"pair": pair, "lang": lang, "title": title, "created": fetch_creation(s, lang, title)})

    frames = []
    for lang in [treated_lang, *control_langs]:
        users = {r["user"] for (_, l), revs in histories.items() if l == lang
                 for r in revs if r.get("user") and not r.get("anon")}
        bots = fetch_bots(s, lang, users)
        for u in units:
            if u["lang"] == lang:
                m = monthly_counts(histories[(u["pair"], lang)], bots, start, end)
                frames.append(m.assign(pair=u["pair"], lang=lang, title=u["title"]))
    monthly = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return {"units": pd.DataFrame(units), "monthly": monthly}
