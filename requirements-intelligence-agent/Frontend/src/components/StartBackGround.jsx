import React from "react";


import { Canvas, useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import { useRef, useState } from 'react';
import * as THREE from 'three';

function ShootingStar() {
  const starRef = useRef();
  const [velocity] = useState(() => new THREE.Vector3(
    (Math.random() - 0.5) * 1.5,
    (Math.random() - 0.5) * 1.5,
    (Math.random() - 0.5) * 1.5
  ));

  useFrame(() => {
    if (starRef.current) {
      starRef.current.position.add(velocity);

      starRef.current.material.opacity -= 0.01;

      if (starRef.current.material.opacity <= 0) {

        starRef.current.position.set(
          (Math.random() - 0.5) * 50,
          (Math.random() - 0.5) * 50,
          (Math.random() - 0.5) * 50
        );
        starRef.current.material.opacity = 1;
      }
    }
  });

  return (
    <mesh ref={starRef} position={[
      (Math.random() - 0.5) * 50,
      (Math.random() - 0.5) * 50,
      (Math.random() - 0.5) * 50
    ]}>
      <sphereGeometry args={[0.08, 8, 8]} />
      <meshBasicMaterial color="white" transparent opacity={1} />
    </mesh>
  );
}

export default function StarBackground() {
  return (
    <Canvas
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        width: '100vw',
        zIndex: 0,
        pointerEvents: 'none',
        background: '#05050f'
      }}
      camera={{ position: [0, 0, 1] }}
    >

      <Stars
        radius={100}
        depth={50}
        count={8000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />

      <ShootingStar />
      <ShootingStar />
      <ShootingStar />

    </Canvas>
  );
}
