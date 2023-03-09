from langchain.agents import load_tools, Tool
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain.llms import PromptLayerOpenAI

from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import LLMChain

from tools import text_agent, subtitle_agent, video_agent, image_agent, timeline_config_agent, output_config_agent, render_video

# https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/footage/skater.hd.mp4
# https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/examples/picture-in-picture/code.mp4
# https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/examples/picture-in-picture/commentary.mp4

# https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/examples/images/pexels/pexels-photo-712850.jpeg
# https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/examples/images/pexels/pexels-photo-867452.jpeg
# https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/examples/images/pexels/pexels-photo-752036.jpeg


if __name__ == "__main__":

    subagent_tools = [
        Tool(
            name = "text_agent",
            func=text_agent.run,
            description="Use when doing video editing that requires manipulation of text elements, such as changing text color, etc."
        ),
        Tool(
            name = "subtitle_agent",
            func=subtitle_agent.run,
            description="Use when doing video editing that requires manipulation of subtitle element, such as changing subtitle time, etc."
        ),
        Tool(
            name = "video_agent",
            func=video_agent.run,
            description="Use when doing video editing that requires manipulation of videos, such as trimming video, etc."
        ),
        Tool(
            name = "image_agent",
            func=image_agent.run,
            description="Use when doing video editing that requires manipulation of images, such as adding image transition, etc."
        ),
        Tool(
            name = "timeline_config_agent",
            func=timeline_config_agent.run,
            description="Use when doing video editing that requires manipulation of timeline configuration, such as adding timeline soundtrack, etc."
        ),
        Tool(
            name = "output_config_agent",
            func=output_config_agent.run,
            description="Use when doing video editing that requires manipulation of output configuration, such as changing output quality, etc."
        ),
    ]

    tools = subagent_tools + [render_video]

    prefix = """You are an agent operating a video editing online site, and you need to use the tools in sequence according to the objective as best you can.
    If the objective cannot be achieved by using the tools, or the objective is not related to the video editing task, directly return the final answer 'I don't know.'
    When you add transition to video, use the video_agent. When you add transition to image, use the image_agent.
    You have access to the following tools: """

    suffix = """Now, begin.

    {chat_history}
    Objective: {input}
    {agent_scratchpad}"""

    prompt = ZeroShotAgent.create_prompt(
        tools, 
        prefix=prefix, 
        suffix=suffix, 
        input_variables=["input", "chat_history", "agent_scratchpad"]
    )

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm = PromptLayerOpenAI(temperature=0, pl_tags=["shotstack_agent"])
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # agent = initialize_agent(tools, llm, agent="conversational-react-description", verbose=True)
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory)


    # query = """first add a video from url 'https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/examples/picture-in-picture/code.mp4', make it start from 3 sec and end at 7 sec, and name it 'code'. Then add a text with content 'Coding Forever', and let it begin at 0 and end at 7 sec, and change this text's background color to light purple. Also, add a 'zoom' transition in the beginning of that video 'code', and finally render it."""
    # query = """can you upload a video from 'https://shotstack-assets.s3.ap-southeast-2.amazonaws.com/examples/picture-in-picture/commentary.mp4', trim it starting from 12 sec. For subtitle, first change its word to 'buffalo buffalo buffalo', then its color to dark purple, and adjust its start time to 1 sec and last for 1 sec there. For the text in video, write as 'Handsome Man'. And about the image please crop half of its left and a quarter of its bottom, and give a reveal transition to it. Finally, render the video."""
    query = "add a video from url https://s3-ap-southeast-2.amazonaws.com/shotstack-assets/footage/skater.hd.mp4, make it start from 0 sec and last for 5 sec, and name it 'skator'. Then add a text with content 'Sport Time', and let it begin at 0 and end at 7 sec."
    query += " then render the video."
    agent_chain.run(input=query)

    # base_prompt = f"""Now, the objective is: {query}"""
    # agent.run(base_prompt)

    while True:
        query = input("QUERY: ")
        if query == 'quit':
            break
        else:
            query += " then render the video."
            agent_chain.run(input=query)
