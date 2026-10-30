// Exercise the real gallery script with a fake DOM, WebGL and frame scheduler.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(process.argv[2], "utf8");
const pending = new Map();
let nextFrame = 1;
let draws = 0;
const gl = new Proxy({}, {
  get(_target, name) {
    if (name === "drawArrays") return () => { draws += 1; };
    if (name === "getShaderParameter" || name === "getProgramParameter") return () => true;
    if (name === "getAttribLocation") return () => 0;
    if (name.startsWith("create") || name === "getUniformLocation") return () => ({});
    if (name.toUpperCase() === name) return 1;
    return () => {};
  },
});

const elements = new Map();
function element(selector) {
  if (!elements.has(selector)) {
    elements.set(selector, {
      checked: false,
      value: "0.5",
      clientWidth: 100,
      clientHeight: 80,
      listeners: {},
      addEventListener(event, callback) { this.listeners[event] = callback; },
      getContext() { return gl; },
    });
  }
  return elements.get(selector);
}

const context = vm.createContext({
  document: {
    querySelector: element,
    querySelectorAll: () => [],
  },
  window: { devicePixelRatio: 1 },
  performance: { now: () => 100 },
  requestAnimationFrame(callback) {
    const id = nextFrame++;
    pending.set(id, callback);
    return id;
  },
  cancelAnimationFrame(id) { pending.delete(id); },
  // Leave the initial catalog load pending. Explicit selections below resolve.
  fetch(url) {
    if (url === "/__shader_gallery__/shaders") return new Promise(() => {});
    return Promise.resolve({ ok: true, text: async () => "void main() {}" });
  },
});

async function main() {
  vm.runInContext(source, context, { filename: "shader-gallery.js" });
  const point = { name: "Point", path: "projects/shaders/point-scatterer-rcs-shader.glsl", url: "/point.glsl" };
  const other = { name: "Other", path: "other.glsl", url: "/other.glsl" };

  await context.loadShader(point);
  assert.equal(pending.size, 1, "loading a renderer schedules exactly one frame");
  const phase = element("#phase");
  for (let i = 0; i < 5; i += 1) phase.listeners.input();
  assert.equal(draws, 5, "paused slider input redraws each new value");
  assert.equal(pending.size, 1, "slider redraws must not create extra frame loops");

  const [id, callback] = pending.entries().next().value;
  pending.delete(id); // The browser removes a callback before invoking it.
  callback(200);
  assert.equal(draws, 6);
  assert.equal(pending.size, 1, "the owning callback schedules one successor");

  element("#animate").checked = true;
  phase.listeners.input();
  assert.equal(draws, 6, "animated input waits for the owning callback");
  assert.equal(pending.size, 1, "animated input does not schedule another loop");

  await context.loadShader(other);
  assert.equal(pending.size, 0, "switching to an unsupported shader stops the loop");
  phase.listeners.input();
  assert.equal(draws, 6, "a stopped renderer does not draw");

  await context.loadShader(point);
  assert.equal(pending.size, 1, "switching back starts one new loop");
  await context.loadShader(point);
  assert.equal(pending.size, 1, "reselecting the shader replaces the old loop");
  context.stopRenderer();
  assert.equal(pending.size, 0, "stopRenderer cancels the remaining callback");
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
