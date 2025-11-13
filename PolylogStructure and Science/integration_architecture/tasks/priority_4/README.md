# Priority 4 — Visualization Pipeline (VIZ)

## TASK-VIZ-001: GPU Instancing Prototype

- **File:** `src/frontend/components/InstancedPolyforms.jsx`
- **Dependencies:** `@react-three/fiber`, `three`
- **Code Stub:**

  ```jsx
  import { useMemo } from 'react'
  import * as THREE from 'three'

  function InstancedPolyforms({ polyforms, geometry, material }) {
    const instancedMesh = useMemo(() => {
      const mesh = new THREE.InstancedMesh(
        geometry,
        material ?? new THREE.MeshPhongMaterial({ color: 0x00ff00 }),
        polyforms.length,
      )

      const matrix = new THREE.Matrix4()
      polyforms.forEach((pf, index) => {
        matrix.compose(pf.position, pf.quaternion, pf.scale)
        mesh.setMatrixAt(index, matrix)
      })
      mesh.instanceMatrix.needsUpdate = true
      return mesh
    }, [geometry, material, polyforms])

    return <primitive object={instancedMesh} />
  }

  export default InstancedPolyforms
  ```

- **Validation:** Profiling shows ≥50× reduction in draw calls for repeated assemblies; frame rate ≥30 FPS at 1000 instances
- **Resources:** Three.js instancing guide <https://threejs.org/examples/#webgl_instancing_dynamic>

## TASK-VIZ-002: Catalog-Driven LOD Pipeline

- **Files:** `scripts/populate_catalogs.py`, `src/frontend/components/LODPolyform.jsx`
- **Dependencies:** `three`
- **Code Stub (`LODPolyform.jsx`):**

  ```jsx
  import { useMemo, useRef } from 'react'
  import { LOD } from 'three'
  import { useFrame } from '@react-three/fiber'

  function LODPolyform({ geometries, material, position }) {
    const lodRef = useRef()

    const lod = useMemo(() => {
      const lodObject = new LOD()
      lodObject.addLevel(new THREE.Mesh(geometries.full, material), 0)
      lodObject.addLevel(new THREE.Mesh(geometries.medium, material), 5)
      lodObject.addLevel(new THREE.Mesh(geometries.low, material), 20)
      return lodObject
    }, [geometries, material])

    useFrame(({ camera }) => {
      lodRef.current?.update(camera)
    })

    return <primitive ref={lodRef} object={lod} position={position} />
  }

  export default LODPolyform
  ```

- **Validation:** LOD transitions at 5/20 units without visible popping; catalog metadata includes `lod_metadata.json`
- **Resources:** Three.js LOD docs <https://threejs.org/docs/#api/en/objects/LOD>

## TASK-VIZ-003: Progressive Geometry Loader

- **File:** `src/frontend/state/useGeometryLoader.ts`
- **Dependencies:** `zustand`, `@react-three/fiber`
- **Code Sketch:**

  ```ts
  import create from 'zustand'

  type GeometryState = {
    loading: boolean
    geometries: Record<string, LoadedGeometry>
    loadGeometry: (uuid: string) => Promise<void>
  }

  export const useGeometryLoader = create<GeometryState>((set, get) => ({
    loading: false,
    geometries: {},
    async loadGeometry(uuid) {
      if (get().geometries[uuid]) return
      set({ loading: true })
      const placeholder = await fetch(`/lod/${uuid}/aabb.json`).then(res => res.json())
      set(state => ({
        geometries: {
          ...state.geometries,
          [uuid]: { level: 'aabb', data: placeholder },
        },
      }))
      const full = await window.__TAURI__.invoke('load_geometry', { uuid })
      set(state => ({
        loading: false,
        geometries: {
          ...state.geometries,
          [uuid]: { level: 'full', data: full },
        },
      }))
    },
  }))
  ```

- **Validation:** Initial AABB render <50 ms; full geometry upgrade <90 ms; no flicker during swap
- **Resources:** Zustand docs <https://docs.pmnd.rs/zustand>

## TASK-VIZ-004: Interaction & Context Menu Framework

- **Files:** `src/frontend/components/InteractivePolyform.jsx`, `src/frontend/components/PolyformContextMenu.jsx`
- **Dependencies:** `react-contexify`, `zustand`
- **Code Stub:**

  ```jsx
  import { Menu, Item, useContextMenu } from 'react-contexify'
  import 'react-contexify/dist/ReactContexify.css'

  const MENU_ID = 'polyform-menu'

  export function PolyformContextMenu({ onDuplicate, onDelete, onRotate }) {
    return (
      <Menu id={MENU_ID}>
        <Item onClick={({ props }) => onDuplicate(props.uuid)}>Duplicate</Item>
        <Item onClick={({ props }) => onRotate(props.uuid)}>Rotate 90°</Item>
        <Item onClick={({ props }) => onDelete(props.uuid)}>Delete</Item>
      </Menu>
    )
  }

  export function InteractivePolyform({ uuid, meshProps, actions }) {
    const { show } = useContextMenu({ id: MENU_ID })

    return (
      <mesh
        {...meshProps}
        onPointerOver={() => actions.setHover(uuid)}
        onPointerOut={actions.clearHover}
        onClick={() => actions.select(uuid)}
        onContextMenu={event => {
          event.stopPropagation()
          show({ event, props: { uuid } })
        }}
      />
    )
  }
  ```

- **Validation:** Right-click opens menu with <100 ms latency; state updates in Zustand store reflect selection/hover
- **Resources:** react-contexify docs <https://github.com/fkhadra/react-contexify>

## TASK-VIZ-005: Worker Offload for Geometry Ops

- **Files:** `src/workers/geometryWorker.ts`, `src/frontend/state/useGeometryWorker.ts`
- **Dependencies:** `comlink`
- **Code Stub (`geometryWorker.ts`):**

  ```ts
  import { expose } from 'comlink'

  const workerAPI = {
    generateLOD(payload) {
      return computeLODLevels(payload)
    },
    preprocessGeometry(payload) {
      return computeTopology(payload)
    },
  }

  expose(workerAPI)
  ```

- **Validation:** Main-thread frame times stay <16 ms while preprocessing runs; worker messages round-trip via Comlink
- **Resources:** Comlink docs <https://github.com/GoogleChromeLabs/comlink>
