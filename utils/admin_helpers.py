from database.requests import find_user_by_username


async def resolve_target(token: str) -> int | None:
    token = token.strip()
    if token.startswith("@"):
        user = await find_user_by_username(token)
        return user.id if user else None
    if token.lstrip("-").isdigit():
        return int(token)
    return None
