"""Claude API — extract structured logistics data from raw Telegram messages."""
import logging
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Tool schema for structured extraction
EXTRACT_TOOL = {
    "name": "extract_logistics_report",
    "description": "Logistika hisobotidan ma'lumot ajratib olish",
    "input_schema": {
        "type": "object",
        "properties": {
            "sana": {
                "type": "string",
                "description": "Sana (YYYY-MM-DD formatida)"
            },
            "reys_id": {
                "type": "string",
                "description": "Buyurtma/Reys ID"
            },
            "jonatish_nuqtasi": {
                "type": "string",
                "description": "Jo'natish nuqtasi (shahar/joy)"
            },
            "yetkazish_nuqtasi": {
                "type": "string",
                "description": "Yetkazish nuqtasi (shahar/joy)"
            },
            "mijoz": {
                "type": "string",
                "description": "Mijoz nomi — bu shartnoma raqami (100X kabi), yuk nomi emas"
            },
            "shartnoma_raqami": {
                "type": "string",
                "description": "Shartnoma raqami (TTN raqami)"
            },
            "yuk": {
                "type": "string",
                "description": "Yuk nomi (masalan CocaCola)"
            },
            "transport_turi": {
                "type": "string",
                "description": "Transport turi — faqat: TENT, Ref, Bortli, Samosval, Tirkamali tortqich yoki boshqa aniq tur"
            },
            "tv_davlat_raqami": {
                "type": "string",
                "description": "Transport vositasi davlat raqami (masalan: 40 126 RCA)"
            },
            "haydovchi": {
                "type": "string",
                "description": "Haydovchi to'liq ismi (Haydovchi: so'zidan keyin keladi)"
            },
            "naqd_tushum": {
                "type": "number",
                "description": "Naqd pul miqdori (Naqd: qiymatidan)"
            },
            "naqdsiz_tushum": {
                "type": "number",
                "description": "Karta + Pul o'tkazma miqdori yig'indisi"
            },
            "jami_tushum": {
                "type": "number",
                "description": "Jami tushum (naqd + naqdsiz)"
            },
        },
        "required": ["reys_id", "haydovchi", "tv_davlat_raqami"],
    },
}

SYSTEM_PROMPT = """Siz logistika kompaniyasi uchun ma'lumot ajratuvchi yordamchisiz.
Sizga Telegram xabari beriladi. Xabardan kerakli ma'lumotlarni aniq ajratib oling.

Muhim qoidalar:
- tv_davlat_raqami: "Mashina Raqami:" yoki FAW/KAMAZ belgisidan keyin keluvchi raqam (masalan: 40 126 RCA)
- transport_turi: TENT, Ref, Bortli, Samosval, Tirkamali tortqich — faqat shu turlardan birini tanlang
- mijoz: shartnoma raqami (100X, SH-001 kabi) — yuk nomi emas
- yuk: tovar nomi (CocaCola, bug'doy va h.k.)
- jonatish va yetkazish: "Bektemir - Marg'ilon" formatidan ajrating
- naqdsiz_tushum: Karta + Pul o'tkazma qiymatlarini qo'shing
- jami_tushum: naqd + naqdsiz yig'indisi
"""


async def extract_report(message_text: str) -> dict | None:
    """Extract structured logistics data from raw message text using Claude API."""
    client = anthropic.AsyncAnthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_logistics_report"},
            messages=[
                {
                    "role": "user",
                    "content": f"Quyidagi xabardan ma'lumot ajrating:\n\n{message_text}",
                }
            ],
        )

        # Extract tool result — no JSON parsing needed
        tool_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if not tool_block:
            logger.warning("Claude did not return a tool_use block")
            return None

        return tool_block.input

    except Exception as e:
        logger.error("Claude API error: %s", e)
        return None
