"""FastAPI backend for Sengoku Attendance Bot."""
import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import (
        get_members,
        get_user,
        get_user_events,
        get_user_payments,
        get_archives,
        get_archive_path,
        get_levels_and_achievements,
        get_user_achievements,
    )
    from models import (
        MembersListResponse,
        UserEventsResponse,
        UserPaymentsResponse,
        ArchivesListResponse,
        HealthResponse,
        MemberResponse,
        EventResponse,
        PaymentResponse,
        UserDetailResponse,
        ArchiveResponse,
        LevelsAndAchievementsResponse,
        UserAchievementsResponse,
        LevelResponse,
        AchievementResponse,
    )
except ImportError:
    from api.database import (
        get_members,
        get_user,
        get_user_events,
        get_user_payments,
        get_archives,
        get_archive_path,
        get_levels_and_achievements,
        get_user_achievements,
    )
    from api.models import (
        MembersListResponse,
        UserEventsResponse,
        UserPaymentsResponse,
        ArchivesListResponse,
        HealthResponse,
        MemberResponse,
        EventResponse,
        PaymentResponse,
        UserDetailResponse,
        ArchiveResponse,
        LevelsAndAchievementsResponse,
        UserAchievementsResponse,
        LevelResponse,
        AchievementResponse,
    )


# Create FastAPI app
app = FastAPI(
    title="Sengoku Attendance Bot API",
    description="RESTful API for Sengoku Attendance Bot web application",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with technical timeout status."""
    technical_timeout = os.getenv("TECHNICAL_TIMEOUT", "0") == "1"
    return {
        "status": "maintenance" if technical_timeout else "ok",
        "technical_timeout": technical_timeout,
    }


@app.get("/api/archives", response_model=ArchivesListResponse)
async def list_archives():
    """Get list of available archive databases."""
    archives = get_archives()
    return {
        "archives": [ArchiveResponse(**archive) for archive in archives]
    }


@app.get("/api/members", response_model=MembersListResponse)
async def list_members(
    db: Optional[str] = Query(None, description="Archive database name (e.g., 'january_2024')")
):
    """
    Get list of all members with their event counts and payment totals.
    
    Query Parameters:
    - db: Optional archive database name in format {month}_{year}
    """
    db_path = None
    
    if db:
        db_path = get_archive_path(db)
        if not db_path:
            raise HTTPException(status_code=404, detail="Archive database not found")
    
    try:
        members_data = get_members(db_path)
        members = [MemberResponse(**member) for member in members_data]
        
        return {
            "members": members,
            "total_count": len(members),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/members/{uid}/events", response_model=UserEventsResponse)
async def get_member_events(
    uid: str,
    db: Optional[str] = Query(None, description="Archive database name (e.g., 'january_2024')")
):
    """
    Get all events for a specific member.
    
    Path Parameters:
    - uid: User ID (Discord UID)
    
    Query Parameters:
    - db: Optional archive database name in format {month}_{year}
    """
    db_path = None
    
    if db:
        db_path = get_archive_path(db)
        if not db_path:
            raise HTTPException(status_code=404, detail="Archive database not found")
    
    try:
        # Get user details
        user_data = get_user(uid, db_path)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user events
        events_data = get_user_events(uid, db_path)
        events = [EventResponse(**event) for event in events_data]
        
        return {
            "user": UserDetailResponse(**user_data),
            "events": events,
            "total_count": len(events),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/members/{uid}/payments", response_model=UserPaymentsResponse)
async def get_member_payments(
    uid: str,
    db: Optional[str] = Query(None, description="Archive database name (e.g., 'january_2024')")
):
    """
    Get all payments for a specific member.

    Path Parameters:
    - uid: User ID (Discord UID)

    Query Parameters:
    - db: Optional archive database name in format {month}_{year}
    """
    db_path = None

    if db:
        db_path = get_archive_path(db)
        if not db_path:
            raise HTTPException(status_code=404, detail="Archive database not found")

    try:
        # Get user details
        user_data = get_user(uid, db_path)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user payments
        payments_data = get_user_payments(uid, db_path)
        payments = [PaymentResponse(**payment) for payment in payments_data]

        return {
            "user": UserDetailResponse(**user_data),
            "payments": payments,
            "total_count": len(payments),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/levels", response_model=LevelsAndAchievementsResponse)
async def list_levels_and_achievements():
    """
    Get all available BP levels and achievements (no user data).
    Uses the main database only; read-only.
    """
    try:
        data = get_levels_and_achievements()
        return {
            "levels": [LevelResponse(**lev) for lev in data["levels"]],
            "achievements": [AchievementResponse(**a) for a in data["achievements"]],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/members/{uid}/achievements", response_model=UserAchievementsResponse)
async def get_member_achievements(uid: str):
    """
    Get all achievements achieved by a specific member.
    Uses the main database only; read-only.
    """
    try:
        user_data = get_user(uid, None)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        achievements_data = get_user_achievements(uid, None)
        return {
            "user": UserDetailResponse(**user_data),
            "achievements": [AchievementResponse(**a) for a in achievements_data],
            "total_count": len(achievements_data),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sengoku Attendance Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
