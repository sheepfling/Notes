const API_PATH = "/__shader_gallery__/shaders";
const POINT_SCATTERER_PATH = "projects/shaders/point-scatterer-rcs-shader.glsl";

const elements = {
  animate: document.querySelector("#animate"),
  canvas: document.querySelector("#shader-canvas"),
  controls: document.querySelector("#controls"),
  indexStatus: document.querySelector("#index-status"),
  list: document.querySelector("#shader-list"),
  phase: document.querySelector("#phase"),
  previewMessage: document.querySelector("#preview-message"),
  renderStatus: document.querySelector("#render-status"),
  shaderCount: document.querySelector("#shader-count"),
  shaderPath: document.querySelector("#shader-path"),
  shaderTitle: document.querySelector("#shader-title"),
  sourceCode: document.querySelector("#source-code code"),
  sourceLink: document.querySelector("#source-link"),
  sourceStatus: document.querySelector("#source-status"),
};

let animationFrame = 0;
let renderer = null;

const vertexSource = `#version 300 es
in vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}`;

// The helper functions below mirror point-scatterer-rcs-shader.glsl. The source file is a
// library rather than a complete fragment shader, so this adapter supplies the WebGL entry point.
const pointScattererFragmentSource = `#version 300 es
precision highp float;

uniform vec2 u_resolution;
uniform float u_time;
uniform float u_phase;
out vec4 outputColor;

float dot2(vec2 value) { return dot(value, value); }
vec2 complex_from_phase(float phase) { return vec2(cos(phase), sin(phase)); }

struct PointScatterer {
  vec3 position;
  float amplitude;
};

vec2 point_scatterer_sqrt_rcs(vec3 wave_vector, PointScatterer scatterer) {
  return scatterer.amplitude * complex_from_phase(dot(scatterer.position, wave_vector));
}

vec2 sum_scatterers(vec3 wave_vector, PointScatterer scatterers[3]) {
  vec2 total = vec2(0.0);
  for (int index = 0; index < 3; ++index) {
    total += point_scatterer_sqrt_rcs(wave_vector, scatterers[index]);
  }
  return total;
}

float intensity_from_complex_amplitude(vec2 amplitude) { return dot2(amplitude); }

void main() {
  vec2 centered = (2.0 * gl_FragCoord.xy - u_resolution) / min(u_resolution.x, u_resolution.y);
  float c = cos(u_phase);
  float s = sin(u_phase);
  vec2 rotated = mat2(c, -s, s, c) * centered;
  vec3 wave_vector = normalize(vec3(rotated * 3.3, 2.4));

  PointScatterer scatterers[3];
  scatterers[0] = PointScatterer(vec3(-0.85, 0.0, -0.15), 1.0);
  scatterers[1] = PointScatterer(vec3(0.0, 0.0, 0.15), 0.8);
  scatterers[2] = PointScatterer(vec3(0.85, 0.0, -0.15), 0.65);

  float intensity = intensity_from_complex_amplitude(sum_scatterers(wave_vector, scatterers));
  float mapped = 1.0 - exp(-0.38 * intensity);
  float glow = smoothstep(0.0, 1.0, mapped);
  vec3 color = mix(vec3(0.015, 0.04, 0.08), vec3(0.08, 0.85, 0.72), glow);
  color += vec3(0.7, 0.35, 0.08) * pow(mapped, 5.0);
  outputColor = vec4(color, 1.0);
}`;

function setStatus(element, text, kind = "") {
  element.textContent = text;
  element.className = `status ${kind}`.trim();
}

function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || "Unknown shader compilation error.";
    gl.deleteShader(shader);
    throw new Error(message);
  }
  return shader;
}

function createRenderer() {
  const gl = elements.canvas.getContext("webgl2", { antialias: true });
  if (!gl) throw new Error("WebGL2 is unavailable in this browser.");

  const vertex = compileShader(gl, gl.VERTEX_SHADER, vertexSource);
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, pointScattererFragmentSource);
  const program = gl.createProgram();
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(gl.getProgramInfoLog(program) || "Unable to link the WebGL program.");
  }

  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, "position");
  const resolution = gl.getUniformLocation(program, "u_resolution");
  const time = gl.getUniformLocation(program, "u_time");
  const phase = gl.getUniformLocation(program, "u_phase");

  return { gl, program, buffer, position, resolution, time, phase };
}

function renderFrame(timestamp) {
  if (!renderer) return;
  const { gl, program, buffer, position, resolution, time, phase } = renderer;
  const width = elements.canvas.clientWidth * window.devicePixelRatio;
  const height = elements.canvas.clientHeight * window.devicePixelRatio;
  if (elements.canvas.width !== width || elements.canvas.height !== height) {
    elements.canvas.width = width;
    elements.canvas.height = height;
  }
  gl.viewport(0, 0, elements.canvas.width, elements.canvas.height);
  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
  gl.uniform2f(resolution, elements.canvas.width, elements.canvas.height);
  gl.uniform1f(time, timestamp * 0.001);
  const automaticPhase = elements.animate.checked ? timestamp * 0.00035 : 0;
  gl.uniform1f(phase, Number(elements.phase.value) + automaticPhase);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}

function draw(timestamp) {
  if (!renderer) return;
  renderFrame(timestamp);
  animationFrame = requestAnimationFrame(draw);
}

function stopRenderer() {
  cancelAnimationFrame(animationFrame);
  renderer = null;
  const gl = elements.canvas.getContext("webgl2");
  if (gl) gl.clearColor(0.03, 0.04, 0.06, 1.0);
}

async function loadShader(item) {
  document.querySelectorAll(".shader-button").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.path === item.path));
  });
  elements.shaderTitle.textContent = item.name;
  elements.shaderPath.textContent = item.path;
  elements.sourceLink.href = item.url;
  elements.sourceStatus.textContent = "Loading";
  elements.sourceCode.textContent = "Loading…";

  try {
    const response = await fetch(item.url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    elements.sourceCode.textContent = await response.text();
    setStatus(elements.sourceStatus, "Source loaded", "ok");
  } catch (error) {
    elements.sourceCode.textContent = `Unable to load source: ${error.message}`;
    setStatus(elements.sourceStatus, "Source error", "warn");
  }

  stopRenderer();
  elements.controls.hidden = true;
  if (item.path !== POINT_SCATTERER_PATH) {
    setStatus(elements.renderStatus, "No adapter", "warn");
    elements.previewMessage.textContent = "This source is listed and readable, but no WebGL preview adapter is registered for it yet.";
    return;
  }

  try {
    renderer = createRenderer();
    elements.controls.hidden = false;
    setStatus(elements.renderStatus, "WebGL2 adapter", "ok");
    elements.previewMessage.textContent = "Previewing the helper library through a small point-scatterer adapter. This is an interference visualization, not calibrated RCS.";
    animationFrame = requestAnimationFrame(draw);
  } catch (error) {
    setStatus(elements.renderStatus, "Preview error", "warn");
    elements.previewMessage.textContent = error.message;
  }
}

function addShaderButton(item) {
  const button = document.createElement("button");
  button.className = "shader-button";
  button.dataset.path = item.path;
  button.setAttribute("role", "option");
  button.setAttribute("aria-selected", "false");
  const name = document.createElement("strong");
  name.textContent = item.name;
  const path = document.createElement("small");
  path.textContent = item.path;
  button.append(name, path);
  button.addEventListener("click", () => loadShader(item));
  elements.list.append(button);
}

async function start() {
  try {
    const response = await fetch(API_PATH);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const shaders = await response.json();
    elements.shaderCount.textContent = `${shaders.length} file${shaders.length === 1 ? "" : "s"}`;
    elements.indexStatus.textContent = "Discovered from notes/ and projects/shaders/";
    shaders.forEach(addShaderButton);
    if (shaders.length > 0) await loadShader(shaders[0]);
  } catch (error) {
    elements.shaderCount.textContent = "Unavailable";
    elements.indexStatus.textContent = "Start the local gallery server to load shaders.";
    setStatus(elements.sourceStatus, "Server unavailable", "warn");
    elements.previewMessage.textContent = `${error.message} Use: uv run python scripts/serve_shader_gallery.py`;
  }
}

elements.phase.addEventListener("input", () => {
  if (!elements.animate.checked && renderer) renderFrame(performance.now());
});
start();
