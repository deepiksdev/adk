import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.linkedin_content_agent.agent import root_agent
from google.genai import types as genai_types

# Load environment variables from .env file
load_dotenv()


async def main():
    """Test the LinkedIn content agent."""
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="linkedin_content_agent",
        user_id="test_user",
        session_id="test_session"
    )

    runner = Runner(
        agent=root_agent,
        app_name="linkedin_content_agent",
        session_service=session_service
    )

    # Product information from friland file
    product_info = """
    产品名称：菲乐兰成人配方奶粉 (Friland Adult Formula Milk Powder)

    核心卖点：
    - 新西兰好乳源 (Premium New Zealand milk source)
    - 促进肠道消化吸收 (Promotes intestinal digestion and absorption)
    - 预防三高 (Prevents high blood pressure, blood sugar, cholesterol)
    - 补钙壮骨 (Calcium supplementation and bone strengthening)

    5大特色成分：
    1. 新西兰奶源：黄金优质奶源
    2. 脱盐乳清粉：奶粉中的灵魂，提升乳清蛋白含量且易吸收无负担
    3. 菊粉、聚葡萄糖：调节肠道，促进消化吸收
    4. 初乳碱性蛋白、维生素D、钙：促进钙吸收，延缓骨质疏松，补钙、壮骨
    5. 富含维生素及矿物质
    """

    query = f"Create a promotion poster design in Chinese for my nutrition product with this information: {product_info}. Generate an attractive image suitable for ecommerce webpage."

    print(f"Query: {query}\n")
    print("Response:")
    print("-" * 50)

    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            if event.content and event.content.parts and len(event.content.parts) > 0:
                if hasattr(event.content.parts[0], 'text') and event.content.parts[0].text:
                    print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
