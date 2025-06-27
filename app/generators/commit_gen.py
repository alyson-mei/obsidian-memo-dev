import random
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.llm import call_llm_structured
from app.services.part_of_day import get_part_of_day_description
from app.data.repository import RepositoryFactory
from app.data.models import Commit
from app.data.database import AsyncSessionLocal
from app.config import NUM_LAST_COMMIT_MSG, NUM_NEW_COMMIT_MSG
from app.config import setup_logger

logger = setup_logger("commit_generator", indent=4)

message_examples = [
    "a shelf of tiny improvements 📚",
    "thunder in the distance, backups here and now 🌩️📦",
    "tea steam, mind clear 🍵",
    "bookmarking the mood 🖇️🌙",
    "misty sync at morning's edge 🌫️",
    "drizzle tapping gently on the code window 🌧️💻",
    "folding thoughts like fresh linen 🧺🧠",
    "golden hour and markdown glow 🌇",
    "one sigh, one sync 💭",
    "tending the digital garden 🌱🧑‍🌾",
    "line by line under Icelandic skies 🇮🇸💨",
    "soft save echoing in a redwood grove 🌲",
    "committing from a cabin by Lake Baikal 🏕️🌊",
    "slow sync on the rings of Saturn 🪐",
    "auroras flicker, thoughts align ❄️✨",
    "soft-spoken commit from a quiet place 🫖",
    "late spring sun and a finished thought ☀️🌱",
    "coding like it's a Ghibli kitchen scene 🍲",
    "snow-dusted sync beneath dim light 🌨️🕯️",
    "cool breeze, warm repo 🍃🔥",
    "twilight edits with Olafur Arnalds in the background 🎹🌆",
    "threading calm into code 🧵",
    "autumn's breath and structured lines 🍁📐",
    "cozy lofi and smoother markdowns 🎶",
    "one quiet update beneath Himalayan light 🏔️🧘",
    "moonlit push from Crater Lake 🌕🌌",
    "crisp air, clean commits 🍂",
    "bookmarking memories in README format 📖📄",
    "pages turned, updates saved 📖",
    "just syncing under Totoro's umbrella 🌂🌳",
    "clouds drift, ideas settle ☁️🪺",
    "a line of thought preserved 📎",
    "after the rain, a clean commit 🍃💾",
    "tidy thoughts wrapped in a ribbon 🎀📝",
    "winter hush and one tidy save ❄️",
    "late shift energy, like a VA-11 HALL-A bartender 🍸🌃",
    "saving progress like Snake in a cardboard box 📦🐍",
    "quiet commit with Stardew Valley vibes 🌾🎧",
]

class CommitMessage(BaseModel):
    message: str = Field(
        description="A concise, friendly commit message with emojis (max 10 words)"
    )

class CommitMessageBatch(BaseModel):
    messages: List[CommitMessage] = Field(
        description=f"List of {NUM_NEW_COMMIT_MSG} unique, creative commit messages",
        min_items=NUM_NEW_COMMIT_MSG,
        max_items=NUM_NEW_COMMIT_MSG * 2
    )

def get_default_commit_messages(count: int = NUM_NEW_COMMIT_MSG) -> List[str]:
    """Default factory: return random example messages when generation fails."""
    logger.info(f"Using default factory to get {count} commit messages")
    return random.sample(message_examples, min(count, len(message_examples)))

async def get_recent_commits() -> str:
    """Get recent commit messages, return empty string on failure."""
    try:
        async with AsyncSessionLocal() as session:
            repo = RepositoryFactory(session).get_repository(Commit)
            last_n_obj = await repo.get_last_n(n=NUM_LAST_COMMIT_MSG)
            return "\n".join([obj.message for obj in last_n_obj])
    except Exception as e:
        logger.warning(f"Failed to get recent commits: {e}")
        return ""

async def generate_commit_messages_batch(weather_data: dict, count: int = NUM_NEW_COMMIT_MSG) -> List[str]:
    """Generate commit messages using LLM, fallback to default on failure."""
    
    try:
        now = datetime.now()
        part_of_day = get_part_of_day_description(now.hour)
        last_n_msg = await get_recent_commits()
        
        logger.info(f"Generating {count} commit messages with LLM")
        
        example_messages = "\n".join([f"- {msg}" for msg in message_examples])
        
        system_prompt = f"""
        You are a creative assistant helping generate unique, expressive commit messages for a code repository.

        ## Your Thought Process Before Generating (MUST follow this for every message):

        1. **Pick the focus**:
        - For half of the messages: base them on weather or time of day.
        - For the other half: focus on internal themes (mood, memory, rhythm of work, poetic reflection).

        2. **Choose an emotional tone**:
        - Vary tones across the list: calm, cozy, playful, melancholy, light-hearted, introspective, or even whimsical.

        **Draw inspiration from anywhere — high or low**:
        - Before writing each message, pause and imagine a source of inspiration.
        - It can be anything: a film scene, a game atmosphere, a song lyric, a fleeting emotion, the color of morning light, the way tea steam curls in winter air, or even a recent thought or memory.
        - Use this inspiration to shape the tone, metaphor, or sensory details of the message — subtly or directly.
        - You can skip this step if inspiration is abstract or internal (e.g. "quiet focus", "melancholy").

            Important:
            - Don't just steal ideas from examples - think for yourself!
            - At least **a few messages must include clear and recognizable references**.
            - These can refer to:
            - specific games (e.g. *VA-11 HALL-A*, *Metal Gear Solid*, *Stardew Valley*),
            - films or visual moments (e.g. *Ghibli*, *Blade Runner*, *Amélie*),
            - songs or musical moods (e.g. lofi, post-rock, jazz piano),
            - real places (e.g. Iceland, redwood forests, Lake Baikal),
            - imagined or cosmic locations (e.g. Saturn's rings, auroras, lunar plains).
            - References should feel intentional, not generic — they add flavor, personality, and emotional context to the message.

        4. **Decide on structure and size**:
        - Most messages should be short (under 10 words).
        - But allow for occasional slightly longer ones, if they carry vivid imagery.
        - Always use natural rhythm and flow.

        5. **Include emojis**:
        - Each message must have one or two emojis.
        - Choose emojis that reinforce the tone, not just literal meanings.

        6. **Check for uniqueness**:
        - Compare with {last_n_msg} and ensure messages are completely distinct.
        - Don't repeat patterns or themes too often.
        
        Examples of good commit messages:
        {example_messages}
        
        Context:
        * Part of day: {part_of_day}
        * Weather data: {weather_data}
        * Current datetime: {now.strftime('%Y-%m-%d %H:%M:%S')}
        * Recent commit messages to avoid: {last_n_msg}
        
        IMPORTANT RULES:
        - Generate at least {count} messages.
        - All messages must be completely unique.
        - Don't repeat themes from recent commits.
        - Half of the messages should mention weather/time, half of messages shouldn't.
        - Be creative and vary the emotional tone and length of the message.
        - Each message should feel fresh and different.
        - Do not place dots in the end of the messages.
        """

        human_prompt = f"""
        Generate at least {count} unique, creative commit messages.
        Ensure variety in themes, emojis, and emotional tones.
        Avoid repetition of recent commit patterns.
        """

        response: Optional[CommitMessageBatch] = await call_llm_structured(
            system_prompt, 
            human_prompt, 
            response_model=CommitMessageBatch
        )
        
        if response and response.messages:
            messages = [msg.message for msg in response.messages]
            logger.info(f"Successfully generated {len(messages)} commit messages")
            return messages
        else:
            logger.warning("LLM returned empty response")
            return get_default_commit_messages(count)
            
    except Exception as e:
        logger.error(f"Failed to generate commit messages: {e}")
        return get_default_commit_messages(count)

async def save_commit_messages_batch(messages: List[str]) -> bool:
    """Save commit messages to database in a single batch."""
    if not messages:
        logger.warning("No messages to save")
        return False

    try:
        async with AsyncSessionLocal() as session:
            repo = RepositoryFactory(session).get_repository(Commit)
            await repo.truncate(max_entries=150, keep_entries=50)
            objs = [Commit(message=msg) for msg in messages]
            await repo.create_many(objs)
        logger.info(f"Successfully saved {len(messages)} commit messages (batch)")
        return True
    except Exception as e:
        logger.error(f"Failed to save commit messages: {e}")
        return False

async def generate_and_save_commit_messages(weather_data: dict, count: int = NUM_NEW_COMMIT_MSG) -> List[str]:
    """Generate and save commit messages. Always returns messages (uses default factory on failure)."""
    logger.info(f"Starting commit message generation and save process")
    
    messages = await generate_commit_messages_batch(weather_data, count)
    
    if messages:
        save_success = await save_commit_messages_batch(messages)
        if save_success:
            logger.info("Commit messages generated and saved successfully")
        else:
            logger.warning("Commit messages generated but failed to save")
    else:
        logger.error("No commit messages generated")
    
    return messages

# Demonstration
async def main():
    """Demonstration of the commit message generator."""
    
    # Mock weather data
    weather_data = {
        "temperature": 22,
        "condition": "partly cloudy",
        "humidity": 65,
        "wind_speed": 5
    }
    
    print("=== Commit Message Generator Demo ===")
    print(f"Weather: {weather_data}")
    print(f"Generating {NUM_NEW_COMMIT_MSG} commit messages...\n")
    
    messages = await generate_and_save_commit_messages(weather_data)
    
    print("Generated messages:")
    for i, message in enumerate(messages, 1):
        print(f"{i:2d}. {message}")
    
    print(f"\n✅ Generated {len(messages)} commit messages")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())