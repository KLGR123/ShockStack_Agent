from langchain.agents import tool


@tool("change_caption_text")
def change_caption_text(query: str) -> str:
    """change the subtitle's context to 'query'."""

    generated = f"""
    title_asset.text = {query}

    """

    with open('generated_code.py', 'a') as f:
        f.write(generated)

    
    return None
    # return f"caption text changed to {query}. Need to change its color next."


@tool("change_caption_color")
def change_caption_color(query: str) -> str:
    """change the subtitle's color to the color 'query'."""

    generated = f"""
    title_asset.color = {query}

    """

    with open('generated_code.py', 'a') as f:
        f.write(generated)
    
    return None
    # return f"caption color changed to {query}."


@tool("trim_video")
def trim_video(query: str) -> str:
    """trim the video to 'query' seconds."""

    generated = f"""
    video_asset.trim = {query}

    """

    with open('generated_code.py', 'a') as f:
        f.write(generated)
    
    return None


@tool("add_transition")
def add_transition(query: str) -> str:
    """add a 'query' transition at the end,for example fade"""

    generated = f"""
    transition = Transition(
        out = "{query}"
    )

    """

    with open('generated_code.py', 'a') as f:
        f.write(generated)
    
    return None

@tool("render video")
def render_video(query: str) -> str:
    """rendering the video finally."""

    edit_prompt = """

    title_track = Clip(
        asset  = title_asset,
        start  = 0.0,
        length = 5.0,
        effect = "zoomIn"
    )

    video_clip_track = Clip(
        asset  = video_asset,
        start  = 0.0,
        length = 5.0,
        transition = transition
    )

    title_track = Track(clips=[title_track])
    video_clip_track = Track(clips=[video_clip_track])

    tracks.append(title_track)
    tracks.append(video_clip_track)

    timeline = Timeline(
        background = "#000000",
        tracks     = tracks
    )

    output = Output(
        format     = "mp4",
        resolution = "sd"
    )

    edit = Edit(
        timeline = timeline,
        output   = output
    )

    try:
        api_response = api_instance.post_render(edit)

        message = api_response['response']['message']
        id = api_response['response']['id']
    
        print(f"\\n{message}\\n")
        # print(f">> Now check the progress of your render by running function with {id}:")
        # print(f">> python examples/status.py {id}")

        if id is None:
            sys.exit(">> Please provide the UUID of the render task (i.e. python examples/status.py 2abd5c11-0f3d-4c6d-ba20-235fc9b8e8b7)")  

        try:
            while True:
                api_response = api_instance.get_render(id, data=False, merged=True)
                status = api_response['response']['status']

                print('Status: ' + status.upper() + '\\n')

                if status == "done":
                    url = api_response['response']['url']
                    print(f">> Asset URL: {url}\\n")

                    r = requests.get(url)
                    with open('./render/video.mp4', 'wb') as f:
                        f.write(r.content)
                    break

                elif status == 'failed':
                    # print(">> Something went wrong, rendering has terminated and will not continue.\\n")
                    break
                else:
                    # print(">> Rendering in progress, please try again shortly. >> Note: Rendering may take up to 1 minute to complete.\\n")
                    time.sleep(10)

        except Exception as e:
            print(f"Unable to resolve API call: {e}") 

    except Exception as e:
        print(f"Unable to resolve API call: {e}")
    """

    with open('./generated_code.py', 'a') as f:
        f.write(edit_prompt)

    with open('./generated_code.py', 'r') as f:
        code = f.read()
        exec(code)

    return None

    



