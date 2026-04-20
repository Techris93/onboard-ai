import { useEffect } from "react";
import type { RefObject } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function useRevealOnScroll(
  scopeRef: RefObject<HTMLElement | null>,
  selector = ".reveal",
  stagger = 0.12,
  start = "top 80%",
  distance = 36,
) {
  useEffect(() => {
    if (!scopeRef.current) {
      return;
    }

    const context = gsap.context(() => {
      const elements = gsap.utils.toArray<HTMLElement>(selector);

      elements.forEach((element, index) => {
        gsap.fromTo(
          element,
          { opacity: 0, y: distance },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            delay: index * stagger,
            ease: "power3.out",
            scrollTrigger: {
              trigger: element,
              start,
              once: true,
            },
          },
        );
      });
    }, scopeRef);

    return () => {
      context.revert();
    };
  }, [distance, scopeRef, selector, stagger, start]);
}
