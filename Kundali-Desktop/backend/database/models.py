from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import datetime
import enum
from .connection import Base

# Timezone-aware UTC helper (Python 3.12+ deprecates datetime.utcnow())
def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class UserRole(str, enum.Enum):
    MASTER_ADMIN = "master_admin"
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)   # optional — no email verification
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_master = Column(Boolean, default=False, nullable=False)
    force_password_change = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    # Forgot password request flag — set by user, cleared by admin after reset
    forgot_password_requested = Column(Boolean, default=False, nullable=False)

    # Set by the admin to approve a normal user's password-reset request.
    #
    # A normal user cannot reset their own password from the stored mobile
    # number (that is the admin's recovery route only).  They file a request,
    # the admin approves it here, and *only then* the "password forgot" page
    # becomes usable for them.  Cleared as soon as the new password is saved.
    password_reset_approved = Column(Boolean, default=False, nullable=False)

    # Informational contact number (required at registration).
    #
    # This is NOT an OTP factor: the project has no SMS gateway.  It is stored
    # for information and only *compared* when (a) the owner confirms a profile
    # update, or (b) the master asks to recover the master password.
    phone = Column(String, nullable=True)
    phone_verified_at = Column(DateTime, nullable=True)   # confirmation accepted
    phone_updated_at = Column(DateTime, nullable=True)

    # Last plaintext password set by admin (so admin can see it) — stored plaintext intentionally
    # Only populated when admin resets password; cleared on user self-change
    last_reset_password = Column(String, nullable=True)

    # Relationships
    records = relationship("KundaliRecord", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class KundaliRecord(Base):
    __tablename__ = "kundali_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)  # YYYY-MM-DD
    birth_time = Column(String, nullable=False)  # HH:MM:SS
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(Float, nullable=False)     # e.g., 5.75 for Nepal
    timezone_id = Column(String, nullable=True)
    country = Column(String, nullable=True)
    birth_place = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    # Optional, additive identity fields used only by the traditional
    # Janmapatrika module. Existing calculations remain independent of them.
    full_name = Column(String, nullable=True)
    father_name = Column(String, nullable=True)
    mother_name = Column(String, nullable=True)
    gotra = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    kula = Column(String, nullable=True)
    kuladevata = Column(String, nullable=True)
    spouse_name = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    family_details = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    user = relationship("User", back_populates="records")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    ayanamsha_type = Column(String, default="LAHIRI")  # LAHIRI, RAMAN, KP, TROPICAL
    chart_style = Column(String, default="NORTH_INDIAN")  # NORTH_INDIAN, SOUTH_INDIAN
    language = Column(String, default="en")  # en, ne

    # Relationships
    user = relationship("User", back_populates="settings")


class OTPStore(Base):
    """Kept for DB backward compatibility. No longer used by new auth flow."""
    __tablename__ = "otp_store"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=True)
    otp_code = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    used = Column(Boolean, default=False, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class AuditLog(Base):
    """Security audit log for tracking authentication and user management events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False, index=True)
    performed_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    details = Column(Text, nullable=True)

    # Relationship
    user = relationship("User")


class AppConfig(Base):
    """Global application configuration stored as key-value pairs.

    Kept for backward compatibility with older databases.
    """
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
