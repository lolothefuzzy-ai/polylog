# Engine Subsystem Inventory

**Last Updated:** 2025-10-30  
**Owner:** Engine Platform Team

---

## Subsystem Ownership Map

| Subsystem | Repo/Path | Owner | Stability SLO | Key Features | Notes |
|-----------|-----------|-------|---------------|--------------|-------|
| **Math** | `core/math/` | — | >99.9% | SIMD vectors (float4, float3x4), quaternions, matrices, transforms | Eigen/GLM wrapper + custom SIMD kernel |
| **Time** | `core/time/` | — | >99.99% | Fixed-step accumulator, clamped dt, jitter filtering | Feeds main loop; determinism critical |
| **Transforms** | `core/transforms/` | — | >99.9% | Hierarchical xform tree, parent-last eval, normalization | Single-threaded; normalized quats |
| **Animation** | `engine/animation/` | — | >99.9% | Spline sampling, blending, dual-quat skinning | Resample to fixed rate; no T-pose pops |
| **Rendering** | `render/core/` | — | >99.9% | Frame graph, PSO cache, device-lost recovery, barrier generation | bgfx backend; DXC shader compiler |
| **Physics** | `physics/engine/` | — | >99.9% | Fixed substeps, CCD, warm-starting, deterministic mode | Jolt integration; seeded RNG in determinism |
| **IO** | `core/io/` | — | >99.99% | Asset streaming, serialization, repro packing | Deterministic import; content-addressed cache |
| **Tooling** | `tools/` | — | >95% | Asset pipeline (baker, importer, fuzzer), shader compiler, golden image tests | Non-shipping; best-effort support |

---

## Subsystem Interfaces

### Math ↔ Transforms

```cpp
// core/math/quat.h
struct Quat { float x, y, z, w; };
void Normalize(Quat& q);

// core/transforms/transform.h
struct Transform {
  Vec3 pos;
  Quat rot;  // Always normalized
  Vec3 scale;
};
```

### Transforms ↔ Animation

```cpp
// core/transforms/hierarchy.h
class TransformHierarchy {
  void UpdateBones(Span<Animation> anims);
};
```

### Animation ↔ Rendering

```cpp
// render/skinning.h
void UpdateSkinningMatrices(const Animation& anim, Span<Mat4x3> output);
```

### Physics ↔ Transforms

```cpp
// physics/engine/world.h
void SyncPhysicsToTransforms(TransformHierarchy& hierarchy);
void SyncTransformsToPhysics(const TransformHierarchy& hierarchy);
```

### IO ↔ All

```cpp
// core/io/serializer.h
void SerializeScene(const Scene& scene, Writer& w);
Scene DeserializeScene(Reader& r);  // Deterministic
```

---

## Stability Commitments

| Subsystem | Crash Rate Target | Determinism | Device Loss Resilience | Notes |
|-----------|-------------------|-------------|------------------------|-------|
| Math | <0.1 per 1M ops | Full (seeded RNG) | N/A | No allocations |
| Time | <0.01 per 1M frames | Full (fixed dt) | N/A | Time is ground truth |
| Transforms | <0.1 per 1M updates | Full (no RNG) | N/A | Stateless updates |
| Animation | <0.2 per 1M samples | Full (no RNG) | N/A | Curve-based, deterministic |
| Rendering | <0.5 per 1M frames | Full (seeded jitter) | <500ms recovery | Device-lost chaos test |
| Physics | <1.0 per 1M steps | Full (sorted islands) | N/A | External seeding |
| IO | <0.2 per 1k imports | Full (deterministic bake) | N/A | Fuzzing + sandbox |
| Tooling | <5% import failure | N/A | N/A | Non-critical path |

---

## Versioning & Deprecation

| Subsystem | Current Version | Min. Support | Deprecation Window |
|-----------|-----------------|--------------|-------------------|
| Math | 1.0 | v1.0 | 2 minor releases |
| Time | 1.0 | v1.0 | 2 minor releases |
| Transforms | 1.0 | v1.0 | 2 minor releases |
| Animation | 1.0 | v1.0 | 2 minor releases |
| Rendering | 1.0 (bgfx) | v1.0 | 2 minor releases |
| Physics | 1.0 (Jolt) | v1.0 | 2 minor releases |
| IO | 1.0 | v1.0 | 2 minor releases |
| Tooling | 0.1 | N/A | Ad-hoc |

---

## Known Limitations

- **Math:** No denormal handling yet (STAB-014 adds FTZ policy)
- **Animation:** Only linear interpolation between frames; spline support TBD
- **Rendering:** Frame graph MVP; limited resource lifecycle management
- **Physics:** No continuous collision detection for skinned meshes
- **IO:** Importer sandbox incomplete (STAB-028)

---

## Roadmap

### Sprint 2
- Lock physics engine (Jolt)
- Finalize asset format (USD/glTF)
- Shader toolchain integration

### Sprint 3–4
- Camera module (reversed-Z, TAA)
- Allocators + fragmentation tracking
- Deterministic asset pipeline

### Sprint 5–6
- Record/replay framework
- Perf gates + dashboards
- Acceptance gates

---

## Contact

For subsystem-specific issues, see owner assignments (TBD) or file in respective repo.
