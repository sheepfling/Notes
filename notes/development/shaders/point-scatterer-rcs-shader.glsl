// Small ShaderToy-style point-scatterer experiment.
// This is a visualization heuristic, not a calibrated RCS solver.

float dot2(vec2 value) { return dot(value, value); }
vec2 complex_from_phase(float phase) { return vec2(cos(phase), sin(phase)); }

struct PointScatterer {
    vec3 position;
    float amplitude;
};

vec2 point_scatterer_sqrt_rcs(
    vec3 wave_vector,
    PointScatterer scatterer
) {
    // A complex phasor contribution: amplitude * exp(i k dot x).
    return scatterer.amplitude
        * complex_from_phase(dot(scatterer.position, wave_vector));
}

vec2 sum_scatterers(
    vec3 wave_vector,
    PointScatterer scatterers[3]
) {
    vec2 total = vec2(0.0);
    for (int index = 0; index < 3; ++index) {
        total += point_scatterer_sqrt_rcs(wave_vector, scatterers[index]);
    }
    return total;
}

float intensity_from_complex_amplitude(vec2 amplitude) {
    return dot2(amplitude);
}
