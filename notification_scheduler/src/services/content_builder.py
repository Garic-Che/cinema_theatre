# services/content_builder.py
import logging
from typing import Dict, Any, List, Optional

from core.config import settings

logger = logging.getLogger(__name__)

class ContentBuilder:
    """
    Service for building personalized notification content.
    """
    def __init__(self):
        self.max_items = settings.MAX_NOTIFICATION_ITEMS

    def build_content(
            self,
            user: Dict[str, Any],
            films: List[Dict[str, Any]],
            bookmarks: List[Dict[str, Any]],
            likes: List[Dict[str, Any]],
            max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        if max_items is None:
            max_items = self.max_items

        logger.debug(f"Building personalized content for user {user.get('id')}")

        # Get user name for personalization
        user_name = user.get("login", "movie lover")

        # Prepare movies list with limited items
        movies = self._prepare_movies(films, bookmarks, likes, max_items)

        # Create personalized message
        personal_message = self._create_personal_message(user_name, movies)

        # Build final content
        content = {
            "movies": movies,
            "personal_message": personal_message
        }

        return content

    def _prepare_movies(
            self,
            films: List[Dict[str, Any]],
            bookmarks: List[Dict[str, Any]],
            likes: List[Dict[str, Any]],
            max_items: int
    ) -> List[Dict[str, Any]]:
        """Prepare movies list with personalized data"""
        # Extract film IDs from bookmarks and likes for quick lookup
        bookmark_ids = {b.get("content_id") for b in bookmarks}
        like_ids = {l.get("content_id") for l in likes}

        # Filter and process films
        processed_films = []

        # First prioritize films that user has bookmarked or liked
        for film in films:
            film_id = film.get("id")

            # Add bookmark and like flags
            film["is_bookmarked"] = film_id in bookmark_ids
            film["is_liked"] = film_id in like_ids

            # Add simplified genre list
            if "genres" in film and isinstance(film["genres"], list):
                film["genre_names"] = [g.get("name") for g in film["genres"]]

            processed_films.append(film)

        # Sort films by priority: bookmarked first, then liked, then by rating
        def film_priority(film):
            return (
                not film.get("is_bookmarked", False),  # Bookmarked first
                not film.get("is_liked", False),       # Then liked
                -1 * film.get("imdb_rating", 0)        # Then by rating (highest first)
            )

        processed_films.sort(key=film_priority)

        # Limit to max_items
        return processed_films[:max_items]

    def _create_personal_message(self, user_name: str, movies: List[Dict[str, Any]]) -> str:
        """Create a personalized message based on user and content"""
        if not movies:
            return f"Hello {user_name}! Check out our latest releases."

        if any(movie.get("is_bookmarked") for movie in movies):
            return f"Hello {user_name}! Here are updates about films you've bookmarked and other recommendations."

        if any(movie.get("is_liked") for movie in movies):
            return f"Hello {user_name}! Based on films you've liked, we think you'll enjoy these recommendations."

        return f"Hello {user_name}! Here are some film recommendations we think you'll enjoy."
