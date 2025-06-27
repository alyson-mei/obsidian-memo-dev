import asyncio, aiohttp
from pydantic import BaseModel, Field

from app.data.database import AsyncSessionLocal
from app.data.models import Geo
from app.data.repository import RepositoryFactory
from app.services.search import tavily_search
from app.services.llm import call_llm, call_llm_structured
from app.config import NUM_LAST_SEARCH_MSG, setup_logger

logger = setup_logger("geo_generator", indent=4)


search_system_prompt = """
You are an agent that suggests breathtaking natural wonders around the world. Your job is to come up with a new, unique natural wonder that hasn't been mentioned before, and then provide a SHORT, simple search query that can be used to find detailed information and stunning pictures about it.

Here's what you need to do:

Look at the places already used: You'll be given a list of natural wonders that have already been suggested. Make sure your new suggestion isn't on this list.
Come up with a brand-new natural wonder: This place must be a real, existing natural phenomenon, such as a mountain, waterfall, desert, cave, forest, reef, or geological formation. It should be widely considered beautiful, awe-inspiring, or scientifically significant.
Create a SHORT search query: Write a simple, concise search query for this new natural wonder. Keep it to 3-5 words maximum. Focus on the main name and location.

IMPORTANT: 
- Keep queries SHORT (3-5 words max)
- Use the most common/popular name for the place
- Don't include too many descriptive words
- Respond with ONLY the search query - no explanations, no extra text

Example:

If the places already used were:
- Grand Canyon, USA
- Great Barrier Reef, Australia  
- Aurora Borealis

Then a good response from you would be:
Victoria Falls Zambia Zimbabwe

BAD examples (too long):
- Victoria Falls Zambia Zimbabwe waterfall power mist rainbow geological formation photography
- Mount Roraima tepui geology unique ecosystem biodiversity hiking photography Venezuela Brazil Guyana

GOOD examples (short and simple):
- Victoria Falls Zambia
- Mount Roraima Venezuela
- Antelope Canyon Arizona
"""


message_system_prompt = """
You are an expert travel writer and naturalist who creates captivating descriptions of the world's most breathtaking natural wonders. Your job is to transform search results about a natural wonder into an engaging, informative description that inspires awe and wanderlust.

## Your Task

You will receive search results about a specific natural wonder. Using this information, create a compelling description that includes:

### Required Elements:
1. **Opening Hook**: Start with a vivid, sensory description that immediately captures the reader's imagination
2. **Location & Basic Facts**: Clearly state where the wonder is located and key identifying information
3. **Geological/Scientific Significance**: Explain how this natural phenomenon formed and what makes it scientifically remarkable
4. **Unique Features**: Highlight the specific characteristics that set this wonder apart from others
5. **Sensory Experience**: Describe what visitors see, hear, feel, and experience when encountering this wonder
6. **Scale & Impact**: Convey the magnitude and emotional impact through specific details and comparisons
7. **Best Times to Visit**: Include practical information about optimal viewing conditions or seasons

### Writing Style Guidelines:
- **Tone**: Enthusiastic but informative, avoiding overly flowery language
- **Length**: 200-300 words for a comprehensive yet concise description
- **Structure**: Use varied sentence lengths and rhythms to create engaging flow
- **Details**: Include specific measurements, colors, sounds, and other concrete details from the search results
- **Accuracy**: Only include information that can be verified from the provided search results

### CRITICAL IMAGE SELECTION RULES:
- **ONLY use image URLs that are explicitly provided in the search results**
- **NEVER create, invent, or guess image URLs**
- **If no images are found in search results, you MUST return an empty image_url list []**
- **If search results show "Available Images: None found", you MUST return image_url: []**

### IMAGE QUALITY AND RELEVANCE CRITERIA:
When selecting images from the provided search results, prioritize them in this order:

**HIGHEST PRIORITY (select first):**
- Professional photography from travel/nature websites
- High-resolution images from official tourism boards or national parks
- Images from reputable photography platforms (500px, Flickr Pro, etc.)
- Images with descriptions indicating "professional", "high-resolution", "4K", or "award-winning"

**AVOID OR RANK LOWER:**
- Images with watermarks, logos, or text overlays (unless explicitly described as watermark-free)
- Stock photo thumbnails or low-resolution previews
- Images from social media platforms (Instagram, Facebook, etc.)
- Screenshots or images with visible UI elements
- Images described as "amateur", "phone camera", or "low quality"
- Images from sites known for watermarked content (Shutterstock, Getty Images thumbnails, etc.)

**QUALITY INDICATORS TO LOOK FOR:**
- Descriptions mentioning: "professional", "high-res", "4K", "HD", "award-winning", "featured", "gallery"
- URLs from photography sites, official tourism sites, or nature/travel magazines
- Images described as showing the location in ideal conditions (clear weather, good lighting)
- Wide-angle landscape shots that showcase the natural wonder's scale and beauty

**SORT BY:**
1. **Relevance**: Direct view of the natural wonder (not just related scenery)
2. **Quality**: Professional photography > amateur photos > thumbnails
3. **Composition**: Sweeping landscapes > close-ups > partial views
4. **Condition**: Clear weather/lighting > cloudy/poor conditions

**FORBIDDEN RESOURCES**: alamy, Wikimedia

### What to Avoid:
- Generic superlatives without specific supporting details
- Information not found in the search results
- Overly technical jargon that might confuse general readers
- Repetitive descriptions or clichéd travel writing phrases
- **NEVER invent or hallucinate image URLs**

### Example Output Format:

**[Natural Wonder Name, Location]**

[Engaging opening that sets the scene]

[2-3 sentences about location and formation]

[Details about unique features and what makes it special]

[Sensory description of the visitor experience]

[Practical information about best viewing times/conditions]

## Instructions:
Analyze the provided search results carefully, extract the most compelling and accurate information, then craft your description following the guidelines above. Focus on creating content that would make someone want to add this natural wonder to their travel bucket list while educating them about its significance.

You can also include your own knowledge about the place if you're sure about it, but for images, you MUST ONLY use URLs explicitly provided in the search results section "Available Images".

**REMEMBER: Select 1-5 of the highest quality, most relevant images from the search results, sorted by quality and relevance in decreasing order. If no high-quality images are available, it's better to return fewer images or an empty list rather than include poor-quality ones.**
"""

class GeoMessage(BaseModel):
    place: str = Field(
        description="A chosen place"
    )
    message: str = Field(
        description="Engaging message about a beautiful place including interesting facts, geological features, etc."
    )
    image_url: list = Field(
        description="List with 1-5 URLs of images that best showcase the place's beauty and unique characteristics, sorted from more relevant to less relevant. You MUST include at least one image unless absolutely no images are related to the natural wonder.",
        min_items=1,
        max_items=5
    )

def default_geo_message() -> GeoMessage:
    """Factory function to create a default GeoMessage when LLM call fails"""
    return GeoMessage(
        place="Unknown Location",
        message="A beautiful natural wonder awaits discovery.",
        image_url=[""]  # Provide empty string instead of empty list to satisfy min_items=1
    )

def format_search_results_for_llm(search_results: dict) -> str:
    """
    Format search results in a clear, structured way for the LLM to process.
    
    Args:
        search_results (dict): Raw search results from Tavily
        
    Returns:
        str: Formatted string with clear sections for text content and images
    """
    formatted = []
    
    # Add query information
    if 'query' in search_results:
        formatted.append(f"Search Query: {search_results['query']}")
        formatted.append("")
    
    # Add answer if available
    if search_results.get('answer'):
        formatted.append("Answer Summary:")
        formatted.append(search_results['answer'])
        formatted.append("")
    
    # Add text results
    if 'results' in search_results and search_results['results']:
        formatted.append("Text Results:")
        for i, result in enumerate(search_results['results'], 1):
            formatted.append(f"{i}. Title: {result.get('title', 'N/A')}")
            formatted.append(f"   URL: {result.get('url', 'N/A')}")
            formatted.append(f"   Content: {result.get('content', 'N/A')}")
            formatted.append("")
    
    # Add images - This is the crucial part that was missing!
    if 'images' in search_results and search_results['images']:
        formatted.append("Available Images:")
        for i, image in enumerate(search_results['images'], 1):
            formatted.append(f"{i}. URL: {image.get('url', 'N/A')}")
            formatted.append(f"   Description: {image.get('description', 'N/A')}")
            formatted.append("")
    else:
        formatted.append("Available Images: None found")
        formatted.append("")
    
    return "\n".join(formatted)

async def check_image_availability(url: str, timeout: int = 10) -> bool:
    """
    Check if an image URL is accessible and returns a valid response.
    
    Args:
        url (str): The image URL to check
        timeout (int): Request timeout in seconds (default: 10)
    
    Returns:
        bool: True if image is accessible, False otherwise
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(url) as response:
                # Check if status is successful and content-type indicates an image
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    return content_type.startswith('image/')
                return False
    except (aiohttp.ClientError, asyncio.TimeoutError, Exception):
        return False

async def get_first_available_image(image_urls: list) -> str:
    """
    Check each image URL in the list and return the first available one.
    
    Args:
        image_urls (list): List of image URLs to check
    
    Returns:
        str: First available image URL, or empty string if none are available
    """
    if not image_urls:
        return ""
    
    for url in image_urls:
        if await check_image_availability(url):
            return url
    
    return ""

async def get_available_images(image_urls: list, max_images: int = 3) -> list:
    """
    Check image URLs and return up to max_images available ones.
    
    Args:
        image_urls (list): List of image URLs to check
        max_images (int): Maximum number of images to return (default: 3)
    
    Returns:
        list: List of available image URLs (up to max_images)
    """
    if not image_urls:
        return []
    
    available_images = []
    for url in image_urls:
        if len(available_images) >= max_images:
            break
        if await check_image_availability(url):
            available_images.append(url)
    
    return available_images

async def generate_geo_message():
    """
    Generate a geo message about a natural wonder, save it to the database, and return the data.

    Returns:
        GeoMessage: Generated geo message with place, description, and available image URLs.
    """
    
    logger.info("Generating geo message")
    
    try:
        async with AsyncSessionLocal() as session:
            repo = RepositoryFactory(session).get_repository(Geo)
            last_n_obj = await repo.get_last_n(n=NUM_LAST_SEARCH_MSG)
            last_n_places = "\n".join([obj.place for obj in last_n_obj])
    except Exception as e:
        logger.error(f"Failed to fetch previous places: {e}")
        last_n_places = ""

    search_human_prompt = f"Already used: \n {last_n_places}"
    query = await call_llm(search_system_prompt, search_human_prompt, default_response="")
    
    if not query:
        logger.error("Failed to generate search query")
        return default_geo_message()

    logger.info(f"Generated search query: {query}")
    
    try:
        # Use better search parameters
        search_results = await tavily_search(
            query, 
            max_results=8,
            topic="general",  # Use general topic as suggested
            include_images=True,
            include_image_descriptions=True,
            search_depth="basic",  # Try basic first, advanced might be too restrictive
            include_answer=True,  # Get answer for better context
            include_raw_content=False,
            time_range="month"  # Longer time range for better results
        )
        
        # Log the type and content of search_results for debugging
        logger.info(f"Search results type: {type(search_results)}")
        if isinstance(search_results, str):
            logger.warning(f"Search returned string instead of dict: {search_results[:200]}...")
        elif not search_results:
            logger.warning("Search returned empty results")
        else:
            logger.info(f"Search returned dict with keys: {search_results.keys() if isinstance(search_results, dict) else 'N/A'}")
            if isinstance(search_results, dict):
                num_results = len(search_results.get('results', []))
                num_images = len(search_results.get('images', []))
                logger.info(f"Found {num_results} text results and {num_images} images")
                
                # Log first few image URLs for debugging
                if search_results.get('images'):
                    for i, img in enumerate(search_results['images'][:3]):
                        logger.info(f"Image {i+1}: {img.get('url', 'No URL')}")
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        search_results = {}

    # Format the search results properly for the LLM
    formatted_results = format_search_results_for_llm(search_results)
    message_human_prompt = f"Search results from Tavily: \n{formatted_results}"

    # Debug: Log the formatted results to see what's being sent to the LLM
    logger.debug(f"Formatted results for LLM:\n{formatted_results}")

    response = await call_llm_structured(
        message_system_prompt, 
        message_human_prompt, 
        response_model=GeoMessage,
        default_factory=default_geo_message
    )

    # Debug: Log the raw response to see what the LLM returned
    logger.info(f"LLM response: {response}")

    if not response or not response.place or not response.message:
        logger.error("Failed to generate geo message")
        return default_geo_message()
    
    logger.info(f"Generated message for: {response.place}")
    logger.info(f"Initial image URLs: {response.image_url}")

    # Check image availability and get the first available one
    first_available_image = await get_first_available_image(response.image_url)
    
    logger.info(f"First available image: {first_available_image if first_available_image else 'None found'}")

    # Save to database
    logger.info("Saving geo message to database")
    try:
        async with AsyncSessionLocal() as session:
            repo = RepositoryFactory(session).get_repository(Geo)
            await repo.truncate(max_entries=150, keep_entries=50)
            await repo.create(
                place=response.place,
                message=response.message, 
                urls=first_available_image  # Save single URL string
            )
        logger.info("Geo message saved to database")
    except Exception as e:
        logger.error(f"Failed to save geo message: {e}")
    
    # Update response with the single available image for return
    response.image_url = [first_available_image] if first_available_image else []
    
    return response
    
async def main():
    """Main function to demonstrate geo message generation"""
    response = await generate_geo_message()
    print(f"Place: {response.place}")
    print(f"Message: {response.message}")
    print(f"Image: {response.image_url[0] if response.image_url else 'No image available'}")


if __name__ == '__main__':
    asyncio.run(main())