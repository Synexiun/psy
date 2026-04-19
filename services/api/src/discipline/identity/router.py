from fastapi import APIRouter

router = APIRouter(prefix="/me", tags=["identity"])


@router.get("")
async def current_user() -> dict[str, str]:
    """Stub — wire to UserService.get_current in the first real milestone."""
    return {"status": "not_implemented"}
