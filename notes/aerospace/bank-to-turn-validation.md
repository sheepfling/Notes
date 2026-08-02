# Bank-to-turn: validated attitude and maneuver notes

> Type: reference  
> Status: current  
> Updated: 2026-08-01

## Scope

This note is a corrected replacement for an earlier bank-to-turn note. The central correction is that the direction of a velocity vector is not the aircraft’s roll-pitch-yaw orientation. The velocity vector describes the flight path; attitude also depends on the body-to-aerodynamic relationship, including angle of attack and sideslip.

The original source also contained object-replacement characters in place of some equations and symbols, so those literal equations could not be recovered or checked directly.

## Conventions

- NED inertial frame: north, east, down; gravity is (+g) in the down direction.
- Body FRD frame: forward, right, down.
- Euler angles: standard aircraft (3\text{-}2\text{-}1) sequence, with roll (\phi), pitch (\theta), and yaw (\psi).
- Track angle (chi): horizontal direction of travel.
- Flight-path angle (gamma): angle of the velocity vector above the inertial horizontal; positive means climb.
- Ground velocity (\mathbf v_g) and air-relative velocity (\mathbf v_a) are distinct when wind is present.

## What a velocity vector tells us

For NED ground velocity

\[
\mathbf v^n =
\begin{bmatrix}v_N & v_E & v_D\end{bmatrix}^{T},
\]

the horizontal direction is

\[
\chi = \operatorname{atan2}(v_E,v_N).
\]

This is ground track, not necessarily aircraft yaw or heading. Wind, sideslip, angle of attack, and attitude can all make (chi \ne \psi). If the measured velocity is air-relative rather than ground-relative, the resulting angle is an air-relative flight direction instead.

The ground/air relationship is

\[
\mathbf v_g^n = \mathbf v_a^n + \mathbf v_w^n,
\]

where (\mathbf v_w^n) is wind velocity expressed in NED coordinates. The attitude relationship below applies to (\mathbf v_a^n), not directly to ground velocity.

With positive climb, the velocity elevation is

\[
\gamma = \operatorname{atan2}\left(-v_D,\sqrt{v_N^2+v_E^2}\right).
\]

This is flight-path angle, not body pitch. A useful restricted approximation is

\[
\theta \approx \gamma + \alpha,
\]

This approximation also assumes approximately zero sideslip, (\beta \approx 0), and compatible sign conventions. With appreciable sideslip, pitch, flight-path angle, angle of attack, and sideslip are coupled, so the simple sum is not exact. Only when both angle of attack and sideslip are negligible may (\theta \approx \gamma) be used.

During a bank-to-turn entry, attitude can begin changing before the velocity direction changes appreciably. This is one reason velocity-derived track and flight-path angles cannot be used as instantaneous roll and pitch.

## Why velocity alone cannot determine attitude

The air-relative velocity relationship is

\[
\mathbf v_a^n = C_b^n(\phi,\theta,\psi)\,\mathbf v_a^b,
\]

where

\[
\mathbf v_a^b = V_a
\begin{bmatrix}
\cos\alpha\cos\beta\\
\sin\beta\\
\sin\alpha\cos\beta
\end{bmatrix}.
\]

One world-frame velocity vector therefore does not separately determine

\[
\phi,\theta,\psi,\alpha,\beta.
\]

Even if the body (x)-axis is assumed to align perfectly with velocity, rotation about that vector remains arbitrary. Roll is still unobservable from that vector alone.

JSBSim explicitly distinguishes body, aerodynamic, wind, and local NED frames; treating their axes as interchangeable is the source of many apparent formula disagreements.

## Sideslip

Sideslip must use air-relative velocity expressed in body FRD coordinates. If the body-frame components are ([u,v,w]^T), then

\[
\alpha = \operatorname{atan2}(w,u),
\]

\[
\beta = \operatorname{atan2}\left(v,\sqrt{u^2+w^2}\right)
       = \arcsin\left(\frac{v}{V_a}\right).
\]

The lateral component must be body-frame air-relative (v); it is not (v_E), another world-frame component, or uncorrected ground velocity.

## Steady coordinated bank-to-turn equations

For a steady, level, constant-speed, coordinated turn in calm air:

\[
L\cos\phi = mg,
\qquad
L\sin\phi = m\frac{V^2}{R}.
\]

Therefore,

\[
\tan\phi = \frac{V^2}{gR},
\qquad
R = \frac{V^2}{g\tan\phi},
\]

\[
\dot\chi = \frac{g\tan\phi}{V},
\qquad
n = \frac{L}{mg} = \sec\phi.
\]

The inverse estimate is best written with `atan2`:

\[
\boxed{\phi = \operatorname{atan2}(V\dot\chi,g)}
\]

or

\[
\boxed{\phi = \operatorname{atan2}\left(\frac{V^2}{R},g\right)}.
\]

These formulas require the stated steady coordinated-turn assumptions. They are not a general attitude observer.

### Numerical validation

For (V=100\ \mathrm{m/s}) and (phi=30^\circ):

\[
\dot\chi = 3.2440^\circ/\mathrm{s},
\qquad
R = 1766.2\ \mathrm{m},
\]

\[
n = 1.1547,
\qquad
a_{\text{turn}} = g\tan 30^\circ = 5.6619\ \mathrm{m/s^2}.
\]

Substitution into

\[
\operatorname{atan2}(a_{\text{turn}},g)
\]

recovers (30^\circ).

## Acceleration-based force-vector bank estimate

Let kinematic acceleration be

\[
\mathbf a^n = \frac{d\mathbf v^n}{dt},
\qquad
\mathbf g^n = \begin{bmatrix}0 & 0 & g\end{bmatrix}^{T}.
\]

The non-gravitational specific force is

\[
\mathbf f^n = \mathbf a^n - \mathbf g^n.
\]

Remove the component tangent to the measured trajectory:

\[
\hat{\mathbf t} = \frac{\mathbf v^n}{\|\mathbf v^n\|},
\qquad
\mathbf f_\perp = \mathbf f^n -
  (\mathbf f^n\cdot\hat{\mathbf t})\hat{\mathbf t}.
\]

The unit normal-force direction is then

\[
\hat{\mathbf n}_f =
\frac{\mathbf f_\perp}{\|\mathbf f_\perp\|},
\]

when the denominator is nonzero. This produces a trajectory-normal-force direction. It is not automatically the aerodynamic lift direction: in wind, the measured ground-velocity tangent differs from the air-relative velocity tangent, and thrust, drag, side force, and changing airspeed can contribute to the result.

In a level-turn approximation, a force-vector bank magnitude can be estimated from the horizontal normal-force component and its upward component, for example:

\[
|\phi_f| \approx
\operatorname{atan2}\left(
\sqrt{f_{\perp,N}^2+f_{\perp,E}^2},
  -f_{\perp,D}
\right).
\]

This is a trajectory-normal-force or force-vector bank estimate, not automatically Euler roll or aerodynamic lift-vector bank. To estimate aerodynamic lift specifically, use air-relative velocity and separate the aerodynamic force components from thrust and other forces. Thrust vectoring, aerodynamic side force, large angle of attack, and aggressive transients can make the force-vector and Euler-roll angles differ. The sign and reference direction must be chosen consistently with the vehicle and maneuver.

## Roll-rate integration

Integrating roll rate (p) gives roll only under a small-angle, nearly pure-roll approximation. For the standard aircraft (3\text{-}2\text{-}1) Euler convention:

\[
\dot\phi = p + q\sin\phi\tan\theta + r\cos\phi\tan\theta,
\]

\[
\dot\theta = q\cos\phi-r\sin\phi,
\]

\[
\dot\psi = (q\sin\phi+r\cos\phi)\sec\theta.
\]

Thus (\dot\phi\approx p) only when the coupling terms are negligible. For simulation or robust state estimation, propagate the attitude as a quaternion or rotation matrix and use the full body-rate vector ([p,q,r]^T). Euler-angle propagation also becomes ill-conditioned near (\theta=\pm90^\circ).

## Bank-to-turn versus skid-to-turn

In missile and flight-control literature, bank-to-turn (BTT) and skid-to-turn (STT) are steering architectures, not merely descriptions of whether an airplane is accidentally slipping.

- BTT rolls the primary normal-force plane toward the commanded direction, then uses that orientation to produce lateral acceleration.
- STT generates lateral force without first banking the primary force plane into the commanded direction.

Hybrid approaches exist. A skidding airplane and an STT missile may both have sideslip, but the terms describe different control architectures and should not be treated as synonyms.

## Audit table

| Earlier claim                                  | Corrected interpretation                                                              |
|------------------------------------------------|---------------------------------------------------------------------------------------|
| Velocity direction gives roll-pitch-yaw        | Velocity gives track and flight-path direction only.                                  |
| Horizontal velocity angle is yaw               | It is track (chi); wind and sideslip can make (chi\ne\psi).                           |
| Velocity elevation is pitch                    | It is flight-path angle (gamma); pitch also depends on (alpha).                       |
| Roll can be recovered from one velocity vector | Roll is unobservable because rotation about the velocity vector is arbitrary.         |
| Sideslip is the lateral velocity component     | Use body-frame air-relative velocity, not a world-frame or ground-velocity component. |
| Integrating (p) directly gives roll            | Only approximately; use the full Euler-rate equations or quaternion propagation.      |
| Skid-to-turn means an accidental aircraft skid | STT is a control architecture distinct from BTT.                                      |

## References

- [JSBSim frames of reference](https://jsbsim-team.github.io/jsbsim-reference-manual/user/concepts/frames-of-reference/)
- [NASA: Bank-To-Turn Control Technology Survey for Homing Missiles](https://ntrs.nasa.gov/api/citations/19800021773/downloads/19800021773.pdf)
