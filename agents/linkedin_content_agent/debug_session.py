
from google.adk.sessions import InMemorySessionService
import asyncio
import inspect

async def main():
    print("Inspecting InMemorySessionService...")
    s = InMemorySessionService()
    
    print(f"create_session sig: {inspect.signature(s.create_session)}")
    try:
        print(f"get_session sig: {inspect.signature(s.get_session)}")
    except AttributeError:
        print("get_session method NOT found")

    if hasattr(s, 'sessions'):
        print(f"s.sessions type: {type(s.sessions)}")
        print(f"s.sessions content: {s.sessions}")

    try:
        res = s.create_session("app", "user", "sess")
        if asyncio.iscoroutine(res):
            await res
            print("create_session is ASYNC")
        else:
            print("create_session is SYNC")
    except Exception as e:
        print(f"create_session failed: {e}")

    try:
        res = s.get_session("sess")
        if asyncio.iscoroutine(res):
            sess = await res
            print("get_session is ASYNC")
        else:
            sess = res
            print("get_session is SYNC")
        
        # Check if we can access state
        if hasattr(sess, 'state'):
           print(f"Session state available: {sess.state}")
           
    except Exception as e:
        print(f"get_session failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
