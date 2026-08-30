# Rules Reference v1.8 Timing Play Lab

These checkpoints exercise the source checkout's `v18_timing` dispatcher with real cards and complete game workflows. Every JSON file explicitly enables `v18_timing`; none use legacy timing.

## Loading a checkpoint

1. Start the local server from the repository root with `.venv\Scripts\python.exe main.py`.
2. Open the game, choose **Replay**, and select a file from `v18_timing`.
3. For `01` and `02`, advance the replay to its recorded endpoint. It stops inside the important response window.
4. Files `03` through `16` are puzzle-style labs. They open at a stable player action with an exact hand and encounter-deck fixture.
5. For the setup commands below, load the game with debug enabled (add `&debug` to the game URL), open the debug command field, and enter one `Puzzle.` command at a time.

Reload the JSON before trying a different branch. Use card IDs in commands where names have duplicate printings.

The generator and checksum validator are:

```powershell
.venv\Scripts\python.exe v18_timing_harness.py --write --validate
```

## Checkpoints

### 01 — Nova unlocks Jarnbjorn

No debug setup is needed. At the recorded response window, Jarnbjorn is visible but disabled because it has no payable physical resource. Choose Nova's response and target Supernova Helmet. The Helmet readies, the response window is recalculated, and Jarnbjorn becomes payable from the newly available Helmet resource without closing the occurrence.

Expected: Nova and Jarnbjorn each resolve no more than once; the Helmet is ready after Nova resolves; the prompt does not jump to a later attack window.

### 02 — Nova and Jarnbjorn are both legal

No debug setup is needed. Nova and Jarnbjorn are both legal at the first response prompt. Try both branches by reloading:

- Nova first, then Jarnbjorn.
- Jarnbjorn first, paying with Strength, then Nova.

Expected: either order remains legal and uses distinct timing-choice identities.

### 03 — Defensive Conditioning constants

```text
Puzzle.PutIntoPlay("56046")
Puzzle.ChangeFormFor(0, "Hero")
```

Expected: no ordering prompt appears. Stephen Strange has +3 maximum HP, and Doctor Strange has +1 DEF. Both constant modifiers apply automatically as one state update.

### 04 — Unuscione forced ordering

```text
Puzzle.PutIntoPlay("32159")
Puzzle.Reveal("32163")
```

Expected: the first player chooses between Teamwork and Toughness. Choose either first; Teamwork makes Unuscione scheme once, Toughness gives one tough status, and each resolves exactly once.

### 05 — cancel Surge and Incite

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.Reveal("01191")
```

Play Enhanced Spider-Sense and pay with an Energy card. Then run:

```text
Puzzle.Reveal("04069")
```

Use the second Enhanced Spider-Sense and the second Energy.

Expected: canceling Exhaustion's When Revealed effect also cancels Surge, so Spider-Man is not exhausted and no extra encounter card is revealed. Canceling Raid the Armory also cancels Incite, so it places no threat and does not search for a Weapon.

### 06 — nested reveal attack and defense

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.Reveal("01186")
```

Play Get Behind Me! and pay with Energy. Resolve Spider-Sense, then choose whether to defend the nested Rhino attack.

Expected: Advance is canceled, Rhino's attack and all attack/defense windows finish as a child occurrence, and only then does the encounter reveal resume and discard Advance. Advance places no threat and no attack candidates leak into the parent reveal.

### 07 — keyword priority lab

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.PutIntoPlay("03009")
Puzzle.Reveal("01167")
```

Vulture's Quickstrike is a mandatory Forced Response after engagement. Continue with:

```text
Puzzle.PutIntoPlay("33005")
Puzzle.Reveal("16183")
```

Attach Exploit Weakness to an enemy when prompted. End the player phase and allow Badoon Headhunter to activate.

Expected: Restricted checks after the Shield enters play, Quickstrike resolves at Forced Response priority, Badoon Headhunter receives a boost card through Villainous when it activates, and Exploit Weakness is discarded by Temporary at round end.

### 08 — Tough, Piercing, and Vulnerable

Tough plus Quickstrike:

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.Tough("01001a")
Puzzle.Reveal("60182")
```

Leave Cop's Quickstrike undefended. Tough replaces the damage and is discarded. Then run:

```text
Puzzle.Stun("60182")
```

Expected: Vulnerable discards Cop as a Forced Interrupt before stun is placed; no stunned card remains out of play.

For Piercing, reload, reveal Cop, give Cop tough with `Puzzle.Tough("60182")`, and play Piercing Strike (`04044`) targeting Cop. Expected: Piercing removes tough before the 3 damage defeats Cop.

### 09 — Retaliate and Ranged

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.PutIntoPlay("04020")
Puzzle.PutIntoPlay("01172")
```

First make Iron Man's ordinary basic attack against Whiplash. Then make War Machine's basic attack against Whiplash.

Expected: Whiplash's Retaliate deals 1 to Iron Man after the ordinary attack. War Machine gains Ranged during its attack and does not suffer Retaliate. War Machine's starting tough instead prevents its consequential damage.

### 10 — Martyr and consequential damage

```text
Puzzle.PutIntoPlay("19012")
Puzzle.PutIntoPlay("01167")
Puzzle.Damage("01167", 2)
```

Attack Vulture with Martyr.

Expected: Vulture is defeated, attack/defeat responses finish, Martyr then takes 1 consequential damage, and only afterward Martyr's Response can give her tough. Final Martyr state: 2 HP and tough.

### 11 — Thor overkill response window

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.PutIntoPlay("06009")
Puzzle.PutIntoPlay("06019")
Puzzle.PutIntoPlay("06018")
Puzzle.PutIntoPlay("01167")
Puzzle.Exhaust("06001a")
Puzzle.SetThreat("01097b", 2)
```

Thor is deliberately exhausted so Battle Fury has a legal ready target. Play Hammer Throw, exhaust Mjolnir for its printed additional cost, pay with Energy/Genius, and target Vulture. Strength remains available for Jarnbjorn.

Expected: Hammer Throw defeats Vulture and assigns overkill damage to Rhino before the optional response choices. The first response chooser contains Jarnbjorn, Battle Fury, and Chase Them Down together. Any of the three can be selected first, and each resolved ability is offered only once.

### 12 — indirect/divided damage

```text
Puzzle.PutIntoPlay("04020")
Puzzle.PutIntoPlay("19012")
Puzzle.Reveal("29040")
```

Zzzap! asks you to assign exactly 4 damage. A useful branch is 1 to War Machine and 3 to Martyr.

Expected: War Machine's tough prevents its assigned point and is discarded; Martyr takes 3 and is defeated. The complete damage occurrence retains both target records, and no timing occurrence remains open afterward.

### 13 — basic thwart and side-scheme defeat

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.PutIntoPlay("04047")
Puzzle.Reveal("16127")
Puzzle.SetThreat("16127", 2)
```

Use Captain Marvel's basic thwart on Hujahdarian Monarch Egg. At the forced-order prompt, try When Defeated before Victory, then accept the ready choice and use Skilled Investigator.

Expected: Captain Marvel readies, the Egg moves to the victory display/removes from play without losing its effect, Skilled Investigator exhausts and draws one card, and the basic-thwart occurrence closes cleanly.

### 14 — recovery response window

```text
Puzzle.PutIntoPlay("44008")
Puzzle.Damage("30001b", 2)
```

Make Peter Porker's basic recovery. Reload and try both response orders:

- Chimichanga Truck first, then Cartoon Power.
- Cartoon Power first, then Chimichanga Truck.

Expected: both responses share the recovery occurrence. Final state is Peter Porker ready with one toon counter and Chimichanga Truck exhausted.

### 15 — scheme lifecycle

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.Reveal("16178a")
Puzzle.SetThreat("16178a", 2)
```

Basic thwart Badoon Blitz. Resolve its When Defeated and Victory effects, and choose to draw. Then run:

```text
Puzzle.SetThreat("02004b", 7)
```

Expected: Badoon Blitz enters the victory display after its draw effect. Hostile Takeover's When Completed adds one infamy to Criminal Enterprise and discards the correct number of deck cards before advancing to Corporate Acquisition.

### 16 — multiplayer response priority

```text
Puzzle.ChangeFormFor(0, "Hero")
Puzzle.ChangeFormFor(1, "Hero")
Puzzle.PutIntoPlayFor(0, "04047")
Puzzle.PutIntoPlayFor(1, "04047")
Puzzle.Reveal("16127")
Puzzle.SetThreat("16127", 2)
```

Player 1 (Captain Marvel) basic thwarts the Egg. Decline or resolve its ready choice, then use both Skilled Investigators.

Expected: response opportunities begin with the first player and rotate one at a time: Captain Marvel's Skilled Investigator, then Spider-Man's. Both exhaust and each controller draws one card. The window closes only after all active players have no response or pass consecutively.

## Automated coverage

The real-card integration tests are in `unit_test/test_v18_timing_integration.py`. The dispatcher, replay-identity, failure, keyword, and legacy-mode edge cases remain in `unit_test/test_v18_timing.py` and `unit_test/test_v18_keyword_timing.py`.

Run the focused suite with:

```powershell
.venv\Scripts\python.exe -m unittest unit_test.test_v18_timing unit_test.test_v18_keyword_timing unit_test.test_v18_timing_integration
```
