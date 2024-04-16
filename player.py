import asyncio
import main
from pygame import mixer


mixer.init(frequency=48000)
mixer.set_num_channels(50)


async def play_music():
    sound = mixer.Sound("music/isaiah-mighty-seer.mp3")
    sound.play()
    await asyncio.sleep(98)
    await play_zimbel()

    # sound = mixer.Sound("music/sanctus.mp3")
    # sound.play()
    # await asyncio.sleep(1.9)
    # await play_zimbel()

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
