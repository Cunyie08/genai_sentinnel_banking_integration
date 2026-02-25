from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from Backend.middleware import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


# Schemas
class ThemeUpdate(BaseModel):
    theme: str


class LanguageUpdate(BaseModel):
    language: str


class NotificationsUpdate(BaseModel):
    enabled: bool
    email: Optional[bool] = None
    sms: Optional[bool] = None


class SecurityUpdate(BaseModel):
    mfa_enabled: Optional[bool] = None
    password_change_required: Optional[bool] = None


def _default_settings() -> Dict[str, Any]:
    return {
        "theme": "light",
        "language": "en",
        "notifications": {"enabled": True, "email": True, "sms": False},
        "security": {"mfa_enabled": False, "password_change_required": False},
    }


@router.get("/", summary="Get current user settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    # token payload may include settings; otherwise return defaults
    settings = current_user.get("settings") if isinstance(
        current_user, dict) else None
    if not settings:
        settings = _default_settings()
    return {"user": current_user.get("sub"), "settings": settings}


@router.patch("/update-theme", summary="Update theme")
def update_theme(payload: ThemeUpdate, current_user: dict = Depends(get_current_user)):
    settings = current_user.get("settings") or _default_settings()
    settings["theme"] = payload.theme
    # Note: not persisted — token payload or DB update needed for persistence
    return {"message": "Theme updated", "settings": settings}


@router.patch("/update-language", summary="Update language")
def update_language(payload: LanguageUpdate, current_user: dict = Depends(get_current_user)):
    settings = current_user.get("settings") or _default_settings()
    settings["language"] = payload.language
    return {"message": "Language updated", "settings": settings}


@router.patch("/update-notifications", summary="Update notification preferences")
def update_notifications(payload: NotificationsUpdate, current_user: dict = Depends(get_current_user)):
    settings = current_user.get("settings") or _default_settings()
    settings["notifications"] = {
        "enabled": payload.enabled,
        "email": payload.email if payload.email is not None else settings.get("notifications", {}).get("email"),
        "sms": payload.sms if payload.sms is not None else settings.get("notifications", {}).get("sms"),
    }
    return {"message": "Notification settings updated", "settings": settings}


@router.patch("/update-security", summary="Update security settings")
def update_security(payload: SecurityUpdate, current_user: dict = Depends(get_current_user)):
    settings = current_user.get("settings") or _default_settings()
    sec = settings.get("security", {})
    if payload.mfa_enabled is not None:
        sec["mfa_enabled"] = payload.mfa_enabled
    if payload.password_change_required is not None:
        sec["password_change_required"] = payload.password_change_required
    settings["security"] = sec
    return {"message": "Security settings updated", "settings": settings}
