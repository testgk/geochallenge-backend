"""
State Challenges API routes.
"""

from entities.challenge import ChallengeType
from api.routes.base import BaseChallengeRouter


class StateChallengeRouter( BaseChallengeRouter ):
    challenge_type = ChallengeType.STATE
    type_label     = "state"


router = StateChallengeRouter().router