Controls

A / D: Change lane

Space: Jump

Left Click: Shoot

Right Click: Toggle first-person

C: Cheat mode (auto-aim/jump + avoids moving cube)

F: Toggle camera mode

P: Pause

R: Restart

Features

Endless 3-lane runner with enemies & pickups

Bullets, collisions, hurdles, pillars, moving blockers 

Boost/Slow zones, coins, lives, score multiplier, streak rewards

Dynamic difficulty ramp every 30s

HUD with custom bitmap font 
Snow particle effect

First/third-person camera

Contribution:

Faria Hoque Tazree:

Built the core gameplay loop and state machine controlling player movement, shooting, collisions, scoring, and game flow.

Implemented player controls (lane switching, jumping arc, shooting system with cooldown).

Designed the HUD (score, lives, streak, level, multipliers) and integrated it with game state.

Added collision system for bullets vs enemies, bullets vs obstacles, player vs items, hurdles, and pillars.

Developed Cheat Mode (auto-jump, auto-aim, auto-fire, lane-switch autopilot).

Handled game reset, pause/resume, and Game Over screen logic..

Pushpita Ghosh:

Implemented the tunnel and floor rendering to create the 3D environment.

Added the dynamic snow particle system for visual atmosphere.

Designed and styled the items/pickups (coins, boost cubes, slow strips, life orbs, stars, boost pads).

Tuned the color palette and visuals for HUD, items, and environment consistency.

Mehreen Momtaz:

Handled difficulty ramping: progressive speed increase and spawn rate adjustments every 30s.

Worked on the spawn system for enemies and item rows.

Managed game balancing: adjusting boost/slow durations, enemy speeds, and spawn intervals.

Implemented and tested game over/restart logic and ensured smooth gameplay through playtesting and bug fixes.
