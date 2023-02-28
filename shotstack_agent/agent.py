from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

from tools import change_caption_text, change_caption_color, render_video


code_init = """
import shotstack_sdk as shotstack
import os, sys
import requests
import time

from shotstack_sdk.model.soundtrack  import Soundtrack
from shotstack_sdk.model.image_asset import ImageAsset
from shotstack_sdk.api               import edit_api
from shotstack_sdk.model.clip        import Clip
from shotstack_sdk.model.track       import Track
from shotstack_sdk.model.timeline    import Timeline
from shotstack_sdk.model.output      import Output
from shotstack_sdk.model.edit        import Edit
from shotstack_sdk.model.title_asset import TitleAsset

host = "https://api.shotstack.io/stage"

if os.getenv("SHOTSTACK_HOST") is not None:
    host = os.getenv("SHOTSTACK_HOST")
if os.getenv("SHOTSTACK_KEY") is None:
    sys.exit("API Key is required. Set using: export SHOTSTACK_KEY=your_key_here") 

configuration = shotstack.Configuration(host=host)
configuration.api_key['DeveloperKey'] = os.getenv("SHOTSTACK_KEY")

with shotstack.ApiClient(configuration) as api_client:
    api_instance = edit_api.EditApi(api_client)
    tracks = []

    title_asset = TitleAsset(
        style = "subtitle",
        text  = "test",
        size  = "medium",
        position = "bottom"
    )
"""


if __name__ == "__main__":

    with open('./generated_code.py', 'w') as f: # initialize the code import and ApiClient
        f.write(code_init)

    llm = OpenAI(temperature=0.3)
    tools = [change_caption_text, change_caption_color, render_video] # choose tools based on task

    agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True) # initialize agent
    
    prompt = "Always remember to set the text color using hexadecimal color notation, given query 'color'. \nNow, " 
    query = str(input("QUERY: "))
    
    agent.run(prompt + query)