from langchain_groq import ChatGroq


API_KEY = "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"

def model():
    return ChatGroq(model="openai/gpt-oss-20b", api_key=API_KEY)


print(model().invoke("what is the weather today in kolkata and what is the weather related things tell me all ").content)


