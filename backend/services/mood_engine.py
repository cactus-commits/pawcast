"""
Mood Engine 

Picks the best walk window of the day.
Each mood defines a scoring function that rates every available hourly
weather slot. We always pick the HIGHEST scoring hour.

Weather logic:
All scoring is relative to today's forecast range, not absolute values.
This means the engine works correctly in any climate:
- Stockholm in February (-12°C to -6°C): "warmest" = -6°C, still valid
- Barcelona in August (28°C to 36°C): "coolest" = 28°C, still valid
- The engine never says "no suitable window" just because it's cold

Absolute thresholds are only used for hard safety limits (e.g. never
recommend going out in a hurricane regardless of mood).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from backend.services.mood_content import format_texts
from backend.services.weather_service import HourlyWeather, SunTimes


# ── Types ────────────────────────────────────────────────────────────────────

@dataclass
class ScoredWindow:
    hour: HourlyWeather
    score: float


# ── Safety limits (absolute — climate-independent) ───────────────────────────
# These are the only hard absolute thresholds in the engine.
# Everything else is relative to today's range.

UNSAFE_WIND_MS = 18        # gale force — unsafe regardless of mood
UNSAFE_RAIN_PCT = 95       # essentially a storm
UNSAFE_TEMP_MIN = -30      # extreme cold — safety limit


def _is_safe(h: HourlyWeather) -> bool:
    """Return False if conditions are dangerous regardless of mood."""
    return (
        h.wind_speed < UNSAFE_WIND_MS
        and h.rain_prob < UNSAFE_RAIN_PCT
        and h.temp > UNSAFE_TEMP_MIN
    )


# ── Relative-range helpers ───────────────────────────────────────────────────

def _temp_range(hours: list[HourlyWeather]) -> tuple[float, float]:
    temps = [h.temp for h in hours]
    return min(temps), max(temps)


def _wind_range(hours: list[HourlyWeather]) -> tuple[float, float]:
    winds = [h.wind_speed for h in hours]
    return min(winds), max(winds)


def _rain_range(hours: list[HourlyWeather]) -> tuple[float, float]:
    rains = [h.rain_prob for h in hours]
    return min(rains), max(rains)


def _relative_position(val: float, lo: float, hi: float) -> float:
    """Return 0.0–1.0 where val sits in [lo, hi].
    0.0 = coldest/calmest/driest end, 1.0 = warmest/windiest/wettest end.
    Returns 0.5 if range is flat (all hours identical).
    """
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (val - lo) / (hi - lo)))


def _is_daylight(hour: HourlyWeather, sun: SunTimes) -> bool:
    t = hour.dt.replace(tzinfo=sun.sunrise.tzinfo)
    return sun.sunrise <= t <= sun.sunset


# ── Cold/heat commentary injected into sarcastic responses ──────────────────

def _condition_commentary(temp: float, wind: float, rain: float) -> str:
    """Return a short sarcastic weather note for very extreme conditions."""
    if temp < -10:
        return f"It is {temp:.0f}°C outside. Paw-freezing territory. Frozen ground protocol engaged. "
    if temp < 0:
        return f"Below zero at {temp:.0f}°C. Bundle them up and go anyway. "
    if wind > 12:
        return f"Wind at {wind:.0f} m/s. Hold onto your human. "
    if rain > 80:
        return "Heavy rain incoming. Nature's power-wash activated. "
    return ""


# ── Diagnostic mood scorers (higher score = better window) ──────────────────
#
# All use relative position within today's forecast range.
# Score range: 0–100.

def _score_low_battery_human(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Low Battery Human — maximize sunlight, warmest part of day, low wind, no rain.
    Relative: picks the warmest, brightest, calmest window available today.
    Works at -12°C — the warmest hour of a cold day is still the right call.
    """
    if not _is_daylight(h, sun):
        return 0.0  # must be daylight — sunlight is the whole point

    score = 100.0

    # Prefer warmest relative to today's range
    temp_pos = _relative_position(h.temp, tlo, thi)
    score += temp_pos * 25  # warmest hour gets +25

    # Penalize rain — rain blocks UV and ruins the vibe
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score -= rain_pos * 35

    # Penalize wind — gentle walk required
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    score -= wind_pos * 20

    # Bonus for low cloud cover (more sun)
    if h.cloud_cover < 30:
        score += 15
    elif h.cloud_cover > 80:
        score -= 15

    return max(0.0, score)


def _score_posture_emergency(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Posture Emergency — clear visibility, crisp air, no rain, daylight only.
    Relative: prefers the driest, calmest, most comfortable window.
    """
    if not _is_daylight(h, sun):
        return 0.0

    score = 100.0

    # Prefer middle-to-warm of today's range (comfortable, not extreme)
    temp_pos = _relative_position(h.temp, tlo, thi)
    score -= abs(temp_pos - 0.6) * 30  # sweet spot at 60th percentile

    # Rain is bad — spine rehabilitation requires dignity
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score -= rain_pos * 40

    # Moderate wind is fine, strong wind is not
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    score -= wind_pos * 20

    return max(0.0, score)


def _score_doomscroll_detox(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Doomscroll Detox — calm, sensory-rich, daylight preferred.
    Not too hot, not too cold. The goal is screens being unreadable outside.
    """
    score = 100.0

    if not _is_daylight(h, sun):
        score -= 25

    # Avoid extremes of temperature — middle of today's range is ideal
    temp_pos = _relative_position(h.temp, tlo, thi)
    score -= abs(temp_pos - 0.5) * 25

    # Light rain is ok (adds sensory interest), heavy rain kills phone use anyway
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    if rain_pos > 0.7:
        score -= (rain_pos - 0.7) * 40  # only penalize heavy rain

    # Calm wind helps
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    score -= wind_pos * 20

    return max(0.0, score)


def _score_burnout_recovery(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Burnout Recovery — low stimulation, soft light, gentle breeze, no extremes.
    Overcast is actually preferred — harsh sun overstimulates a fried brain.
    """
    score = 100.0

    # Daylight preferred but not required — dusk is fine for decompression
    if not _is_daylight(h, sun):
        score -= 20

    # Prefer cooler end of today's range — fresh air resets the nervous system
    temp_pos = _relative_position(h.temp, tlo, thi)
    score -= abs(temp_pos - 0.35) * 25  # cooler side of range

    # Very low wind feels dead; very high wind is stressful
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    if wind_pos < 0.1:
        score -= 10  # too still
    elif wind_pos > 0.7:
        score -= 25  # too wild

    # No heavy rain
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score -= rain_pos * 25

    # Partial cloud is soothing — not harsh sun, not oppressive gloom
    if 30 <= h.cloud_cover <= 75:
        score += 12

    return max(0.0, min(110.0, score))


def _score_long_term_health(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Long Term Health Investment — stable, moderate, sustainable.
    Moderate relative temperature, low wind, low rain, manageable UV.
    """
    score = 100.0

    # Prefer middle of today's range — consistency over extremes
    temp_pos = _relative_position(h.temp, tlo, thi)
    score -= abs(temp_pos - 0.45) * 30

    # Light wind is fine, strong wind makes sustained walking harder
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    score -= wind_pos * 20

    # Prefer dry
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score -= rain_pos * 30

    # Penalize extreme UV (absolute threshold — UV above 7 is genuinely harmful)
    if h.uv_index > 7:
        score -= 20

    return max(0.0, score)


def _score_hygiene_intervention(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Natural Hygiene Intervention — needs rain or high humidity.
    Relative: picks the wettest window of the day, whatever that looks like.
    Works in summer rain or Swedish drizzle — wettest available is the answer.
    """
    score = 0.0

    # Maximize rain — this is the whole point
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score += rain_pos * 60

    # High cloud cover suggests humidity even without direct rain
    cloud_bonus = _relative_position(h.cloud_cover, 0, 100)
    score += cloud_bonus * 20

    # Mild wind helps distribute the moisture evenly
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    if 0.2 < wind_pos < 0.6:
        score += 10

    # Safety: don't go out in a storm even for hygiene reasons
    if not _is_safe(h):
        return 0.0

    return max(0.0, min(100.0, score))


def _score_character_development(
    h: HourlyWeather,
    sun: SunTimes,
    tlo: float, thi: float,
    wlo: float, whi: float,
    rlo: float, rhi: float,
) -> float:
    """
    Character Development Arc — most challenging but safe window.
    Relative: picks the windiest, coldest, least comfortable hour available.
    In -12°C Stockholm this still picks the worst of a bad day — as intended.
    """
    score = 0.0

    # Want windiest relative to today
    wind_pos = _relative_position(h.wind_speed, wlo, whi)
    score += wind_pos * 35

    # Want coldest relative to today
    temp_pos = _relative_position(h.temp, tlo, thi)
    score += (1 - temp_pos) * 30  # colder = higher score

    # Some rain adds to the challenge
    rain_pos = _relative_position(h.rain_prob, rlo, rhi)
    score += rain_pos * 25

    # Overcast is bleaker — adds to the atmosphere
    cloud_pos = _relative_position(h.cloud_cover, 0, 100)
    score += cloud_pos * 10

    # Safety hard limit
    if not _is_safe(h):
        return 0.0

    return max(0.0, min(100.0, score))



# ── Mood registry ────────────────────────────────────────────────────────────
# Keys match mood_content.py exactly (snake_case)

DIAGNOSTIC_MOODS: dict[str, callable] = {
    "low_battery": _score_low_battery_human,
    "posture_emergency": _score_posture_emergency,
    "doomscroll_detox": _score_doomscroll_detox,
    "burnout_recovery": _score_burnout_recovery,
    "long_term_health": _score_long_term_health,
    "hygiene_intervention": _score_hygiene_intervention,
    "character_development": _score_character_development,
}


# ── Fallback messages ────────────────────────────────────────────────────────
# Used when no hour scores above the minimum threshold.
# This should be rare with relative scoring — but kept as a safety net.

_DIAGNOSTIC_FALLBACKS = [
    "Checked the forecast. Nature is being uncooperative. Try again tomorrow or lower your standards.",
    "Weather is mid. No optimal window detected. Your human will just have to suffer inside.",
    "Nothing meets the criteria. The sky is giving nothing. Literally.",
    "Forecast reviewed. Conditions are aggressively average. Walk at your own risk.",
]


# ── Main engine ──────────────────────────────────────────────────────────────

def pick_walk_window(
    mood_name: str,
    hours: list[HourlyWeather],
    sun: SunTimes,
    dog_name: str,
    human_name: str,
    relationship: str,
) -> dict:
    """Pick the best walk window for the given mood and return a response dict.

    Uses relative scoring across today's forecast range — works in any climate.
    """
    scorers = DIAGNOSTIC_MOODS
    fallbacks = _DIAGNOSTIC_FALLBACKS

    scorer = scorers.get(mood_name)
    if scorer is None:
        raise ValueError(
            f"Unknown mood {mood_name!r}. "
            f"Valid moods: {', '.join(scorers.keys())}"
        )

    # Pre-compute today's full ranges once — used by all scorers
    tlo, thi = _temp_range(hours)
    wlo, whi = _wind_range(hours)
    rlo, rhi = _rain_range(hours)

    # Score every safe hour
    scored: list[ScoredWindow] = []
    for h in hours:
        if not _is_safe(h):
            continue
        s = scorer(h, sun, tlo, thi, wlo, whi, rlo, rhi)
        scored.append(ScoredWindow(hour=h, score=s))

    if not scored:
        # All hours were unsafe — extremely rare
        return _fallback_response(mood_name, dog_name, human_name, relationship, fallbacks)

    # Pick highest scoring hour
    scored.sort(key=lambda sw: sw.score, reverse=True)
    best = scored[0]

    # If even the best score is very low, use a fallback
    # Threshold is low (10) because relative scoring always produces some spread
    if best.score < 10:
        return _fallback_response(mood_name, dog_name, human_name, relationship, fallbacks)

    h = best.hour
    time_str = f"{h.dt.strftime('%H:%M')}–{h.dt.strftime('%H')}:59"
    cold_note = _condition_commentary(h.temp, h.wind_speed, h.rain_prob)

    # Pull texts from mood_content.py
    texts = format_texts(mood_name, human_name, relationship)

    return {
        "mood": mood_name,
        "recommended_time": time_str,
        "diagnosis": cold_note + texts["diagnosis"],
        "prescription": texts["prescription"],
        "experts_recommend": texts["experts_recommend"],
        "weather": {
            "temp": round(h.temp, 1),
            "wind": round(h.wind_speed, 1),
            "rain_probability": round(h.rain_prob),
            "cloud_cover": round(h.cloud_cover),
            "uv_index": round(h.uv_index, 1),
        },
        "dog_name": dog_name,
        "human_name": human_name,
        "human_relationship": relationship,
    }


def _fallback_response(
    mood_name: str,
    dog_name: str,
    human_name: str,
    relationship: str,
    fallbacks: list[str],
) -> dict:
    """Return a sarcastic fallback when no suitable window is found."""
    return {
        "mood": mood_name,
        "recommended_time": "N/A",
        "diagnosis": random.choice(fallbacks),
        "prescription": "Try again tomorrow. Or just open a window and point at it.",
        "experts_recommend": "Hydration. Rest. Lower expectations.",
        "weather": {
            "temp": 0,
            "wind": 0,
            "rain_probability": 0,
            "cloud_cover": 0,
            "uv_index": 0,
        },
        "dog_name": dog_name,
        "human_name": human_name,
        "human_relationship": relationship,
    }