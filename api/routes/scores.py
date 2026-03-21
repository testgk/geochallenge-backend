"""
Scores and leaderboard API routes.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from api.models import (
    LeaderboardResponse,
    LeaderboardEntry,
    UserStatsResponse,
    GameModeEnum,
    LeaderboardPeriodEnum,
)
from services.scoring_service import get_scoring_service

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    game_mode: GameModeEnum = Query(default=GameModeEnum.CLASSIC, description="Game mode"),
    period: LeaderboardPeriodEnum = Query(default=LeaderboardPeriodEnum.ALL_TIME, description="Time period"),
    limit: int = Query(default=50, ge=1, le=100, description="Number of entries to return")
):
    """
    Get the leaderboard for a game mode.
    
    Returns ranked scores filtered by game mode and time period.
    """
    service = get_scoring_service()
    
    try:
        entries_data = service.get_leaderboard(
            game_mode=game_mode.value,
            period=period.value,
            limit=limit
        )
        
        entries = []
        for i, entry in enumerate(entries_data, 1):
            entries.append(LeaderboardEntry(
                rank=entry.get('rank', i),
                user_id=entry.get('user_id'),
                username=entry.get('username'),
                display_name=entry.get('display_name'),
                points=entry.get('points', 0),
                accuracy=entry.get('accuracy', 0.0),
                game_mode=game_mode.value,
                achieved_at=entry.get('achieved_at')
            ))
        
        return LeaderboardResponse(
            game_mode=game_mode.value,
            period=period.value,
            entries=entries,
            total_entries=len(entries)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )


@router.get("/user/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: int):
    """
    Get comprehensive statistics for a user.
    
    Returns games played, total score, best score, averages, and rank.
    """
    service = get_scoring_service()
    
    try:
        stats = service.get_user_stats(user_id)
        
        return UserStatsResponse(
            user_id=user_id,
            games_played=stats.get('games_played', 0),
            total_score=stats.get('total_score', 0),
            best_score=stats.get('best_score', 0),
            avg_score=stats.get('avg_score', 0.0),
            avg_accuracy=stats.get('avg_accuracy', 0.0),
            best_rank=stats.get('best_rank')
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user stats: {str(e)}"
        )


@router.get("/user/{user_id}/rank")
async def get_user_rank(
    user_id: int,
    game_mode: GameModeEnum = Query(default=GameModeEnum.CLASSIC, description="Game mode")
):
    """
    Get a user's rank in a specific game mode.
    """
    service = get_scoring_service()
    
    try:
        rank = service.score_repo.get_user_rank(user_id, game_mode.value)
        
        return {
            "user_id": user_id,
            "game_mode": game_mode.value,
            "rank": rank
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user rank: {str(e)}"
        )
