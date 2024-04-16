import asyncio as asyncio
from pygame import mixer

ZIMBEL_MIN_VOL = 12
ZIMBEL_MAX_VOL = 40

MAPPED_MIN_VOL = 0.05
MAPPED_MAX_VOL = 0.2

mixer.init(frequency=48000)
mixer.set_num_channels(50)

async def play_digital_bell(note, volume=40, testing=False):
    if volume is not None:
        volume = round((volume - ZIMBEL_MIN_VOL) / (ZIMBEL_MAX_VOL - ZIMBEL_MIN_VOL) * (MAPPED_MAX_VOL - MAPPED_MIN_VOL) + MAPPED_MIN_VOL, 2)
    
    print(f"Playing digital bell {note} at volume {volume}")

    sound = mixer.Sound(f"bells/{note}.mp3")
    if volume:
        sound.set_volume(volume)
    sound.play()

    if testing:
        await asyncio.sleep(2)

async def main():
    bells = 'dfgac'
    await play_digital_bell('a', 40, True)
    return
    while True:
        for bell in bells:
            await play_digital_bell(bell, 40, False)
            await asyncio.sleep(0.05)

if __name__ == '__main__':
    asyncio.run(main())
