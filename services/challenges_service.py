"""
Challenges service for managing geographic challenges.
Provides the single source of truth for game challenges across all interfaces.
"""

import math
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from entities.challenge import Challenge, DifficultyLevel


@dataclass
class GuessResult:
    """Result of a guess submission."""
    challenge_id: str
    guessed_lat: float
    guessed_lng: float
    actual_lat: float
    actual_lng: float
    distance_km: float
    accuracy_percent: float
    points_earned: int
    max_points: int
    is_correct: bool  # Within acceptable distance


class ChallengesService:
    """
    Service for managing geographic challenges.
    Contains the challenge database and scoring logic used by all interfaces.
    """
    
    # Scoring constants
    MAX_POINTS_PER_CHALLENGE = 5000
    EARTH_RADIUS_KM = 6371
    
    def __init__(self):
        self._challenges = self._load_challenges()
        self._challenges_by_id = {c.id: c for c in self._challenges}
        self._challenges_by_difficulty = self._group_by_difficulty()
    
    def get_all_challenges(self) -> List[Challenge]:
        """Get all available challenges."""
        return self._challenges
    
    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        """Get a specific challenge by ID."""
        return self._challenges_by_id.get(challenge_id)
    
    def get_challenges_by_difficulty(self, difficulty: str) -> List[Challenge]:
        """Get challenges filtered by difficulty."""
        try:
            level = DifficultyLevel(difficulty.lower())
            return self._challenges_by_difficulty.get(level, [])
        except ValueError:
            return []
    
    def get_random_challenge(
        self, 
        difficulty: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[Challenge]:
        """
        Get a random challenge, optionally filtered by difficulty.
        
        Args:
            difficulty: Optional difficulty filter ('easy', 'medium', 'hard', 'expert', or 'random')
            exclude_ids: List of challenge IDs to exclude
        """
        exclude_ids = exclude_ids or []
        
        if difficulty and difficulty.lower() != 'random':
            challenges = self.get_challenges_by_difficulty(difficulty)
        else:
            challenges = self._challenges
        
        available = [c for c in challenges if c.id not in exclude_ids]
        
        if not available:
            return None
        
        return random.choice(available)
    
    def calculate_guess_result(
        self,
        challenge_id: str,
        guessed_lat: float,
        guessed_lng: float
    ) -> Optional[GuessResult]:
        """
        Calculate the result of a guess.
        
        Args:
            challenge_id: ID of the challenge being guessed
            guessed_lat: Guessed latitude
            guessed_lng: Guessed longitude
            
        Returns:
            GuessResult with distance, accuracy, and points
        """
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return None
        
        # Calculate distance using Haversine formula
        distance_km = self._haversine_distance(
            guessed_lat, guessed_lng,
            challenge.latitude, challenge.longitude
        )
        
        # Calculate accuracy (0-100%)
        accuracy = self._calculate_accuracy(distance_km, challenge.max_distance_km)
        
        # Calculate points
        points = self._calculate_points(distance_km, challenge.difficulty)
        
        # Determine if "correct" (within max distance)
        is_correct = distance_km <= challenge.max_distance_km
        
        return GuessResult(
            challenge_id=challenge_id,
            guessed_lat=guessed_lat,
            guessed_lng=guessed_lng,
            actual_lat=challenge.latitude,
            actual_lng=challenge.longitude,
            distance_km=round(distance_km, 2),
            accuracy_percent=round(accuracy, 1),
            points_earned=points,
            max_points=self.MAX_POINTS_PER_CHALLENGE,
            is_correct=is_correct
        )
    
    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return self.EARTH_RADIUS_KM * c
    
    def _calculate_accuracy(self, distance_km: float, max_distance_km: float) -> float:
        """Calculate accuracy percentage based on distance."""
        if distance_km <= 0:
            return 100.0
        if distance_km >= max_distance_km:
            return 0.0
        return 100.0 * (1 - distance_km / max_distance_km)
    
    def _calculate_points(self, distance_km: float, difficulty: DifficultyLevel) -> int:
        """
        Calculate points earned based on distance and difficulty.
        Uses exponential decay for more forgiving scoring.
        """
        # Difficulty multipliers
        multipliers = {
            DifficultyLevel.EASY: 0.8,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.3,
            DifficultyLevel.EXPERT: 1.5
        }
        
        # Perfect threshold (km) - get max points within this
        perfect_thresholds = {
            DifficultyLevel.EASY: 50,
            DifficultyLevel.MEDIUM: 25,
            DifficultyLevel.HARD: 10,
            DifficultyLevel.EXPERT: 5
        }
        
        # Max distance for any points
        max_distances = {
            DifficultyLevel.EASY: 10000,
            DifficultyLevel.MEDIUM: 5000,
            DifficultyLevel.HARD: 2500,
            DifficultyLevel.EXPERT: 1000
        }
        
        perfect = perfect_thresholds[difficulty]
        max_dist = max_distances[difficulty]
        multiplier = multipliers[difficulty]
        
        if distance_km <= perfect:
            # Perfect score
            base_points = self.MAX_POINTS_PER_CHALLENGE
        elif distance_km >= max_dist:
            # No points
            base_points = 0
        else:
            # Exponential decay
            normalized = (distance_km - perfect) / (max_dist - perfect)
            decay = math.exp(-3 * normalized)
            base_points = int(self.MAX_POINTS_PER_CHALLENGE * decay)
        
        return int(base_points * multiplier)
    
    def _group_by_difficulty(self) -> Dict[DifficultyLevel, List[Challenge]]:
        """Group challenges by difficulty level."""
        grouped = {level: [] for level in DifficultyLevel}
        for challenge in self._challenges:
            grouped[challenge.difficulty].append(challenge)
        return grouped
    
    def _load_challenges(self) -> List[Challenge]:
        """Load the challenge database."""
        challenges = []
        
        # Easy challenges - Famous landmarks & major cities
        easy_cities = [
            ("New York", (40.7128, -74.0060), "United States", "North America", 
             ["Largest city in USA", "Big Apple", "Statue of Liberty"]),
            ("London", (51.5074, -0.1278), "United Kingdom", "Europe", 
             ["Big Ben", "Thames River", "Capital of UK"]),
            ("Paris", (48.8566, 2.3522), "France", "Europe", 
             ["Eiffel Tower", "City of Light", "Capital of France"]),
            ("Tokyo", (35.6762, 139.6503), "Japan", "Asia", 
             ["Capital of Japan", "Mount Fuji nearby", "Largest metro area"]),
            ("Sydney", (-33.8688, 151.2093), "Australia", "Oceania", 
             ["Opera House", "Harbor Bridge", "Largest city in Australia"]),
            ("Berlin", (52.5200, 13.4050), "Germany", "Europe", 
             ["Brandenburg Gate", "Capital of Germany", "Berlin Wall"]),
            ("Rome", (41.9028, 12.4964), "Italy", "Europe", 
             ["Colosseum", "Vatican", "Eternal City"]),
            ("Madrid", (40.4168, -3.7038), "Spain", "Europe", 
             ["Prado Museum", "Capital of Spain", "Royal Palace"]),
            ("Moscow", (55.7558, 37.6176), "Russia", "Europe", 
             ["Red Square", "Kremlin", "Capital of Russia"]),
            ("Beijing", (39.9042, 116.4074), "China", "Asia", 
             ["Forbidden City", "Great Wall nearby", "Capital of China"]),
            ("Los Angeles", (34.0522, -118.2437), "United States", "North America", 
             ["Hollywood", "Beverly Hills", "City of Angels"]),
            ("Chicago", (41.8781, -87.6298), "United States", "North America", 
             ["Windy City", "Sears Tower", "Great Lakes"]),
            ("Toronto", (43.6532, -79.3832), "Canada", "North America", 
             ["CN Tower", "Largest city in Canada", "Great Lakes"]),
            ("Mexico City", (19.4326, -99.1332), "Mexico", "North America", 
             ["Largest city in Mexico", "Aztec heritage", "High altitude"]),
            ("São Paulo", (-23.5505, -46.6333), "Brazil", "South America", 
             ["Largest city in Brazil", "Economic center", "South America"]),
            ("Buenos Aires", (-34.6118, -58.3960), "Argentina", "South America", 
             ["Tango", "Capital of Argentina", "Paris of South America"]),
            ("Cairo", (30.0444, 31.2357), "Egypt", "Africa", 
             ["Pyramids nearby", "Nile River", "Capital of Egypt"]),
            ("Mumbai", (19.0760, 72.8777), "India", "Asia", 
             ["Bollywood", "Gateway of India", "Financial capital"]),
            ("Dubai", (25.2048, 55.2708), "UAE", "Asia", 
             ["Burj Khalifa", "Desert city", "Modern architecture"]),
            ("Singapore", (1.3521, 103.8198), "Singapore", "Asia", 
             ["City-state", "Marina Bay", "Garden City"]),
        ]
        
        # Medium challenges
        medium_cities = [
            ("Rio de Janeiro", (-22.9068, -43.1729), "Brazil", "South America", 
             ["Christ the Redeemer", "Copacabana Beach", "Former capital"]),
            ("Istanbul", (41.0082, 28.9784), "Turkey", "Europe", 
             ["Bosphorus Bridge", "Between two continents", "Former Constantinople"]),
            ("Cape Town", (-33.9249, 18.4241), "South Africa", "Africa", 
             ["Table Mountain", "Cape of Good Hope", "Legislative capital"]),
            ("Barcelona", (41.3851, 2.1734), "Spain", "Europe", 
             ["Sagrada Familia", "Mediterranean coast", "Gaudi architecture"]),
            ("Amsterdam", (52.3676, 4.9041), "Netherlands", "Europe", 
             ["Canals", "Tulips", "Capital of Netherlands"]),
            ("Vienna", (48.2082, 16.3738), "Austria", "Europe", 
             ["Classical music", "Danube River", "Imperial palaces"]),
            ("Prague", (50.0755, 14.4378), "Czech Republic", "Europe", 
             ["Charles Bridge", "Golden City", "Medieval architecture"]),
            ("Budapest", (47.4979, 19.0402), "Hungary", "Europe", 
             ["Danube River", "Thermal baths", "Parliament building"]),
            ("Stockholm", (59.3293, 18.0686), "Sweden", "Europe", 
             ["Capital of Sweden", "14 islands", "Nobel Prize"]),
            ("Dublin", (53.3498, -6.2603), "Ireland", "Europe", 
             ["Trinity College", "Guinness", "Emerald Isle"]),
            ("Lisbon", (38.7223, -9.1393), "Portugal", "Europe", 
             ["Atlantic coast", "Age of exploration", "Fado music"]),
            ("Athens", (37.9838, 23.7275), "Greece", "Europe", 
             ["Acropolis", "Parthenon", "Birthplace of democracy"]),
            ("Seoul", (37.5665, 126.9780), "South Korea", "Asia", 
             ["K-pop", "Technology hub", "Korean culture"]),
            ("Bangkok", (13.7563, 100.5018), "Thailand", "Asia", 
             ["Capital of Thailand", "Buddhist temples", "Street food"]),
            ("Nairobi", (1.2921, 36.8219), "Kenya", "Africa", 
             ["Capital of Kenya", "Safari hub", "Great Rift Valley"]),
        ]
        
        # Hard challenges
        hard_cities = [
            ("Ulaanbaatar", (47.8864, 106.9057), "Mongolia", "Asia", 
             ["Capital of Mongolia", "Coldest capital", "Genghis Khan"]),
            ("Reykjavik", (64.1466, -21.9426), "Iceland", "Europe", 
             ["Northernmost capital", "Geysers", "Northern Lights"]),
            ("Antananarivo", (-18.8792, 47.5079), "Madagascar", "Africa", 
             ["Capital of Madagascar", "Island nation", "Lemurs"]),
            ("Tbilisi", (41.7151, 44.8271), "Georgia", "Asia", 
             ["Capital of Georgia", "Caucasus mountains", "Wine country"]),
            ("Riga", (56.9496, 24.1052), "Latvia", "Europe", 
             ["Capital of Latvia", "Art nouveau", "Baltic Sea"]),
            ("Tallinn", (59.4370, 24.7536), "Estonia", "Europe", 
             ["Capital of Estonia", "Digital nomads", "Medieval walls"]),
            ("Ljubljana", (46.0569, 14.5058), "Slovenia", "Europe", 
             ["Capital of Slovenia", "Lake Bled nearby", "Green capital"]),
            ("Zagreb", (45.8150, 15.9819), "Croatia", "Europe", 
             ["Capital of Croatia", "Adriatic Sea nearby", "Balkan country"]),
            ("Sarajevo", (43.8486, 18.3564), "Bosnia", "Europe", 
             ["Capital of Bosnia", "1984 Olympics", "Siege history"]),
            ("Windhoek", (-22.5597, 17.0832), "Namibia", "Africa", 
             ["Capital of Namibia", "Kalahari Desert", "German colonial"]),
        ]
        
        # Expert challenges
        expert_cities = [
            ("Nuuk", (64.1836, -51.7214), "Greenland", "North America", 
             ["Capital of Greenland", "Arctic Circle", "Icebergs"]),
            ("Funafuti", (-8.5167, 179.2167), "Tuvalu", "Oceania", 
             ["Capital of Tuvalu", "Smallest country", "Rising sea levels"]),
            ("Thimphu", (27.4728, 89.6390), "Bhutan", "Asia", 
             ["Capital of Bhutan", "Happiness index", "Buddhist kingdom"]),
            ("Malé", (4.1755, 73.5093), "Maldives", "Asia", 
             ["Capital of Maldives", "Lowest country", "Coral atolls"]),
            ("Port Vila", (-17.7333, 168.3273), "Vanuatu", "Oceania", 
             ["Capital of Vanuatu", "Pacific islands", "Volcanoes"]),
            ("Dili", (-8.5569, 125.5603), "East Timor", "Asia", 
             ["Capital of East Timor", "Newest Asian nation", "Portuguese colonial"]),
            ("Praia", (14.9177, -23.5092), "Cape Verde", "Africa", 
             ["Capital of Cape Verde", "Atlantic islands", "Creole culture"]),
            ("Victoria", (-4.6199, 55.4513), "Seychelles", "Africa", 
             ["Capital of Seychelles", "Granite islands", "Indian Ocean"]),
            ("Moroni", (-11.7172, 43.2473), "Comoros", "Africa", 
             ["Capital of Comoros", "Volcanic islands", "Ylang-ylang perfume"]),
            ("Banjul", (13.4549, -16.5790), "Gambia", "Africa", 
             ["Capital of Gambia", "Smallest African mainland country", "River Gambia"]),
        ]
        
        # Max distances by difficulty
        max_distances = {
            DifficultyLevel.EASY: 10000,
            DifficultyLevel.MEDIUM: 5000,
            DifficultyLevel.HARD: 2500,
            DifficultyLevel.EXPERT: 1000
        }
        
        # Build challenge objects
        for cities, difficulty in [
            (easy_cities, DifficultyLevel.EASY),
            (medium_cities, DifficultyLevel.MEDIUM),
            (hard_cities, DifficultyLevel.HARD),
            (expert_cities, DifficultyLevel.EXPERT)
        ]:
            for name, coords, country, continent, hints in cities:
                challenge_id = f"{name.lower().replace(' ', '_')}_{country.lower().replace(' ', '_')}"
                challenges.append(Challenge(
                    id=challenge_id,
                    location_name=name,
                    latitude=coords[0],
                    longitude=coords[1],
                    country=country,
                    continent=continent,
                    difficulty=difficulty,
                    hints=hints,
                    max_distance_km=max_distances[difficulty]
                ))
        
        return challenges


# Singleton instance
_challenges_service: Optional[ChallengesService] = None


def get_challenges_service() -> ChallengesService:
    """Get the singleton challenges service instance."""
    global _challenges_service
    if _challenges_service is None:
        _challenges_service = ChallengesService()
    return _challenges_service
