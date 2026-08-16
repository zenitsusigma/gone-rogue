# Gone Rogue

An isometric top-down roguelite shooter where you fight your way up a skyscraper which is a corporate office, dodging clipboard-throwing middle managers and zombie-like workers, with executives who summon more of them, until you can unlock the elevator and ascend higher!

**Made for the MACONDO !!**

## Why I made this

I made this game for my Y10 computing technology assessment task, because I wanted to make a pretty cool game, and back at daydream I tried to make a dungeon roguelite but I kinda miserable failed, so this is a less miserable failure as it actually works! But anyways, I wanted to invert the concept of a dungeon roguelite - instead of going down into a dungeon you're going UP into a skyscraper!!! This is like pretty cool and modernises the concept a lot.

## What it does

- Move with WASD or arrow keys, aim and fire with the mouse or Space
- Switch between pistol (2) and rifle (3)
- Three enemy types with different behavior: workers (zombies), middle managers (throwers), and executives (summoners)
- Each floor is procedurally laid out and you have to find and unlock the elevator (e) to go uppies!
- Full directional animation set (front/back/side/idle/run/fire/death) for the player and slightly smaller for every enemy type

## How to run it

1. Install [Python (click here)](https://www.python.org/) and pygame:
   ```
   pip install -r requirements.txt
   ```
2. Run the game:
   ```
   python main.py
   ```
3. Controls: WASD/arrows to move, Space or left-click to fire, 2/3 to switch weapons, e to open the elevator, esc to quit.

## What I'd change next

If I had 4 more weeks to develop this game, I would focus on adding actual progression to the game, removing its current puzzle-like structure like implementing the lootbox system I built sprites for. I would also revisit my art assets to bring them to a more consistent style since they were made over separate sessions and some were scrapped and because of this, inconsistency crept in which I could fix!

## Credits

Built from the starter scaffold provided for my school's Computing Technology course (basic PyGame setup). All game logic, enemy AI, animation system, level generation, and art direction beyond that starting scaffold are my own.

## License

MIT [LICENSE (click here)](LICENSE).