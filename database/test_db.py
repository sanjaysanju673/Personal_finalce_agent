import unittest

from groq import Groq

from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL


@unittest.skipUnless(GROQ_API_KEY, "GROQ_API_KEY is not set")
class GroqConnectivityTests(unittest.TestCase):
    def test_chat_completions_returns_response(self):
        client_args = {"api_key": GROQ_API_KEY}
        if GROQ_BASE_URL:
            client_args["base_url"] = GROQ_BASE_URL

        client = Groq(**client_args)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hello"}],
            model=GROQ_MODEL,
        )

        self.assertIn("hello", response.choices[0].message.content.lower())


if __name__ == "__main__":
    unittest.main()