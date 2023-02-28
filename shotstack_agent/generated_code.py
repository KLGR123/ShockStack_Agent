
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

    title_asset.text = 'hello hello test'

    
    title_asset.color = '#0000FF'

    

    title_track = Clip(
        asset  = title_asset,
        start  = 0.0,
        length = 5.0,
        effect = "zoomIn"
    )

    title_track = Track(clips=[title_track])
    tracks.append(title_track)

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
    
        print(f"\n{message}\n")
        # print(f">> Now check the progress of your render by running function with {id}:")
        # print(f">> python examples/status.py {id}")

        if id is None:
            sys.exit(">> Please provide the UUID of the render task (i.e. python examples/status.py 2abd5c11-0f3d-4c6d-ba20-235fc9b8e8b7)")  

        try:
            while True:
                api_response = api_instance.get_render(id, data=False, merged=True)
                status = api_response['response']['status']

                print('Status: ' + status.upper() + '\n')

                if status == "done":
                    url = api_response['response']['url']
                    print(f">> Asset URL: {url}\n")

                    r = requests.get(url)
                    with open('./render/video.mp4', 'wb') as f:
                        f.write(r.content)
                    break

                elif status == 'failed':
                    # print(">> Something went wrong, rendering has terminated and will not continue.\n")
                    break
                else:
                    # print(">> Rendering in progress, please try again shortly. >> Note: Rendering may take up to 1 minute to complete.\n")
                    time.sleep(10)

        except Exception as e:
            print(f"Unable to resolve API call: {e}") 

    except Exception as e:
        print(f"Unable to resolve API call: {e}")
    