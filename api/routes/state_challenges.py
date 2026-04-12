"""
Country Challenges API routes.
"""

from entities.challenge import ChallengeType
from api.routes.base import BaseChallengeRouter


class CountryChallengeRouter( BaseChallengeRouter ):
    challenge_type = ChallengeType.COUNTRY
    type_label     = "country"


router = CountryChallengeRouter().router