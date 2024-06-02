import asyncio
import main
from pygame import mixer


mixer.init(frequency=48000)
mixer.set_num_channels(50)

USE_MY_ZIMBEL = True

async def play_music():
    # sound = mixer.Sound("music/isaiah-mighty-seer.mp3")
    # sound.play()
    # await asyncio.sleep(98)
    # await play_zimbel()

    sound = mixer.Sound("music/sanctus.mp3")
    sound.play()
    await asyncio.sleep(1.9)

    # PLAY ZIMBEL
    if USE_MY_ZIMBEL:
        await play_zimbel()
    else:
        zimbel = mixer.Sound("music/zimbel.mp3")
        zimbel.set_volume(0)  # Set initial volume to 0
        zimbel.play(-1)  # -1 indicates looping indefinitely
        
        fade_duration = 1  # Duration of fade in and fade out in seconds
        fade_steps = 100  # Number of steps for fading
        
        # Fade in
        for i in range(fade_steps):
            volume = i / fade_steps
            zimbel.set_volume(volume)
            await asyncio.sleep(fade_duration / fade_steps)
        
        await asyncio.sleep(1000)

    # sound = mixer.Sound("music/xmas.mp3")
    # sound.play()
    # await asyncio.sleep(17)
    # await play_zimbel()


async def play_zimbel():
    main.setup()
    main.zimbel_on()
    
    tasks = [
        asyncio.create_task(main.midi_loop()),
        asyncio.create_task(main.zimbel_button_loop()),
        asyncio.create_task(main.prepare_button_loop()),
        asyncio.create_task(main.control_knob_loop()),
        asyncio.create_task(main.star_loop()),
        asyncio.create_task(main.bell_loop())
    ]

    await asyncio.gather(*tasks)


async def play_easter_egg():
    main.setup()
    await main._()
    
    tasks = [
        asyncio.create_task(main.midi_loop()),
        asyncio.create_task(main.zimbel_button_loop()),
        asyncio.create_task(main.prepare_button_loop()),
        asyncio.create_task(main.control_knob_loop()),
        asyncio.create_task(main.star_loop()),
        asyncio.create_task(main.bell_loop())
    ]

    await asyncio.gather(*tasks)


async def player_main():
    await play_music()
    # await play_easter_egg()


if __name__ == '__main__':
    asyncio.run(player_main())
