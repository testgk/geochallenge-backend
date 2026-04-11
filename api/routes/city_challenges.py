"""
City Challenges API routes.
"""

from entities.challenge import ChallengeType
from api.routes.base import BaseChallengeRouter


class CityChallengeRouter( BaseChallengeRouter ):
    challenge_type = ChallengeType.CITY
    type_label     = "city"


router = CityChallengeRouter().router