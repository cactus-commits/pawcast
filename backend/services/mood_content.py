"""
Mood Content 

All diagnostic mood texts and weather scoring criteria.
Import MOOD_CONTENT in walks.py to look up content by mood_name.
"""

MOOD_CONTENT: dict = {

    # ── DIAGNOSTIC MOODS ────────────────────────────────────────────────────

    "low_battery": {
        "title": "Low Battery Human",
        "category": "diagnostic",
        "diagnosis": (
            "Acute Vitamin D Deficiency & Circadian Dysregulation.\n\n"
            "Prolonged rotting leads to \"The Fog.\" If {human} isn't manually "
            "dragged into the light, they may eventually become one with the mattress. "
            "Following this protocol is the only way to restart their serotonin production."
        ),
        "prescription": (
            "To properly reboot the system, we need direct sunlight and maximum UV exposure. "
            "The optimal window for our 20–30 minute \"Low-Impact Sun-Soak\" is below. "
            "Sticking to flat pavement — their legs are currently made of jelly."
        ),
        "experts_recommend": (
            "At least 5 minutes of standing perfectly still in a sun-patch. "
            "End the walk at an outdoor coffee shop for a \"liquid battery\" "
            "(caffeine) for them and a pup cup for you."
        ),
    },

    "posture_emergency": {
        "title": "Posture Emergency",
        "category": "diagnostic",
        "diagnosis": (
            "Advanced Kyphosis (aka \"The Shrimp Effect\").\n\n"
            "{human}'s vertebrae are currently screaming in a language only dogs can hear. "
            "If they continue to fold, they will eventually lose the ability to reach "
            "the high shelf where the treats are kept."
        ),
        "prescription": (
            "We need clear visibility and a crisp atmosphere to encourage upright movement. "
            "Initiating 45 minutes of Structural Realignment Therapy. "
            "Seek out \"High-Resistance Terrain\" (hills or stairs) to force them to look up."
        ),
        "experts_recommend": (
            "Find a sturdy tree or a fence. Pretend to sniff something very high up "
            "so they have to stretch their neck to see what you're looking at."
        ),
    },

    "doomscroll_detox": {
        "title": "Doomscroll Detox",
        "category": "diagnostic",
        "diagnosis": (
            "Vertical-Swipe Psychosis & Dopamine Fried-Circuitry.\n\n"
            "Excessive consumption of \"POV\" videos has caused {human}'s brain to turn "
            "into digital sludge. They have forgotten that the world exists in 3D. "
            "This intervention is mandatory for their sanity."
        ),
        "prescription": (
            "The goal is a high-sensory environment that makes screens impossible to read. "
            "The best time for our 40-minute \"Analog Sensory Overload\" is below. "
            "Heading to a \"Distraction Zone\" (the park or a busy street) "
            "to drown out the digital noise."
        ),
        "experts_recommend": (
            "Touching grass. Specifically, find some damp lawn and walk across it. "
            "Force them to navigate uneven ground so they have to put the phone "
            "in their pocket or risk a \"Major L.\""
        ),
    },

    "long_term_health": {
        "title": "Long Term Health Investment",
        "category": "diagnostic",
        "diagnosis": (
            "Sedentary Lifestyle Syndrome.\n\n"
            "{human} is acting like they have nine lives. They do not. "
            "To ensure maximum \"Fetch Years,\" we must initiate "
            "preventative maintenance immediately."
        ),
        "prescription": (
            "We require moderate temperatures and stable conditions to maintain "
            "a consistent heart rate. Our 60-minute \"Longevity Loop\" is scheduled below. "
            "Soft trails or forest paths are best to save their aging human joints."
        ),
        "experts_recommend": (
            "A tactical hydration break. Stop at a water fountain or a stream. "
            "Show them how refreshing it is to just drink water and exist in nature "
            "without a \"deliverable.\""
        ),
    },

    "burnout_recovery": {
        "title": "Burnout Recovery Protocol",
        "category": "diagnostic",
        "diagnosis": (
            "Cognitive Overload & System Glitch.\n\n"
            "{human}'s brain has too many tabs open and the cooling fan is broken. "
            "They are currently a \"Glass Battery\" — one more email "
            "and they might actually shatter."
        ),
        "prescription": (
            "We need low-stimulation, dim lighting, and minimal noise to clear the cache. "
            "Our 50-minute \"Silent-Mode Decompression\" is best performed below "
            "in a \"Zero-Noise\" environment like a botanical garden or quiet suburb."
        ),
        "experts_recommend": (
            "Finding a bench and sitting on their feet for 10 minutes. "
            "This provides \"Deep Pressure Therapy\" and forces them to stare at a tree "
            "instead of thinking about their \"Inbox Zero\" goal."
        ),
    },

    "hygiene_intervention": {
        "title": "Natural Hygiene Intervention",
        "category": "diagnostic",
        "diagnosis": (
            "Gamer-Musk Saturation & Olfactory Offense.\n\n"
            "The scent profile of {human} has moved from \"Owner\" to \"Locker Room.\" "
            "This is an affront to your 300 million scent receptors. "
            "Atmospheric rinsing is now the only option."
        ),
        "prescription": (
            "We are waiting for high humidity or actual precipitation to facilitate "
            "a \"Nature's Power-Wash.\" The optimal rinse-cycle window is below. "
            "We're doing 15–20 minutes in an open field for maximum coverage."
        ),
        "experts_recommend": (
            "Performing a \"Big Shake\" right next to their legs upon return. "
            "They need to understand that being wet is a shared experience. "
            "Suggest a warm shower for them immediately after."
        ),
    },

    "character_development": {
        "title": "Character Development Arc",
        "category": "diagnostic",
        "diagnosis": (
            "Chronic Comfort-Zone Sequestration.\n\n"
            "{human} has become \"soft.\" They are afraid of a light breeze "
            "and a little dampness. Without regular exposure to minor inconvenience, "
            "they will lose their \"Main Character\" energy."
        ),
        "prescription": (
            "We are looking for the most \"challenging\" weather window of the day "
            "to build some actual grit. We are heading out for 30 minutes of "
            "\"Adversity Training\" below. Choose the windiest route possible "
            "and go through the mud, not around it."
        ),
        "experts_recommend": (
            "No shortcuts. Even if they sigh or pull their hood up, you must stop "
            "to sniff every single vertical surface. "
            "They need to learn patience through suffering."
        )
    }
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def format_texts(mood_name: str, human_name: str, relationship: str) -> dict:
    """
    Return diagnosis, prescription and experts_recommend
    with {human} placeholder replaced by the real human name + relationship.
    """
    mood = MOOD_CONTENT[mood_name]
    human_str = f"{human_name} (your {relationship})"
    return {
        "diagnosis": mood["diagnosis"].replace("{human}", human_str),
        "prescription": mood["prescription"],
        "experts_recommend": mood["experts_recommend"],
    }