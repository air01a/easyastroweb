import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";

// ==========================
// Types
// ==========================

type Radians = number;

type EquatorialPos = { ra: Radians; dec: Radians };

type ScreenPos = { x: number; y: number };

export interface Star {
  pos: EquatorialPos & Partial<ScreenPos>;
  mag: number; // visual magnitude
  bv: number; // B-V color index
  name: string;
  // Derived at runtime
  color?: string; // CSS color
  radius?: number; // px
  bright?: boolean;
  visible?: boolean;
}

export interface DSO {
  pos: EquatorialPos & Partial<ScreenPos>;
  name: string;
  color: string;
  radius: number;
  visible? : boolean;
}

export interface Constellation {
  pos: EquatorialPos; // label position (RA/Dec in radians)
  abbrev: string;
  name: string;
}

export type ConstellationLine = readonly [number, number]; // indices in stars.json

export interface PlanetEl {
  pos: EquatorialPos; // initial placeholder (can be 0,0)
  name: string;
  color: string; // hex CSS color
  a: number; // semi-major axis (AU)
  e: number; // eccentricity
  i: Radians; // inclination
  o: Radians; // longitude of ascending node (Ω)
  wb: Radians; // argument of periapsis (ω)
  L: Radians; // mean longitude at J2000
  dL: number; // mean motion (deg/day) but we store rad/day by conversion
}

// ==========================
// Math/Astro helpers (ported from Dart)
// ==========================

class Astro {
  static readonly jdJ2000 = 2451545.0;
  static readonly jd1970 = 2440587.5;
  static readonly yearDays = 365.2422;

  static range(v: number, r: number): number {
    return v - r * Math.floor(v / r);
  }

  static degrad(x: number): Radians {
    return x * 1.74532925199433e-2; // π/180
  }

  static raddeg(x: number): number {
    return x * 5.729577951308232e1; // 180/π
  }

  static hrrad(x: number): Radians {
    return x * 2.617993877991494e-1; // 15° in rad per hour
  }

  static radhr(x: number): number {
    return x * 3.819718634205488; // 12/π hours per radian
  }

  // Convert hour angle/declination at given latitude -> azimuth/altitude (to)
  static aaHadec(lat: Radians, from: [Radians, Radians], to: [Radians, Radians]): void {
    const slat = Math.sin(lat);
    const clat = Math.cos(lat);
    const sx = Math.sin(from[0]); // HA
    const cx = Math.cos(from[0]);
    const sy = Math.sin(from[1]); // Dec
    const cyRaw = Math.cos(from[1]);
    const cy = Math.abs(cyRaw) < 1e-20 ? 1e-20 : cyRaw;

    to[0] = Math.atan2(-cy * sx, -cy * cx * slat + sy * clat); // Az
    to[1] = Math.asin(sy * slat + cy * clat * cx); // Alt
  }

  // Ecliptic <-> Equatorial (not used for stars, but handy for planets)
  static eclEq(sw: 1 | -1, from: [Radians, Radians], to: [Radians, Radians]): void {
    const eps = Astro.degrad(23.45229444);
    const seps = Math.sin(eps);
    const ceps = Math.cos(eps);

    const sy = Math.sin(from[1]);
    const cy0 = Math.cos(from[1]);
    const cy = Math.abs(cy0) < 1e-20 ? 1e-20 : cy0;
    const ty = sy / cy;
    const cx = Math.cos(from[0]);
    const sx = Math.sin(from[0]);

    to[1] = Math.asin(sy * ceps - cy * seps * sx * sw);
    to[0] = Math.atan2(sx * ceps + ty * seps * sw, cx);
    to[0] = Astro.range(to[0], 2 * Math.PI);
  }

  // Precession from jd1 epoch to jd2 epoch for [RA, Dec]
  static precess(jd1: number, jd2: number, coord: [Radians, Radians]): void {
    let zetaA: number, zA: number, thetaA: number;
    let T: number;
    let A: number, B: number, C: number;
    let alpha: number, delta: number;

    const fromEquinox = (jd1 - Astro.jdJ2000) / Astro.yearDays;
    const toEquinox = (jd2 - Astro.jdJ2000) / Astro.yearDays;
    const alphaIn = coord[0];
    const deltaIn = coord[1];

    let alpha2000: number;
    let delta2000: number;

    if (fromEquinox !== 0.0) {
      T = fromEquinox / 100.0;
      zetaA = Astro.degrad(T * (0.6406161 + T * (8.39e-5 + T * 5.0e-6)));
      zA = Astro.degrad(T * (0.6406161 + T * (3.041e-4 + T * 5.1e-6)));
      thetaA = Astro.degrad(T * (0.5567530 + T * (-1.185e-4 + T * 1.16e-5)));

      A = Math.sin(alphaIn - zA) * Math.cos(deltaIn);
      B = Math.cos(alphaIn - zA) * Math.cos(thetaA) * Math.cos(deltaIn) + Math.sin(thetaA) * Math.sin(deltaIn);
      C = -Math.cos(alphaIn - zA) * Math.sin(thetaA) * Math.cos(deltaIn) + Math.cos(thetaA) * Math.sin(deltaIn);

      alpha2000 = Math.atan2(A, B) - zetaA;
      alpha2000 = Astro.range(alpha2000, 2 * Math.PI);
      delta2000 = Math.asin(C);
    } else {
      alpha2000 = alphaIn;
      delta2000 = deltaIn;
    }

    if (toEquinox !== 0.0) {
      T = toEquinox / 100.0;
      zetaA = Astro.degrad(T * (0.6406161 + T * (8.39e-5 + T * 5.0e-6)));
      zA = Astro.degrad(T * (0.6406161 + T * (3.041e-4 + T * 5.1e-6)));
      thetaA = Astro.degrad(T * (0.5567530 + T * (-1.185e-4 + T * 1.16e-5)));

      A = Math.sin(alpha2000 + zetaA) * Math.cos(delta2000);
      B = Math.cos(alpha2000 + zetaA) * Math.cos(thetaA) * Math.cos(delta2000) - Math.sin(thetaA) * Math.sin(delta2000);
      C = Math.cos(alpha2000 + zetaA) * Math.sin(thetaA) * Math.cos(delta2000) + Math.cos(thetaA) * Math.sin(delta2000);

      alpha = Math.atan2(A, B) + zA;
      alpha = Astro.range(alpha, 2.0 * Math.PI);
      delta = Math.asin(C);
    } else {
      alpha = alpha2000;
      delta = delta2000;
    }

    coord[0] = alpha;
    coord[1] = delta;
  }
}

// ==========================
// Observer
// ==========================

class Observer {
  jd: number; // Julian day
  longitude: Radians; // East positive
  latitude: Radians;
  lst: Radians; // local sidereal time

  constructor(date: Date, lonDeg: number, latDeg: number) {
    this.jd = Observer.dateToJD(date);
    this.longitude = Astro.degrad(lonDeg);
    this.latitude = Astro.degrad(latDeg);
    this.lst = 0;
    this.initLST();
  }

  static dateToJD(date: Date): number {
    return Astro.jd1970 + date.getTime() / 86400000.0;
  }

  setDate(date: Date): void {
    this.jd = Observer.dateToJD(date);
    this.initLST();
  }

  incHour(count: number): void {
    this.jd += count / 24.0;
    this.initLST();
  }

  private jdDay(): number {
    return Math.floor(this.jd - 0.5) + 0.5;
  }

  private jdHour(): number {
    return (this.jd - this.jdDay()) * 24.0;
  }

  private gst(): Radians {
    const t = (this.jdDay() - Astro.jdJ2000) / 36525;
    const theta = 1.753368559146 + t * (628.331970688835 + t * (6.770708e-6 + t * -1.48e-6));
    return Astro.range(theta + Astro.hrrad(this.jdHour()), 2 * Math.PI);
  }

  private initLST(): void {
    this.lst = Astro.range(this.gst() + this.longitude, 2 * Math.PI);
  }
}

// ==========================
// SkyMap Logic
// ==========================

function initStarVisuals(stars: Star[]): void {
  const clut: string[] = [
    "#94B1FF", // -0.4  32000 K
    "#ADC6FF", // -0.1  12700 K
    "#CBDCFF", //  0.2   8400 K
    "#F0F5FF", //  0.5   6300 K
    "#FFF6E5", //  0.8   5100 K
    "#FFE7C2", //  1.1   4300 K
    "#FFDCA8", //  1.4   3800 K
    "#FFCE89", //  1.7   3300 K
    "#FFC475", //  2.0   3000 K
  ];

  const bvToColor = (bv: number): string => {
    let idx = Math.round((8 * (bv + 0.4)) / 2.4);
    if (idx < 0) idx = 0;
    if (idx > 8) idx = 8;
    return clut[idx];
  };

  for (const s of stars) {
    // Toujours une couleur issue du B-V (même pour les faibles magnitudes)
    s.color = bvToColor(s.bv);

    if (s.mag < 3.5) {
      s.radius = Math.max(1, 3.1 - 0.6 * s.mag); // 1..4
      s.bright = true;
    } else {
      s.radius = 1;
      s.bright = false;
    }
  }

  // Mini-tests dev
  
}

function projectToScreen(
  star: Star|DSO,
  obs: Observer,
  w: number,
  h: number
): void {
  // Copy coords (in radians)
  const coord: [Radians, Radians] = [star.pos.ra + 0.0, star.pos.dec + 0.0];
  // Precess from J2000 to current JD
  Astro.precess(Astro.jdJ2000, obs.jd, coord);
  // Hour angle = LST - RA
  coord[0] = obs.lst - coord[0];
  // Convert to Az/Alt
  Astro.aaHadec(obs.latitude, coord, coord);

  // Simple horizon cut (like original code)
  if (coord[1] < 0.15) {
    star.visible = false;
    return;
  }

  star.visible = true;
  const tmp = 0.5 - coord[1] / Math.PI; // radius factor
  const x = w * (0.5 - tmp * Math.sin(coord[0]));
  const y = h * (0.5 - tmp * Math.cos(coord[0]));
  star.pos.x = x;
  star.pos.y = y;
}

// ==========================
// React Component
// ==========================

export interface SkyMapProps {
  width?: number;
  height?: number;
  // Observer position (deg). Defaults: Paris (approx)
  lonDeg?: number; // East positive
  latDeg?: number;
  // Data URLs (relative to /public by default)
  starsCatalog : Star[];
  constellationsCatalog : Constellation[];
  linesCatalog:  ConstellationLine[];
  dsoCatalog: DSO[];
  background?: string; // canvas background
  backgroundImageUrl?:string;
    minScale? : number,
  maxScale? : number,
  minMagnitude?: number,
  date?: Date
  showConstellations? : boolean,
  showStarsName? : boolean,
  showDSO? : boolean,

}

//type PlanetJson = Omit<PlanetEl, "dL"> & { dL: number };

export const SkyMap: React.FC<SkyMapProps> = ({
  width = 900,
  height = 900,
  lonDeg = 2.3522,
  latDeg = 48.8566,
  starsCatalog,
  constellationsCatalog,
  linesCatalog,
  dsoCatalog,
  backgroundImageUrl,
  minMagnitude = 100,
  minScale = 0.5,
  maxScale = 8,
  showConstellations = true,
  showStarsName = true,
  showDSO =true,
  date = null,
  background = "#0a165cff"
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stars, setStars] = useState<Star[] | null>(null);
  const [constellations, setConstellations] = useState<Constellation[] | null>(null);
  const [lines, setLines] = useState<ConstellationLine[] | null>(null);
  const [dso, setDso] = useState<DSO[]|null>(null);
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null);

  // View transform (pan/zoom)
  const [scale, setScale] = useState<number>(1);
  const [offset, setOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Panning state
  const isPanningRef = useRef(false);
  const lastPosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Pinch state (for touch)
  const touchesRef = useRef<Map<number, { x: number; y: number }>>(new Map());
  const pinchStart = useRef<{
    dist: number;
    scale: number;
    midpoint: { x: number; y: number };
    offset: { x: number; y: number };
  } | null>(null);

  const observer = useMemo(() => {
    const observerDate:Date = date? date: new Date()

    return new Observer(observerDate, lonDeg, latDeg)
  }, [lonDeg, latDeg, date]);

  // Preload background image once
  useEffect(() => {
    if (!backgroundImageUrl) {
      setBgImage(null);
      return;
    }
    const img = new Image();
    img.src = backgroundImageUrl;
    img.onload = () => setBgImage(img);
  }, [backgroundImageUrl]);

  // Fetch JSON data
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!mounted) return;
      initStarVisuals(starsCatalog);
      setStars(starsCatalog);
      setConstellations(constellationsCatalog);
      setLines(linesCatalog);
      setDso(dsoCatalog);
    })().catch((e) => console.error(e));

    return () => {
      mounted = false;
    };
  }, [starsCatalog, constellationsCatalog, linesCatalog, dsoCatalog,  date]);

  // Helpers to convert screen <-> world coords (for cursor-centered zoom)
  const screenToWorld = useCallback(
    (sx: number, sy: number) => {
      return {
        x: (sx - offset.x) / scale,
        y: (sy - offset.y) / scale,
      };
    },
    [offset.x, offset.y, scale]
  );

  // Input handlers: mouse wheel (zoom at cursor)
  useEffect(() => {
    const cvs = canvasRef.current;
    if (!cvs) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault(); // avoid page scroll
      const rect = cvs.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      // cursor in world coords before zoom
      const worldBefore = screenToWorld(sx, sy);

      // zoom factor (trackpad vs wheel): use deltaY sign; small step
      const ZOOM_SENSITIVITY = 0.0015;
      const nextScale = Math.min(
        maxScale,
        Math.max(minScale, scale * Math.exp(-e.deltaY * ZOOM_SENSITIVITY))
      );

      // keep cursor-anchored zoom: adjust offset so the same world point stays under cursor
      const newOffsetX = sx - worldBefore.x * nextScale;
      const newOffsetY = sy - worldBefore.y * nextScale;

      setScale(nextScale);
      setOffset({ x: newOffsetX, y: newOffsetY });
    };

    cvs.addEventListener("wheel", onWheel, { passive: false });
    return () => cvs.removeEventListener("wheel", onWheel as EventListener);
  }, [scale, minScale, maxScale, screenToWorld]);

  // Input handlers: pointer (pan + pinch)
  useEffect(() => {
    const cvs = canvasRef.current;
    if (!cvs) return;

    const getPos = (e: PointerEvent) => {
      const rect = cvs.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const onPointerDown = (e: PointerEvent) => {
      cvs.setPointerCapture(e.pointerId);
      const p = getPos(e);
      touchesRef.current.set(e.pointerId, p);

      if (touchesRef.current.size === 1) {
        // start panning
        isPanningRef.current = true;
        lastPosRef.current = p;
      } else if (touchesRef.current.size === 2) {
        // start pinch
        const arr = Array.from(touchesRef.current.values());
        const dx = arr[1].x - arr[0].x;
        const dy = arr[1].y - arr[0].y;
        const dist = Math.hypot(dx, dy);
        const midpoint = { x: (arr[0].x + arr[1].x) / 2, y: (arr[0].y + arr[1].y) / 2 };
        pinchStart.current = { dist, scale, midpoint, offset: { ...offset } };
        isPanningRef.current = false;
      }
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!cvs.hasPointerCapture(e.pointerId)) return;
      const p = getPos(e);
      touchesRef.current.set(e.pointerId, p);

      if (touchesRef.current.size === 1 && isPanningRef.current) {
        // drag to pan
        const dx = p.x - lastPosRef.current.x;
        const dy = p.y - lastPosRef.current.y;
        lastPosRef.current = p;
        setOffset((o) => ({ x: o.x + dx, y: o.y + dy }));
      } else if (touchesRef.current.size === 2 && pinchStart.current) {
        // pinch zoom
        const arr = Array.from(touchesRef.current.values());
        const dx = arr[1].x - arr[0].x;
        const dy = arr[1].y - arr[0].y;
        const dist = Math.hypot(dx, dy);
        const midpoint = { x: (arr[0].x + arr[1].x) / 2, y: (arr[0].y + arr[1].y) / 2 };

        // scale factor relative to start
        let nextScale = (pinchStart.current.scale * dist) / pinchStart.current.dist;
        nextScale = Math.min(maxScale, Math.max(minScale, nextScale));

        // keep midpoint anchored under fingers
        const worldBefore = {
          x: (pinchStart.current.midpoint.x - pinchStart.current.offset.x) / pinchStart.current.scale,
          y: (pinchStart.current.midpoint.y - pinchStart.current.offset.y) / pinchStart.current.scale,
        };
        const newOffsetX = midpoint.x - worldBefore.x * nextScale;
        const newOffsetY = midpoint.y - worldBefore.y * nextScale;

        setScale(nextScale);
        setOffset({ x: newOffsetX, y: newOffsetY });
      }
    };

    const onPointerUp = (e: PointerEvent) => {
      touchesRef.current.delete(e.pointerId);
      cvs.releasePointerCapture(e.pointerId);
      if (touchesRef.current.size === 0) {
        isPanningRef.current = false;
        pinchStart.current = null;
      } else if (touchesRef.current.size === 1) {
        // switch back to panning with remaining finger
        const remaining = Array.from(touchesRef.current.values())[0];
        lastPosRef.current = remaining;
        isPanningRef.current = true;
        pinchStart.current = null;
      }
    };

    cvs.addEventListener("pointerdown", onPointerDown);
    cvs.addEventListener("pointermove", onPointerMove);
    cvs.addEventListener("pointerup", onPointerUp);
    cvs.addEventListener("pointercancel", onPointerUp);
    cvs.addEventListener("pointerleave", onPointerUp);

    return () => {
      cvs.removeEventListener("pointerdown", onPointerDown);
      cvs.removeEventListener("pointermove", onPointerMove);
      cvs.removeEventListener("pointerup", onPointerUp);
      cvs.removeEventListener("pointercancel", onPointerUp);
      cvs.removeEventListener("pointerleave", onPointerUp);
    };
  }, [scale, offset, minScale, maxScale]);

  // Draw with transform (pan/zoom)
  useEffect(() => {
    const cvs = canvasRef.current;
    if (!cvs || !stars || !lines || !dso) return;
    const ctx = cvs.getContext("2d");
    if (!ctx) return;

    // clear
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, cvs.width, cvs.height);

    // apply pan/zoom
    ctx.setTransform(scale, 0, 0, scale, offset.x, offset.y);

    // background (scaled with content)
    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, width, height);
    } else {
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, width, height);
    }

    // project stars in "world" coords (base width/height)
    for (const s of stars) {
      projectToScreen(s, observer, width, height);
    }

    for (const d of dso) {
      projectToScreen(d, observer, width, height)
    }

    // lines
    if (showConstellations) {
      ctx.lineWidth = 0.6 / scale; // keep visual width constant-ish
      ctx.strokeStyle = "#44506A";
      ctx.beginPath();
      for (const [a, b] of lines) {
        const sa = stars[a];
        const sb = stars[b];
        if (!sa || !sb) continue;
        if (!sa.visible || !sb.visible) continue;
        if (sa.pos.x === undefined || sa.pos.y === undefined) continue;
        if (sb.pos.x === undefined || sb.pos.y === undefined) continue;
        ctx.moveTo(sa.pos.x, sa.pos.y);
        ctx.lineTo(sb.pos.x, sb.pos.y);
      }
      ctx.stroke();
    }
    
    //ctx.setTransform(scale, 0, 0, scale, offset.x, offset.y);

    // labels
    if (showConstellations && constellations) {
      ctx.font = `${12 / scale}px system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
      ctx.fillStyle = "#93A1B0";
      for (const c of constellations) {
        const tmpStar: Star = { pos: { ...c.pos }, mag: 0, bv: 0, name: c.name };
        projectToScreen(tmpStar, observer, width, height);
        if (!tmpStar.visible || tmpStar.pos.x === undefined || tmpStar.pos.y === undefined) continue;
        ctx.fillText(c.abbrev || c.name, tmpStar.pos.x + 4 / scale, tmpStar.pos.y - 4 / scale);
      }
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0); // reset transform

    // stars (respect alpha by magnitude, couleurs B-V)
    for (const s of stars) {
      ctx.font = `${12 }px system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
      if (s.mag>minMagnitude || !s.visible || s.pos.x === undefined || s.pos.y === undefined) continue;
      const r = (s.radius ?? 1);
      const alpha = s.bright ? 1 : Math.max(0.2, 1 - 0.22 * (s.mag - 3.5));
      const prevAlpha = ctx.globalAlpha;
      
      const screenX = offset.x + s.pos.x * scale;
      const screenY = offset.y + s.pos.y * scale;
      ctx.globalAlpha = Math.min(1, Math.max(0.2, alpha));
      ctx.beginPath();
      ctx.arc(screenX, screenY  , r, 0, Math.PI * 2);
      ctx.closePath();
      ctx.fillStyle = s.color ?? "#CCCCFF";
      ctx.fill();
      ctx.globalAlpha = prevAlpha;
      if (showStarsName) {
        ctx.fillText(s.name, screenX+5, screenY)
      }


    }

    if (showDSO) {
      for (const c of dso) {
        ctx.font = `${12 }px system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
        if (!c.visible || c.pos.x === undefined || c.pos.y === undefined) continue;
        const r = (c.radius ?? 1);
        
        const screenX = offset.x + c.pos.x * scale;
        const screenY = offset.y + c.pos.y * scale;
        ctx.beginPath();
        ctx.arc(screenX, screenY  , r, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = c.color ?? "#CCCCFF";
        ctx.fill();
        ctx.fillText(c.name, screenX+5, screenY)



      }
        
    }
  }, [stars, lines, constellations, background, observer, bgImage, scale, offset, width, height, minMagnitude, showConstellations, showStarsName, showDSO, date, dso]);

  return (
    <div className="w-full flex flex-col items-center gap-2">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="rounded-2xl shadow-lg touch-none"
        style={{ touchAction: "none", cursor: "grab" }}
      />

    </div>
  );
};


export default SkyMap;