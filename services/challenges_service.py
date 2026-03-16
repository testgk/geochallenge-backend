"""
Challenges service for managing geographic challenges.
Single source of truth for game logic - used by ALL interfaces (web, desktop, mobile).
"""

import math
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from entities.challenge import Challenge, DifficultyLevel


# Country areas in km² for threshold calculation
COUNTRY_AREA_KM2: Dict[str, float] = {
    "Russia": 17_098_242, "Canada": 9_984_670,
    "United States": 9_833_517, "China": 9_596_960,
    "Brazil": 8_515_767, "Australia": 7_692_024,
    "India": 3_287_263, "Argentina": 2_780_400,
    "Kazakhstan": 2_724_900, "Algeria": 2_381_741,
    "Saudi Arabia": 2_149_690, "Mexico": 1_964_375,
    "Indonesia": 1_904_569, "Sudan": 1_861_484,
    "Libya": 1_759_540, "Iran": 1_648_195,
    "Mongolia": 1_564_116, "Peru": 1_285_216,
    "South Africa": 1_219_090, "Colombia": 1_141_748,
    "Ethiopia": 1_104_300, "Egypt": 1_001_450,
    "Tanzania": 945_087, "Nigeria": 923_768,
    "Venezuela": 916_445, "Namibia": 824_292,
    "Mozambique": 801_590, "Pakistan": 881_913,
    "Turkey": 783_562, "Chile": 756_102,
    "Zambia": 752_612, "Myanmar": 676_578,
    "Afghanistan": 652_230, "Ukraine": 603_550,
    "Botswana": 581_730, "Madagascar": 587_041,
    "Kenya": 580_367, "France": 643_801,
    "Thailand": 513_120, "Spain": 505_990,
    "Japan": 377_915, "Germany": 357_114,
    "Finland": 338_145, "Malaysia": 329_847,
    "Vietnam": 331_212, "Norway": 323_802,
    "Poland": 312_696, "Italy": 301_340,
    "Philippines": 300_000, "New Zealand": 268_838,
    "United Kingdom": 243_610, "Uganda": 241_038,
    "Ghana": 238_533, "Romania": 238_397,
    "Laos": 236_800, "Guyana": 214_969,
    "Belarus": 207_600, "Kyrgyzstan": 199_951,
    "Senegal": 196_722, "Cambodia": 181_035,
    "Uruguay": 176_215, "Suriname": 163_820,
    "Tunisia": 163_610, "Bangladesh": 147_570,
    "Nepal": 147_181, "Tajikistan": 143_100,
    "Greece": 131_957, "North Korea": 120_538,
    "Iceland": 103_000, "South Korea": 99_678,
    "Hungary": 93_028, "Portugal": 92_212,
    "Jordan": 89_342, "Azerbaijan": 86_600,
    "Austria": 83_871, "UAE": 83_600,
    "Czech Republic": 78_866, "Serbia": 77_474,
    "Panama": 75_417, "Georgia": 69_700,
    "Sri Lanka": 65_610, "Lithuania": 65_300,
    "Latvia": 64_589, "Croatia": 56_594,
    "Bosnia": 51_197, "Costa Rica": 51_100,
    "Slovakia": 49_035, "Estonia": 45_228,
    "Denmark": 42_924, "Netherlands": 41_543,
    "Switzerland": 41_285, "Bhutan": 38_394,
    "Moldova": 33_846, "Belgium": 30_528,
    "Armenia": 29_743, "Albania": 28_748,
    "Slovenia": 20_273, "Israel": 20_770,
    "Cyprus": 9_251, "Luxembourg": 2_586,
    "Vanuatu": 12_189, "Fiji": 18_274,
    "Tuvalu": 26, "Maldives": 298,
    "Singapore": 728, "Greenland": 836_330,
    "Cape Verde": 4_033, "Seychelles": 459,
    "Comoros": 2_235, "Gambia": 11_295,
    "East Timor": 14_874,
}

# =============================================================================
# SCORING ZONE CONFIGURATION - Single source of truth for ALL interfaces
# =============================================================================
# Both backend scoring and visual display (web, desktop) derive from this.
# Bigger score = thinner ring zone.

SCORING_ZONES = [
    {"inner": 0.00, "outer": 0.10, "color": "green",  "label": "Perfect"},   # Best
    {"inner": 0.10, "outer": 0.30, "color": "yellow", "label": "Great"},     # Good
    {"inner": 0.30, "outer": 0.60, "color": "orange", "label": "Good"},      # OK
    {"inner": 0.60, "outer": 1.00, "color": "red",    "label": "Close"},     # Worst
]


def get_scoring_zones_config() -> List[Dict[str, Any]]:
    """
    Get the scoring zone configuration.
    This is THE single source of truth for zone boundaries.
    """
    return SCORING_ZONES


# =============================================================================
# CORE SCORING LOGIC - Used by ALL interfaces
# =============================================================================

def calculate_score(distance_km: float, threshold_km: float) -> int:
    """
    THE scoring function. Takes distance and threshold, returns score 0-100.
    This is the ONLY place scoring logic lives.
    """
    if distance_km > threshold_km:
        return 0
    if distance_km <= 0:
        return 100
    
    # Linear decay: 100 at center, 0 at threshold
    return int(100 * (1 - distance_km / threshold_km))


def get_scoring_zone(distance_km: float, threshold_km: float) -> str:
    """Determine which scoring zone a distance falls into."""
    if distance_km > threshold_km:
        return "miss"
    
    fraction = distance_km / threshold_km
    for zone in SCORING_ZONES:
        if zone["inner"] <= fraction < zone["outer"]:
            return zone["color"]
    return "red"  # Edge case at exactly threshold


def get_threshold_km(country: str, difficulty: DifficultyLevel) -> float:
    """
    Calculate threshold based on country size and difficulty.
    Larger countries = larger threshold = more forgiving.
    """
    BASE_THRESHOLD_KM = 600.0   # Minimum threshold - increased for easier scoring
    MAX_THRESHOLD_KM = 1100.0   # Maximum threshold cap - increased for easier scoring
    
    DIFFICULTY_MULTIPLIERS = {
        DifficultyLevel.EASY: 2.0,
        DifficultyLevel.MEDIUM: 1.4,
        DifficultyLevel.HARD: 1.0,
        DifficultyLevel.EXPERT: 0.65,
    }
    
    area_km2 = COUNTRY_AREA_KM2.get(country, 500_000)
    multiplier = DIFFICULTY_MULTIPLIERS[difficulty]
    country_km = math.sqrt(area_km2) * multiplier
    
    return min(MAX_THRESHOLD_KM, max(BASE_THRESHOLD_KM, country_km))


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    EARTH_RADIUS_KM = 6371
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class GuessResult:
    """Result of a guess submission."""
    challenge_id: str
    guessed_lat: float
    guessed_lng: float
    actual_lat: float
    actual_lng: float
    distance_km: float
    threshold_km: float
    score: int  # 0-100
    scoring_zone: str
    is_correct: bool


class ChallengesService:
    """
    Service for managing challenges and calculating results.
    All scoring uses the core functions above.
    """
    
    def __init__(self):
        self._challenges = self._load_challenges()
        self._challenges_by_id = {c.id: c for c in self._challenges}
        self._challenges_by_difficulty = self._group_by_difficulty()
    
    def get_all_challenges(self) -> List[Challenge]:
        return self._challenges
    
    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        return self._challenges_by_id.get(challenge_id)
    
    def get_challenges_by_difficulty(self, difficulty: str) -> List[Challenge]:
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
        exclude_ids = exclude_ids or []
        
        if difficulty and difficulty.lower() != 'random':
            challenges = self.get_challenges_by_difficulty(difficulty)
        else:
            challenges = self._challenges
        
        available = [c for c in challenges if c.id not in exclude_ids]
        return random.choice(available) if available else None
    
    def calculate_guess_result(
        self,
        challenge_id: str,
        guessed_lat: float,
        guessed_lng: float
    ) -> Optional[GuessResult]:
        """Calculate result using the core scoring functions."""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return None
        
        # Calculate distance
        distance_km = haversine_distance(
            guessed_lat, guessed_lng,
            challenge.latitude, challenge.longitude
        )
        
        # Get threshold for this country/difficulty
        threshold_km = get_threshold_km(challenge.country, challenge.difficulty)
        
        # Calculate score using THE scoring function
        score = calculate_score(distance_km, threshold_km)
        
        # Get scoring zone
        zone = get_scoring_zone(distance_km, threshold_km)
        
        return GuessResult(
            challenge_id=challenge_id,
            guessed_lat=guessed_lat,
            guessed_lng=guessed_lng,
            actual_lat=challenge.latitude,
            actual_lng=challenge.longitude,
            distance_km=round(distance_km, 2),
            threshold_km=round(threshold_km, 2),
            score=score,
            scoring_zone=zone,
            is_correct=(distance_km <= threshold_km)
        )
    
    def get_scoring_zones_for_challenge(self, challenge_id: str) -> Optional[List[Dict]]:
        """Get scoring zone data for visual ring display."""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return None
        
        threshold = get_threshold_km(challenge.country, challenge.difficulty)
        
        return [
            {
                "inner_fraction": zone["inner"],
                "outer_fraction": zone["outer"],
                "color": zone["color"],
                "label": zone["label"],
                "inner_km": threshold * zone["inner"],
                "outer_km": threshold * zone["outer"],
            }
            for zone in SCORING_ZONES
        ]
    
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
