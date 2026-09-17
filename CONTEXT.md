# waveyard

waveyard is a finite-difference time-domain simulator for photonic
integrated circuits. This is its glossary: the words the spec, the issues,
the lessons, and the code all use for the same things.

## Language

**Structure**:
A single medium occupying a single region of space — one piece of geometry
paired with the material that fills it — together with the precedence that
settles what wins where structures overlap.
_Avoid_: object, geometry, shape

**Plan**:
A simulation reduced to its discrete form, with every physical quantity
already worked out for a fixed grid and a fixed time step. It is the sole
contract between the physics and whatever runs the simulation: nothing
downstream of the plan decides anything physical.
_Avoid_: discretization, grid data, coefficients

**Port**:
A named plane at the edge of a device where guided light enters or leaves,
carrying an outward direction and the description of the modes to excite or
measure there. Ports are what scattering parameters are indexed by, and
each can supply both the excitation and the measurement at its plane.
_Avoid_: terminal, pin, waveguide end

**Monitor**:
A named place in the simulation where a chosen quantity is recorded as the
fields evolve. Monitors are the only reason a run produces anything: what
is not monitored is not observed.
_Avoid_: probe, detector, sensor, output

**Backend**:
The interchangeable executor that takes a plan, advances the fields through
time, and returns what the monitors recorded. Each one declares which
physics it is able to handle, so a backend is allowed to support less than
the model can express.
_Avoid_: engine, solver, device

**State**:
The complete condition of a run at one instant: the electromagnetic fields,
the auxiliary quantities the media and the absorbing boundaries carry along
with them, and what the monitors have accumulated so far. It is everything
the next time step needs and nothing else.
_Avoid_: fields, snapshot
