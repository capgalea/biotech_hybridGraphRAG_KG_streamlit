from typing import Tuple, Optional

# Static mapping for major Australian universities and research institutes
INSTITUTION_COORDINATES = {
    # VIC
    "University of Melbourne": (-37.7982, 144.9610),
    "The University of Melbourne": (-37.7982, 144.9610),
    "Monash University": (-37.9105, 145.1362),
    "RMIT University": (-37.8078, 144.9633),
    "Deakin University": (-38.1987, 144.2993),
    "La Trobe University": (-37.7208, 145.0487),
    "Swinburne University of Technology": (-37.8220, 145.0389),
    "Walter and Eliza Hall Institute": (-37.7989, 144.9556),
    "WEHI": (-37.7989, 144.9556),
    "Murdoch Children's Research Institute": (-37.7936, 144.9497),
    "MCRI": (-37.7936, 144.9497),
    "Peter MacCallum Cancer Centre": (-37.7986, 144.9497),
    "Burnet Institute": (-37.8447, 144.9829),
    "Baker Heart and Diabetes Institute": (-37.8465, 144.9818),
    "Florey Institute": (-37.7987, 144.9567),
    "St Vincent's Institute": (-37.8074, 144.9743),

    # NSW
    "University of Sydney": (-33.8886, 151.1873),
    "The University of Sydney": (-33.8886, 151.1873),
    "UNSW Sydney": (-33.9173, 151.2313),
    "University of New South Wales": (-33.9173, 151.2313),
    "University of Technology Sydney": (-33.8832, 151.2004),
    "UTS": (-33.8832, 151.2004),
    "Macquarie University": (-33.7738, 151.1126),
    "Garvan Institute of Medical Research": (-33.8778, 151.2217),
    "Victor Chang Cardiac Research Institute": (-33.8767, 151.2222),
    "George Institute for Global Health": (-33.9678, 151.1192), # Newtown/Sydney
    
    # QLD
    "University of Queensland": (-27.4975, 153.0137),
    "The University of Queensland": (-27.4975, 153.0137),
    "QIMR Berghofer Medical Research Institute": (-27.4516, 153.0270),
    "Griffith University": (-27.5540, 153.0514),
    "Queensland University of Technology": (-27.4772, 153.0284),
    "QUT": (-27.4772, 153.0284),
    
    # ACT
    "Australian National University": (-35.2777, 149.1185),
    "ANU": (-35.2777, 149.1185),
    "CSIRO": (-35.2750, 149.1130), # Black Mountain
    
    # SA
    "University of Adelaide": (-34.9205, 138.6061),
    "Flinders University": (-35.0169, 138.5684),
    "SAHMRI": (-34.9213, 138.5901),
    
    # WA
    "University of Western Australia": (-31.9799, 115.8172),
    "Telethon Kids Institute": (-31.9566, 115.8344),
    "Curtin University": (-32.0062, 115.8950),

    # Others
    "University of Newcastle": (-32.8927, 151.7042),
    "University of Wollongong": (-34.4045, 150.8812)
}

def get_institution_coordinates(institution_name: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates (lat, lon) for a given institution name.
    Matches nicely against keys even with minor variations if needed in future (fuzzy matching).
    Currently implemented as direct lookup with case-insensitive check if direct fail.
    """
    if not institution_name:
        return None
        
    # 1. Direct match
    if institution_name in INSTITUTION_COORDINATES:
        return INSTITUTION_COORDINATES[institution_name]
        
    # 2. Case insensitive match
    for k, v in INSTITUTION_COORDINATES.items():
        if k.lower() == institution_name.lower():
            return v
            
    # 3. Partial match check (heuristic - careful with this)
    # e.g. "Uni of Melbourne" matches "University of Melbourne"
    # For now, skip to avoid false positives. 
    
    return None
