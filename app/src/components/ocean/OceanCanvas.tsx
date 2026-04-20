import { useEffect, useRef } from "react";
import * as THREE from "three";
import { oceanFragmentShader, oceanVertexShader } from "./shaders";

export default function OceanCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const fallbackBackground =
      "linear-gradient(180deg, #0f2740 0%, #153c5f 40%, #050913 100%)";

    const gl = canvas.getContext("webgl2");
    if (!gl) {
      canvas.style.background = fallbackBackground;
      return;
    }

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: false,
        alpha: false,
      });
    } catch {
      canvas.style.background = fallbackBackground;
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x050913, 1);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {
      uTime: { value: 0 },
      uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
      uMouse: { value: new THREE.Vector2(-10, -10) },
      uMouseActive: { value: 0 },
      uIntensity: { value: 0.5 },
      uSunPositionX: { value: -0.7 },
      uSunPositionY: { value: 0.12 },
    };

    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      vertexShader: oceanVertexShader,
      fragmentShader: oceanFragmentShader,
      uniforms,
    });
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const clock = new THREE.Clock();
    let mouseActive = 0;
    let mouseTimeout: ReturnType<typeof setTimeout> | null = null;
    let targetIntensity = 0.5;
    let animId = 0;

    const onMouseMove = (e: MouseEvent) => {
      uniforms.uMouse.value.x = e.clientX / window.innerWidth;
      uniforms.uMouse.value.y = 1.0 - e.clientY / window.innerHeight;
      mouseActive = 1;
      if (mouseTimeout) {
        clearTimeout(mouseTimeout);
      }
      mouseTimeout = setTimeout(() => {
        mouseActive = 0;
      }, 150);
    };

    const onMouseLeave = () => {
      mouseActive = 0;
    };

    const onScroll = () => {
      const progress = window.scrollY / Math.max(document.body.scrollHeight - window.innerHeight, 1);
      targetIntensity = 0.5 + progress * 0.5;
    };

    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.setSize(w, h);
      uniforms.uResolution.value.set(w, h);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseleave', onMouseLeave);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize);

    const animate = () => {
      animId = requestAnimationFrame(animate);
      uniforms.uTime.value = clock.getElapsedTime();
      uniforms.uIntensity.value += (targetIntensity - uniforms.uIntensity.value) * 0.05;
      uniforms.uMouseActive.value += (mouseActive - uniforms.uMouseActive.value) * 0.05;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      if (mouseTimeout) {
        clearTimeout(mouseTimeout);
      }
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseleave", onMouseLeave);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 0,
        display: "block",
      }}
    />
  );
}
