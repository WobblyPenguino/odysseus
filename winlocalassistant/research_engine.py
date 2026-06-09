from __future__ import annotations

import html
import ipaddress
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text, unique_path

from .config import APP_DIR, AssistantConfig

LOGGER = logging.getLogger(__name__)

RESEARCH_DIR = APP_DIR / "research_reports"
USER_AGENT = "NovaResearch/1.0 (+local user initiated research)"

@dataclass
class ResearchSource:
    title: str
    url: str
    domain: str
    text: str
    source_type: str
    bias_risk: str
    bias_notes: list[str]
    credibility_notes: list[str]


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</p>|</li>|</h[1-6]>", "\n", raw)
    raw = re.sub(r"(?is)<.*?>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\n\s*\n+", "\n\n", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    return raw.strip()


def _title_from_html(raw: str, fallback: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    if m:
        return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:180]
    return fallback


def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _classify_source(domain: str, url: str, title: str) -> str:
    d = domain.lower()
    if any(x in d for x in [".gov", "who.int", "abs.gov", "bom.gov", "nasa.gov", "data.gov"]):
        return "government/statistical"
    if any(x in d for x in [".edu", "arxiv.org", "scholar", "pubmed", "nature.com", "science.org", "springer", "elsevier", "wiley"]):
        return "academic/research"
    if any(x in d for x in ["reuters.com", "apnews.com", "abc.net.au", "bbc.com", "theguardian.com", "nytimes.com"]):
        return "news/journalism"
    if any(x in d for x in ["wikipedia.org"]):
        return "tertiary/encyclopedia"
    if any(x in d for x in ["github.com", "docs.", "developer."]):
        return "technical documentation/repository"
    if any(x in d for x in ["medium.com", "substack.com", "blog", "wordpress", "reddit.com", "x.com", "twitter.com"]):
        return "commentary/social/blog"
    return "general web"


def _bias_and_credibility(domain: str, text: str, source_type: str) -> tuple[str, list[str], list[str]]:
    low = text.lower()
    bias: list[str] = []
    cred: list[str] = []
    risk = "medium"
    if source_type in {"government/statistical", "academic/research", "technical documentation/repository"}:
        risk = "low-to-medium"
        cred.append("Primary or specialist source type; still check methodology, date and scope.")
    if source_type in {"commentary/social/blog", "general web"}:
        risk = "medium-to-high"
        bias.append("Source type may contain personal, promotional or unreviewed claims.")
    if any(w in low for w in ["sponsored", "affiliate", "buy now", "pricing", "our product", "sign up"]):
        risk = "high"
        bias.append("Commercial/promotion language detected.")
    if any(w in low for w in ["always", "never", "obviously", "shocking", "secret", "destroy", "guaranteed"]):
        bias.append("Loaded or absolute language detected; verify claims against neutral sources.")
    if any(w in low for w in ["method", "data", "sample", "limitations", "confidence", "uncertainty", "citation", "references"]):
        cred.append("Contains methodology, data, uncertainty or reference markers.")
    if len(text) < 700:
        bias.append("Short extract; conclusions may be under-supported.")
    if not cred:
        cred.append("No strong methodology/citation signals detected in the extracted text.")
    return risk, bias, cred




def _normalise_source_urls(urls: list[str], max_sources: int) -> tuple[list[str], list[dict[str, str]]]:
    """Normalise/dedupe user or search URLs and reject unsafe fetch targets."""
    accepted: list[str] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in urls:
        candidate = (raw or "").strip().strip("<>\"'.,;)")
        if not candidate:
            continue
        parsed = urllib.parse.urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            rejected.append({"url": candidate, "reason": "Only absolute http/https source URLs can be fetched."})
            continue
        host = (parsed.hostname or "").lower()
        if _is_blocked_fetch_host(host):
            rejected.append({"url": candidate, "reason": "Blocked local/private/link-local source target for research safety."})
            continue
        normalised = urllib.parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))
        key = normalised.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        accepted.append(normalised)
        if len(accepted) >= max(1, int(max_sources)):
            break
    return accepted, rejected


def _is_blocked_fetch_host(host: str) -> bool:
    if not host:
        return True
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        return bool(ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)
    except ValueError:
        return False

def _fetch_url(url: str, max_chars: int = 16000) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read(max_chars * 4)
        ctype = resp.headers.get("content-type", "")
    enc = "utf-8"
    m = re.search(r"charset=([^;]+)", ctype, re.I)
    if m:
        enc = m.group(1).strip()
    text = raw.decode(enc, errors="replace")
    title = _title_from_html(text, url)
    return title, _strip_html(text)[:max_chars]


def _duckduckgo_search(topic: str, limit: int = 8) -> list[str]:
    q = urllib.parse.quote_plus(topic)
    url = f"https://duckduckgo.com/html/?q={q}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read(120000).decode("utf-8", errors="replace")
    urls: list[str] = []
    for m in re.finditer(r'href="([^"]+)"', raw):
        href = html.unescape(m.group(1))
        if "uddg=" in href:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [""])[0]
            href = parsed or href
        if href.startswith("http") and "duckduckgo.com" not in href and href not in urls:
            urls.append(href)
        if len(urls) >= limit:
            break
    return urls


def _seed_source_urls(topic: str, limit: int = 8) -> list[str]:
    low = (topic or "").lower()
    urls: list[str] = []
    def add_url(url: str) -> None:
        if url not in urls and len(urls) < limit:
            urls.append(url)
    if any(x in low for x in ["ww2", "world war 2", "world war ii", "second world war"]):
        add_url("https://en.wikipedia.org/wiki/World_War_II")
        add_url("https://www.britannica.com/event/World-War-II")
        add_url("https://www.iwm.org.uk/history/first-world-war-and-the-second-world-war")
    if "neil" in low and "seal" in low:
        add_url("https://en.wikipedia.org/wiki/Neil_the_Seal")
        add_url("https://www.theguardian.com/australia-news/2023/dec/22/neil-the-seal-tasmania-australia-outside-homes-footage-viral-fame-welfare")
        add_url("https://time.com/6550164/neil-the-seal-tasmania-background-instagram-tiktok/")
    if "tasmania" in low and "seal" in low:
        add_url("https://nre.tas.gov.au/wildlife-management/marine-conservation-program/seals")
    return urls


def _wikipedia_opensearch(topic: str, limit: int = 4) -> list[str]:
    api = "https://en.wikipedia.org/w/api.php?action=opensearch&format=json&limit=" + str(max(1, min(limit, 8))) + "&search=" + urllib.parse.quote(topic)
    req = urllib.request.Request(api, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read(80000).decode("utf-8", errors="replace"))
    urls = data[3] if isinstance(data, list) and len(data) > 3 and isinstance(data[3], list) else []
    return [u for u in urls if isinstance(u, str) and u.startswith("https://")]


def discover_source_urls(topic: str, limit: int = 8) -> list[str]:
    """Discover safe public source URLs for a topic.

    Uses deterministic high-value seed sources for known topics first, then
    best-effort DuckDuckGo and Wikipedia discovery. This makes Nova's research
    path useful even when a generic search endpoint blocks or rate-limits.
    """
    topic = (topic or "").strip()
    urls: list[str] = []
    def extend(items: list[str]) -> None:
        for item in items:
            if item and item not in urls and len(urls) < limit:
                urls.append(item)
    extend(_seed_source_urls(topic, limit=limit))
    if len(urls) < limit:
        try:
            extend(_duckduckgo_search(topic, limit=limit))
        except Exception:
            LOGGER.debug("DuckDuckGo discovery failed for research topic %r", topic, exc_info=True)
    if len(urls) < limit:
        try:
            extend(_wikipedia_opensearch(topic, limit=limit-len(urls)))
        except Exception:
            LOGGER.debug("Wikipedia OpenSearch discovery failed for research topic %r", topic, exc_info=True)
    return urls[:limit]


def _keywords(text: str, max_terms: int = 20) -> list[str]:
    stop = set("the and for with that this from have are was were has into about after before between using use can will should could would there their than then also more most when where what which while because these those your you they them its it's our not but out all any how why who".split())
    counts: dict[str, int] = {}
    for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", text.lower()):
        if w not in stop:
            counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:max_terms]]


def _extract_claims(text: str, topic: str, limit: int = 10) -> list[str]:
    topic_terms = [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", topic)[:8]]
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
    scored: list[tuple[int, str]] = []
    for s in sentences:
        ss = s.strip()
        if len(ss) < 50 or len(ss) > 320:
            continue
        low = ss.lower()
        score = sum(1 for t in topic_terms if t in low)
        score += 1 if re.search(r"\b\d+(?:\.\d+)?%?\b", ss) else 0
        score += 1 if any(w in low for w in ["because", "therefore", "however", "evidence", "data", "study", "report", "found"]) else 0
        if score:
            scored.append((score, ss))
    seen: set[str] = set()
    out: list[str] = []
    for _, s in sorted(scored, key=lambda x: -x[0]):
        key = s[:90].lower()
        if key not in seen:
            out.append(s)
            seen.add(key)
        if len(out) >= limit:
            break
    return out



def _source_score(source_type: str, bias_risk: str, text: str) -> int:
    score = 55
    if source_type in {"government/statistical", "academic/research", "technical documentation/repository"}:
        score += 18
    elif source_type == "news/journalism":
        score += 8
    elif source_type == "tertiary/encyclopedia":
        score += 4
    elif source_type in {"commentary/social/blog", "general web"}:
        score -= 10
    if "high" in bias_risk:
        score -= 18
    elif "low" in bias_risk:
        score += 8
    if any(w in text.lower() for w in ["method", "data", "references", "limitations", "confidence", "sample"]):
        score += 8
    if len(text) < 700:
        score -= 8
    return max(0, min(100, score))


def _claim_index(sources: list[ResearchSource], topic: str) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    seen: set[str] = set()
    for src in sources:
        for claim in _extract_claims(src.text, topic, limit=5):
            key = re.sub(r"\W+", " ", claim.lower()).strip()[:120]
            if key in seen:
                continue
            seen.add(key)
            index.append({
                "claim": claim,
                "source_title": src.title,
                "domain": src.domain,
                "source_type": src.source_type,
                "bias_risk": src.bias_risk,
                "url": src.url,
            })
            if len(index) >= 24:
                return index
    return index


def _consensus_and_gaps(payload: dict[str, Any]) -> dict[str, Any]:
    sources = payload.get("sources") or []
    source_mix = payload.get("source_mix") or {}
    risks = payload.get("bias_summary") or {}
    notes: list[str] = []
    gaps: list[str] = []
    if not sources:
        return {"consensus_notes": ["No source consensus can be assessed until sources are gathered."], "evidence_gaps": ["Add source URLs or enable internet discovery."]}
    if source_mix.get("government/statistical") or source_mix.get("academic/research"):
        notes.append("At least one primary, technical, government or academic-style source is present, improving evidential grounding.")
    else:
        gaps.append("No obvious primary/government/academic source was gathered; verify with stronger sources before acting.")
    if risks.get("high") or risks.get("medium-to-high"):
        gaps.append("Some sources show higher bias/commercial/commentary risk; compare claims against neutral sources.")
    if len(source_mix) <= 1 and len(sources) > 1:
        gaps.append("Source diversity is limited; add different source types to reduce blind spots.")
    if len(sources) < 3:
        gaps.append("Fewer than three sources were gathered; conclusions should be treated as preliminary.")
    if not notes:
        notes.append("The gathered material is enough for a map of claims, but not enough for final truth claims.")
    return {"consensus_notes": notes, "evidence_gaps": gaps}

def build_research_report(config: AssistantConfig, topic: str, source_urls: list[str] | None = None, max_sources: int = 8) -> tuple[Path, Path, dict[str, Any]]:
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Research topic is required.")
    allow_internet = bool(getattr(config, "allow_internet", False))
    raw_urls = [u.strip() for u in (source_urls or []) if u.strip()]
    search_error = ""
    rejected_sources: list[dict[str, str]] = []
    if allow_internet and not raw_urls:
        try:
            raw_urls = discover_source_urls(topic, limit=max_sources)
        except Exception as exc:
            search_error = repr(exc)
    urls, rejected_sources = _normalise_source_urls(raw_urls, max_sources=max_sources)
    sources: list[ResearchSource] = []
    fetch_errors: list[dict[str, str]] = list(rejected_sources)
    for url in urls:
        try:
            title, text = _fetch_url(url)
            dom = _domain(url)
            stype = _classify_source(dom, url, title)
            risk, bias, cred = _bias_and_credibility(dom, text, stype)
            sources.append(ResearchSource(title=title, url=url, domain=dom, text=text, source_type=stype, bias_risk=risk, bias_notes=bias, credibility_notes=cred))
        except Exception as exc:
            fetch_errors.append({"url": url, "error": repr(exc)})
    combined = "\n\n".join(s.text for s in sources)
    payload: dict[str, Any] = {
        "topic": topic,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "internet_allowed": allow_internet,
        "search_error": search_error,
        "requested_source_count": len(raw_urls),
        "accepted_source_count": len(urls),
        "rejected_sources": rejected_sources,
        "sources": [{k: v for k, v in asdict(s).items() if k != "text"} | {"excerpt": s.text[:1200]} for s in sources],
        "fetch_errors": fetch_errors,
        "keywords": _keywords(combined),
        "key_claims": _extract_claims(combined, topic, limit=12),
        "claim_index": _claim_index(sources, topic),
        "source_scores": [],
        "source_mix": {},
        "bias_summary": {},
    }
    for s in sources:
        payload["source_mix"][s.source_type] = payload["source_mix"].get(s.source_type, 0) + 1
        payload["bias_summary"][s.bias_risk] = payload["bias_summary"].get(s.bias_risk, 0) + 1
        payload["source_scores"].append({
            "domain": s.domain,
            "title": s.title,
            "score": _source_score(s.source_type, s.bias_risk, s.text),
            "source_type": s.source_type,
            "bias_risk": s.bias_risk,
            "url": s.url,
        })
    payload.update(_consensus_and_gaps(payload))
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", topic)[:64].strip("_") or "research"
    md_path = unique_path(RESEARCH_DIR, f"research_{safe}", ".md")
    json_path = md_path.with_suffix(".json")
    atomic_write_json(json_path, payload, ensure_ascii=False)
    atomic_write_text(md_path, render_research_markdown(payload))
    return md_path, json_path, payload


def render_research_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Research report: {payload.get('topic','')}",
        "",
        f"Created: `{payload.get('created_at','')}`",
        f"Internet allowed: `{payload.get('internet_allowed')}`",
        "",
        "## Meaning / initial interpretation",
        "",
    ]
    if not payload.get("sources"):
        lines += [
            "No sources were gathered. Enable internet with `/allow-internet on`, provide URLs using `/research TOPIC => URL1 URL2`, or attach files/context first.",
            "",
        ]
    else:
        mix = payload.get("source_mix", {})
        risks = payload.get("bias_summary", {})
        lines += [
            f"Gathered **{len(payload.get('sources', []))}** sources. Source mix: `{mix}`. Bias-risk mix: `{risks}`.",
            "The strongest conclusions should come from repeated claims across independent, primary or specialist sources, not from a single high-confidence-looking page.",
            "",
        ]
    lines += ["## Short synthesis", ""]
    claims = payload.get("key_claims", [])[:4]
    scores = sorted(payload.get("source_scores", []), key=lambda x: x.get("score", 0), reverse=True)
    if claims:
        lines.append("This topic appears to involve these main points from the gathered material:")
        for claim in claims:
            lines.append(f"- {claim}")
        if scores:
            lines.append(f"\nBest available source in this run: `{scores[0].get('domain')}` ({scores[0].get('score')}/100). Treat lower-scored commercial/general sources as leads, not proof.")
    else:
        lines.append("The gathered text did not yield strong extractive claims; add stronger URLs or rerun with a narrower topic.")
    lines += ["", "## Consensus, gaps and meaning", ""]
    for c in payload.get("consensus_notes", []):
        lines.append(f"- {c}")
    for g in payload.get("evidence_gaps", []):
        lines.append(f"- **Gap / caution:** {g}")
    if not payload.get("consensus_notes") and not payload.get("evidence_gaps"):
        lines.append("- No consensus/gap assessment available.")
    lines += ["", "## Key claims to verify", ""]
    for claim in payload.get("key_claims", [])[:12]:
        lines.append(f"- {claim}")
    if not payload.get("key_claims"):
        lines.append("- No strong extractive claims found from the gathered text.")
    lines += ["", "## Claim/source map", ""]
    for item in payload.get("claim_index", [])[:16]:
        lines.append(f"- {item.get('claim')}")
        lines.append(f"  - Source: `{item.get('domain')}` ({item.get('source_type')}; bias risk: {item.get('bias_risk')})")
    if not payload.get("claim_index"):
        lines.append("- No claim/source pairs available yet.")
    lines += ["", "## Source scores", ""]
    for item in sorted(payload.get("source_scores", []), key=lambda x: x.get("score", 0), reverse=True):
        lines.append(f"- **{item.get('score')}/100** `{item.get('domain')}` — {item.get('source_type')} — bias risk: {item.get('bias_risk')}")
    if not payload.get("source_scores"):
        lines.append("- No scored sources available yet.")
    lines += ["", "## Keywords / concepts", "", ", ".join(payload.get("keywords", [])[:20]) or "No keywords extracted.", "", "## Source and bias analysis", ""]
    for i, src in enumerate(payload.get("sources", []), 1):
        lines += [
            f"### {i}. {src.get('title') or src.get('domain')}",
            "",
            f"- URL: `{src.get('url')}`",
            f"- Domain: `{src.get('domain')}`",
            f"- Type: **{src.get('source_type')}**",
            f"- Bias risk: **{src.get('bias_risk')}**",
            f"- Bias notes: {'; '.join(src.get('bias_notes') or ['No obvious bias markers detected.'])}",
            f"- Credibility notes: {'; '.join(src.get('credibility_notes') or [])}",
            "",
            "Excerpt:",
            "",
            src.get("excerpt", "")[:900].replace("\n", " "),
            "",
        ]
    if payload.get("fetch_errors"):
        lines += ["## Fetch errors", ""]
        for err in payload.get("fetch_errors", []):
            lines.append(f"- `{err.get('url')}` — {err.get('error')}")
        lines.append("")
    lines += [
        "## How to use this report",
        "",
        "- Treat it as a research map, not final truth.",
        "- Prefer claims repeated across independent primary/specialist sources.",
        "- Flag commercial, political, advocacy, or social-media sources as perspective-bearing rather than neutral.",
        "- Use the source mix to identify missing perspectives before making decisions.",
    ]
    return "\n".join(lines)
