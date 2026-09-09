"""Validate extracted logistics data against Malumotnoma reference data."""
import logging

logger = logging.getLogger(__name__)


def _partial_match(value: str, reference_list: list[str]) -> bool:
    """Case-insensitive partial match — 'TENT' matches 'Tent', '40 126 RCA' matches '40126RCA'."""
    if not value:
        return False
    value_clean = value.upper().replace(" ", "")
    for ref in reference_list:
        ref_clean = ref.upper().replace(" ", "")
        if value_clean in ref_clean or ref_clean in value_clean:
            return True
    return False


def validate(extracted: dict, reference: dict) -> tuple[bool, list[str]]:
    """Validate extracted data against Malumotnoma reference data.

    Returns:
        (is_valid, list_of_errors)
        is_valid = True only if all MANDATORY checks pass
        list_of_errors contains all failed checks (mandatory + optional warnings)
    """
    errors = []

    # --- MANDATORY checks ---
    tv = extracted.get("tv_davlat_raqami", "")
    if not _partial_match(tv, reference["tv_davlat_raqamlari"]):
        errors.append(f'TV raqami "{tv}" Malumotnomada topilmadi')

    haydovchi = extracted.get("haydovchi", "")
    if not _partial_match(haydovchi, reference["haydovchilar"]):
        errors.append(f'Haydovchi "{haydovchi}" Malumotnomada topilmadi')

    transport = extracted.get("transport_turi", "")
    if not _partial_match(transport, reference["transport_turlari"]):
        errors.append(f'Transport turi "{transport}" Malumotnomada topilmadi')

    # If any mandatory check failed, return invalid
    if errors:
        return False, errors

    # --- OPTIONAL warnings (don't block, just log) ---
    jonatish = extracted.get("jonatish_nuqtasi", "")
    yetkazish = extracted.get("yetkazish_nuqtasi", "")
    punktlar = reference["punktlar"]

    if jonatish and not _partial_match(jonatish, punktlar):
        logger.warning("Jo'natish nuqtasi '%s' Malumotnomada topilmadi (majburiy emas)", jonatish)

    if yetkazish and not _partial_match(yetkazish, punktlar):
        logger.warning("Yetkazish nuqtasi '%s' Malumotnomada topilmadi (majburiy emas)", yetkazish)

    mijoz = extracted.get("mijoz", "")
    if mijoz and not _partial_match(mijoz, reference["mijozlar"]):
        logger.warning("Mijoz '%s' Malumotnomada topilmadi (majburiy emas)", mijoz)

    return True, []
