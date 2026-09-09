"""Telegram message handler — processes incoming logistics reports."""
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from services.ai import extract_report
from services.sheets import append_to_reyslar, get_malumotnoma_data
from services.validator import validate

logger = logging.getLogger(__name__)


def _success_message(extracted: dict) -> str:
    """Build success confirmation message in Uzbek."""
    naqd = extracted.get("naqd_tushum", 0) or 0
    naqdsiz = extracted.get("naqdsiz_tushum", 0) or 0
    jami = extracted.get("jami_tushum", naqd + naqdsiz) or (naqd + naqdsiz)

    jonatish = extracted.get("jonatish_nuqtasi", "—")
    yetkazish = extracted.get("yetkazish_nuqtasi", "—")

    return (
        f"✅ Reys muvaffaqiyatli kiritildi!\n\n"
        f"📋 Reys ID: {extracted.get('reys_id', '—')}\n"
        f"📅 Sana: {extracted.get('sana', '—')}\n"
        f"🚛 Haydovchi: {extracted.get('haydovchi', '—')}\n"
        f"📍 Yo'nalish: {jonatish} → {yetkazish}\n"
        f"📦 Yuk: {extracted.get('yuk', '—')}\n"
        f"💰 Jami tushum: {jami:,.0f} so'm"
    )


def _error_message_user(errors: list[str]) -> str:
    """Build error message for the user who sent the report."""
    error_lines = "\n".join(f"• {e}" for e in errors)
    return (
        f"❌ Ma'lumotlar mos kelmadi!\n\n"
        f"Sabab:\n{error_lines}\n\n"
        f"Iltimos, ma'lumotlarni tekshirib qayta yuboring."
    )


def _error_message_group(
    extracted: dict, errors: list[str], username: str, original_text: str
) -> str:
    """Build error notification for the error group."""
    error_lines = "\n".join(f"❌ {e}" for e in errors)
    return (
        f"⚠️ Mos kelmaydigan reys hisoboti!\n\n"
        f"📋 Reys ID: {extracted.get('reys_id', 'Aniqlanmadi')}\n"
        f"{error_lines}\n\n"
        f"👤 Yuboruvchi: @{username}\n"
        f"📝 Asl xabar:\n{original_text}"
    )


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main handler — called when user sends a text message to the bot."""
    message = update.message
    if not message or not message.text:
        return

    original_text = message.text
    username = message.from_user.username or message.from_user.first_name or "Noma'lum"
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "")
    error_group_id = os.environ.get("ERROR_GROUP_CHAT_ID", "")

    # Step 1 — notify user we are processing
    processing_msg = await message.reply_text("⏳ Ma'lumotlar tekshirilmoqda...")

    # Step 2 — extract structured data via Claude API
    extracted = await extract_report(original_text)
    if not extracted:
        await processing_msg.edit_text(
            "❌ Xabardan ma'lumot ajratib bo'lmadi. "
            "Iltimos, formatni tekshirib qayta yuboring."
        )
        return

    logger.info("Extracted data for reys_id=%s", extracted.get("reys_id"))

    # Step 3 — read Malumotnoma reference data
    try:
        reference = await get_malumotnoma_data(sheet_id)
    except Exception as e:
        logger.error("Failed to read Malumotnoma: %s", e)
        await processing_msg.edit_text(
            "❌ Google Sheets bilan ulanishda xatolik yuz berdi. "
            "Keyinroq urinib ko'ring."
        )
        return

    # Step 4 — validate against reference data
    is_valid, errors = validate(extracted, reference)

    if is_valid:
        # Step 5a — write to Reyslar sheet
        try:
            await append_to_reyslar(sheet_id, extracted)
        except Exception as e:
            logger.error("Failed to write to Reyslar: %s", e)
            await processing_msg.edit_text(
                "❌ Reyslar varag'iga yozishda xatolik yuz berdi. "
                "Keyinroq urinib ko'ring."
            )
            return

        await processing_msg.edit_text(_success_message(extracted))
        logger.info("Successfully wrote reys %s to Reyslar", extracted.get("reys_id"))

    else:
        # Step 5b — notify user and send to error group
        await processing_msg.edit_text(_error_message_user(errors))

        if error_group_id:
            try:
                await context.bot.send_message(
                    chat_id=int(error_group_id),
                    text=_error_message_group(extracted, errors, username, original_text),
                )
            except Exception as e:
                logger.error("Failed to send error to group: %s", e)

        logger.warning(
            "Validation failed for reys_id=%s: %s",
            extracted.get("reys_id"),
            errors,
        )
