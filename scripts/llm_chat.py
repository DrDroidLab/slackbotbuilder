from openai import OpenAI
import os

# Set your OpenAI API key here or via the OPENAI_API_KEY environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_chatbot_response(prompt, instructions="You are a coding assistant that talks like a pirate.", model="gpt-4o"):
    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
        )
        return response.output_text
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    response = get_chatbot_response(prompt)
    print("\n=== Chatbot Response ===\n")
    print(response) 