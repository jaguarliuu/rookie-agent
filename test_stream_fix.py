"""Quick test script to verify streaming fix.

Run this to verify the streaming issue is fixed before running full integration tests.
"""

import os
from dotenv import load_dotenv
from rookie_agent.llm import QwenProvider, DeepSeekProvider, Message, MessageRole

load_dotenv()


def test_qwen_stream():
    """Test Qwen streaming."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY not configured, skipping Qwen test")
        return False

    print("\n🧪 Testing Qwen streaming...")
    try:
        provider = QwenProvider()
        messages = [Message(role=MessageRole.USER, content="数1到3")]

        print("📡 Streaming response: ", end='', flush=True)
        chunks = []
        for chunk in provider.stream(messages):
            content = chunk.get_content()
            if content:
                print(content, end='', flush=True)
                chunks.append(content)

        print(f"\n✅ Qwen streaming worked! Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"\n❌ Qwen streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deepseek_stream():
    """Test DeepSeek streaming."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not configured, skipping DeepSeek test")
        return False

    print("\n🧪 Testing DeepSeek streaming...")
    try:
        provider = DeepSeekProvider()
        messages = [Message(role=MessageRole.USER, content="数1到3")]

        print("📡 Streaming response: ", end='', flush=True)
        chunks = []
        for chunk in provider.stream(messages):
            content = chunk.get_content()
            if content:
                print(content, end='', flush=True)
                chunks.append(content)

        print(f"\n✅ DeepSeek streaming worked! Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"\n❌ DeepSeek streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Testing Streaming Fix")
    print("=" * 60)

    results = []
    results.append(("Qwen", test_qwen_stream()))
    results.append(("DeepSeek", test_deepseek_stream()))

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")

    all_passed = all(passed for _, passed in results if passed is not False)
    if all_passed:
        print("\n🎉 All streaming tests passed! You can now run full integration tests.")
    else:
        print("\n⚠️ Some tests failed. Check error messages above.")
