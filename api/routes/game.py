"""
Game session API routes.
"""

from fastapi import APIRouter, HTTPException, status

from api.models import (
    StartGameRequest,
    SubmitRoundRequest,
    RoundResultResponse,
    GameSessionResponse,
    GameResultResponse,
    SuccessResponse,
)
from entities.game_session import GameMode
from services.scoring_service import ScoringService

router = APIRouter()


def _get_scoring_service() -> ScoringService:
    """Get scoring service instance."""
    return ScoringService()


@router.post("/start", response_model=GameSessionResponse)
async def start_game(request: StartGameRequest):
    """
    Start a new game session.
    
    If the user has an existing active session, it will be abandoned.
    """
    service = _get_scoring_service()
    
    try:
        game_mode = GameMode(request.game_mode.value)
        session = service.start_game(
            user_id=request.user_id,
            game_mode=game_mode,
            difficulty=request.difficulty.value,
            total_rounds=request.total_rounds
        )
        
        return GameSessionResponse(
            id=session.id,
            user_id=session.user_id,
            game_mode=session.game_mode.value,
            status=session.status.value,
            score=session.score,
            rounds_played=session.rounds_played,
            total_rounds=session.total_rounds,
            total_distance_error=session.total_distance_error,
            avg_response_time=session.avg_response_time,
            difficulty=session.difficulty,
            started_at=session.started_at,
            completed_at=session.completed_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start game: {str(e)}"
        )


@router.post("/{session_id}/round", response_model=RoundResultResponse)
async def submit_round(session_id: int, request: SubmitRoundRequest):
    """
    Submit a round result for scoring.
    
    Call this after each guess in the game to record the result
    and get the points earned.
    """
    service = _get_scoring_service()
    
    result = service.submit_round(
        session_id=session_id,
        distance_error_km=request.distance_error_km,
        response_time_seconds=request.response_time_seconds
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found or not active"
        )
    
    return RoundResultResponse(
        round_number=result.round_number,
        distance_error_km=result.distance_error_km,
        response_time_seconds=result.response_time_seconds,
        points_earned=result.points_earned,
        accuracy_percent=result.accuracy_percent,
        total_score=result.total_score
    )


@router.post("/{session_id}/end", response_model=GameResultResponse)
async def end_game(session_id: int):
    """
    End a game session and get final results.
    
    This records the final score and returns rankings.
    """
    service = _get_scoring_service()
    
    result = service.end_game(session_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    return GameResultResponse(
        session_id=result.session_id,
        user_id=result.user_id,
        final_score=result.final_score,
        rounds_played=result.rounds_played,
        total_distance_error=result.total_distance_error,
        avg_response_time=result.avg_response_time,
        accuracy=result.accuracy,
        grade=result.grade,
        is_personal_best=result.is_personal_best,
        rank=result.rank
    )


@router.post("/{session_id}/abandon", response_model=SuccessResponse)
async def abandon_game(session_id: int):
    """Abandon an active game session."""
    service = _get_scoring_service()
    
    success = service.abandon_game(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found or not active"
        )
    
    return SuccessResponse(message="Game abandoned successfully")


@router.get("/active/{user_id}", response_model=GameSessionResponse)
async def get_active_game(user_id: int):
    """Get the user's active game session if any."""
    service = _get_scoring_service()
    
    session = service.get_active_game(user_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active game session found"
        )
    
    return GameSessionResponse(
        id=session.id,
        user_id=session.user_id,
        game_mode=session.game_mode.value,
        status=session.status.value,
        score=session.score,
        rounds_played=session.rounds_played,
        total_rounds=session.total_rounds,
        total_distance_error=session.total_distance_error,
        avg_response_time=session.avg_response_time,
        difficulty=session.difficulty,
        started_at=session.started_at,
        completed_at=session.completed_at
    )
