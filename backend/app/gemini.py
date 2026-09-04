"""Server-side AI summary generation for the "Análisis IA" panel, via Gemini
2.5 Flash. Per the design handoff, this text MUST be generated on the server
from the model's already-computed output — Gemini only writes the natural
language; it never computes risk, FAI, or any number itself.

If GEMINI_API_KEY is missing or the call fails for any reason (network,
quota, malformed response), callers fall back to a deterministic template so
/forecast never breaks because of an external AI service.
"""

import httpx

from .config import GEMINI_API_KEY

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
TIMEOUT_SECONDS = 8.0


def _prompt(ctx: dict) -> str:
    return (
        "Eres el redactor del panel 'Análisis IA' de AlgaeWatch Villarrica, un sistema de "
        "monitoreo de floraciones de algas en el Lago Villarrica, Chile. Con los siguientes "
        "datos YA CALCULADOS por el modelo predictivo (Gradient Boosting), redacta EXACTAMENTE "
        "dos párrafos en español de Chile, sin markdown, sin títulos:\n"
        "1) Un resumen técnico breve (3-4 frases) del riesgo proyectado a 7 días para la "
        "estación con mayor riesgo, mencionando el valor de riesgo, la variación vs. la semana "
        "anterior, temperatura superficial, viento medio y el índice FAI con su pH.\n"
        "2) Una recomendación operativa breve (1-2 frases) que empiece con 'Recomendación:'.\n\n"
        "NO inventes números: usa únicamente los valores de este contexto.\n\n"
        f"Estación de mayor riesgo: {ctx['top_station_name']}\n"
        f"Riesgo a 7 días: {ctx['top_risk']}/100 ({ctx['top_level']})\n"
        f"Variación vs. semana anterior: {ctx['delta']:+d}\n"
        f"Temperatura superficial: {ctx['water_temp_c']} °C\n"
        f"Viento medio: {ctx['wind_kmh']} km/h\n"
        f"Índice FAI (Sentinel-2): {ctx['fai']}\n"
        f"pH: {ctx['ph']}\n"
        f"Segunda estación con más riesgo: {ctx['second_station_name']}\n"
        f"Riesgo medio del lago a 7 días: {ctx['lake_mean_risk_7d']}/100\n"
        f"Estaciones en alerta: {ctx['stations_in_alert']}/4\n"
    )


async def generate_ai_summary(ctx: dict) -> dict | None:
    """Returns {"summary": str, "recommendation": str} from Gemini, or None on
    any failure (missing key, network error, empty/malformed response) so the
    caller can fall back to the template.
    """
    if not GEMINI_API_KEY:
        return None

    body = {
        "contents": [{"parts": [{"text": _prompt(ctx)}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 500,
            # gemini-2.5-flash spends output-token budget on internal "thinking" by
            # default, which can exhaust maxOutputTokens before any text is written
            # (finishReason: MAX_TOKENS with an empty/truncated response). This task
            # needs plain text generation from already-computed numbers, not
            # reasoning, so thinking is disabled.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            res = await client.post(GEMINI_URL, params={"key": GEMINI_API_KEY}, json=body)
        res.raise_for_status()
        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if len(paragraphs) < 2:
        return None

    summary = paragraphs[0]
    recommendation = paragraphs[1]
    if not recommendation.lower().startswith("recomendación"):
        recommendation = f"Recomendación: {recommendation}"

    return {"summary": summary, "recommendation": recommendation}
