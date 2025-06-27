from app.services.bing import get_peapix_image
from app.data.database import AsyncSessionLocal
from app.data.repository import RepositoryFactory
from app.data.models import Bing
from app.config import setup_logger

logger = setup_logger("bing_generator", indent=4)

async def generate_bing_message(country: str = "ca", count: int = 1) -> dict:
    """
    Generate a Bing image message, save it to the database, and return the image data.

    Args:
        country (str): Country code for the Bing image feed (default: "ca").
        count (int): Number of images to fetch (default: 1).

    Returns:
        dict: Dictionary containing Bing image metadata and description.
    """
    
    logger.info("Generating Bing message")
    bing_data = await get_peapix_image(country, count)
    
    if bing_data and bing_data["url"] != "" and bing_data["title"] != "":
        logger.info("Saving Bing message to database")
        try:
            async with AsyncSessionLocal() as session:
                repo = RepositoryFactory(session).get_repository(Bing)
                await repo.truncate(max_entries=12, keep_entries=4)
                await repo.create(
                    url=bing_data.get("url"),
                    title=bing_data.get("title"),
                    description=bing_data.get("description"),
                    page_date=bing_data.get("page_date"),
                    copyright=bing_data.get("copyright"),
                    page_url=bing_data.get("pageUrl"),
                )
        except Exception as e:
            logger.error(f"Failed to save Bing message: {e}")
        logger.info(f"Bing message saved to the database")
    else:
        logger.error(f"Failed to generate Bing message")
    

    return bing_data

async def main() -> None:
   response_content = await generate_bing_message()
   print(response_content)

if __name__ == '__main__':
   import asyncio
   asyncio.run(main())