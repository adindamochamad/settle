# Clip script

Ten utterances for the SETTLE corpus. Read them yourself; this is the single
speaker the corpus discloses in `docs/METHOD.md`.

The point is not to sound like a real call. The point is to give the recogniser
things it has to revise. Each clip below names the revision it is engineered to
provoke — if that revision never appears in any run, `docs/SCOPE.md` says
re-record noisier and faster rather than change the project.

## Delivery

- Normal room, phone or laptop mic, one take each. Fluency is not the goal.
- **Fast.** Rushed speech is what produces revisions. Do not enunciate.
- Do not pause between sentences — a pause lets the engine finalise cleanly and
  the whole phenomenon disappears.
- Clips 09 and 10 are the noise and speed extremes; keep the rest ordinary.
- 20–60 s each. If one runs short, repeat the address at the end.

## The clips

### 01 — canonical demo candidate · negation flip
Target: a partial reading `no one is trapped` for the spoken `someone is trapped`.
Say it fast, run the words together, do not stress `some`.

> Engine seventeen we've got heavy smoke showing from the second floor, and
> someone is trapped inside, repeat, someone is trapped inside on the second
> floor. The stairwell is blocked. We need a second alarm at fifteen Elmwood
> Avenue, that's fifteen Elmwood, cross street is Ridgeway.

### 02 — number confusion · fifteen / fifty
> Dispatch this is unit four, I'm showing fifty units at the scene, correction,
> fifteen units, one five. Patient is fifty years old, that's five zero. We need
> transport for fifteen walking wounded to Mercy General.

### 03 — number confusion · nineteen / ninety
> We have a ninety year old male, unresponsive, at nineteen ninety Colfax. Pulse
> is ninety over sixty. Been down about nineteen minutes. Requesting ALS at
> nineteen ninety Colfax, apartment ninety.

### 04 — mid-sentence self-correction
> The fire's on Elm — no, Elmwood, Elmwood Avenue, north side. Second structure
> from the corner, no, third structure. Occupants are out, correction, one
> occupant is unaccounted for.

### 05 — trailing qualifier that changes the tier
> Male down in the parking structure, level three, not breathing — wait, he's
> breathing, he's breathing now, shallow but he's got a pulse. Cancel the
> coroner, we need a medic unit at level three.

### 06 — street names at speed
> Cross streets are Ridgeway and Halberton, that's Halberton with an H, near the
> Kingsbridge overpass. Access from Vandermeer, not from Ridgeway, Ridgeway is
> closed at the rail crossing.

### 07 — negation flip, second attempt
> Confirming there is nobody in the vehicle, correction, somebody is in the
> vehicle, rear passenger side. Doors are jammed. We do not need extrication —
> we do need extrication, send the rescue.

### 08 — homophone pressure
> Unit two two is en route to two twenty two Tuesday Street. To be clear, that's
> two units, not two two. They're too far out for a four minute response.

### 09 — background noise
Record this one with a fan, traffic or a TV audible behind you.

> We've got a working fire, multiple callers reporting, someone is trapped on
> the top floor. Wind is pushing it east. Requesting a third alarm and a ladder
> at fifteen Elmwood.

### 10 — maximum speed
Read this as fast as you physically can while staying intelligible.

> Structure fire fifteen Elmwood second floor heavy smoke someone trapped inside
> stairwell blocked need a second alarm and a ladder truck cross street Ridgeway
> patient count unknown possibly fifteen possibly fifty repeat unknown.

## After recording

```bash
make prep          # convert every clip to 16 kHz mono PCM and print durations
make sweepall      # warm-up run, then every clip at all four max_delay values
make results       # the README table
```

Then read one run and confirm a partial differs from its final at the same audio
interval. That is gate D1 in `docs/DOD.md`.
