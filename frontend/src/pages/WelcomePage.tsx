import React, { useEffect, useMemo, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import gsap from "gsap"
import ScrollTrigger from "gsap/ScrollTrigger"
import Lenis from "@studio-freight/lenis"

gsap.registerPlugin(ScrollTrigger)

type MordorStats = {
  avgAttendance?: number
  avgIp?: number
  kills?: number
  deaths?: number
  killFame?: string
}

function cx(...c: Array<string | false | null | undefined>) {
  return c.filter(Boolean).join(" ")
}

function StatCard({
  label,
  value,
  hint,
  loading,
}: {
  label: string
  value: string
  hint?: string
  loading?: boolean
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4 shadow-[0_0_0_1px_rgba(255,255,255,0.04)]">
      <div className="pointer-events-none absolute -inset-24 opacity-30 blur-3xl [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.25),transparent_60%),radial-gradient(circle_at_70%_60%,rgba(140,200,255,0.16),transparent_55%)]" />
      <div className="relative">
        <div className="text-xs tracking-widest text-white/60">{label}</div>
        <div className="mt-2 text-2xl font-semibold text-white">
          {loading ? <span className="inline-block h-7 w-28 animate-pulse rounded-lg bg-white/10" /> : value}
        </div>
        {hint ? <div className="mt-2 text-xs text-white/45">{hint}</div> : null}
      </div>
    </div>
  )
}

function RuneDivider({ className }: { className?: string }) {
  return (
    <div className={cx("relative my-10 h-px w-full overflow-hidden", className)}>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="absolute inset-0 opacity-60 [mask-image:linear-gradient(to_right,transparent,black,transparent)]">
        <div className="h-px w-[200%] animate-[shimmer_3.5s_linear_infinite] bg-gradient-to-r from-transparent via-amber-200/30 to-transparent" />
      </div>
    </div>
  )
}

function FloatingRunes() {
  const runes = useMemo(
    () => ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛋ", "ᛏ"],
    []
  )
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {Array.from({ length: 18 }).map((_, i) => {
        const r = runes[i % runes.length]
        const left = (i * 7 + 13) % 100
        const top = (i * 11 + 9) % 100
        const size = 14 + (i % 7) * 3
        const dur = 7 + (i % 6) * 1.5
        const delay = (i % 9) * 0.35
        return (
          <div
            key={i}
            className="absolute text-amber-200/20 drop-shadow-[0_0_12px_rgba(255,214,120,0.22)]"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              fontSize: `${size}px`,
              animation: `floatRune ${dur}s ease-in-out ${delay}s infinite`,
            }}
          >
            {r}
          </div>
        )
      })}
    </div>
  )
}

export default function WelcomePage() {
  const heroRef = useRef<HTMLDivElement | null>(null)
  const doorsRef = useRef<HTMLDivElement | null>(null)
  const runeRingRef = useRef<HTMLDivElement | null>(null)
  const shatterRef = useRef<HTMLDivElement | null>(null)
  const aboutRef = useRef<HTMLDivElement | null>(null)
  const mordorRef = useRef<HTMLDivElement | null>(null)
  const perksRef = useRef<HTMLDivElement | null>(null)
  const galleryRef = useRef<HTMLDivElement | null>(null)
  const contactRef = useRef<HTMLDivElement | null>(null)

  const DISCORD_INVITE = "https://discord.gg/PASTE_YOUR_INVITE"

  const [stats, setStats] = useState<MordorStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [mouse, setMouse] = useState({ x: 50, y: 50 })
  const lenisCleanupRef = useRef<(() => void) | null>(null)

  // Reset scroll, clear ScrollTrigger state, apply body styles (fixes EREBOR→MORDOR→EREBOR)
  useEffect(() => {
    window.scrollTo(0, 0)
    ScrollTrigger.clearScrollMemory()
    ScrollTrigger.getAll().forEach((st) => st.kill())
    const prevBackground = document.body.style.background
    const prevColor = document.body.style.color
    const prevMinHeight = document.body.style.minHeight
    document.body.style.background = "#050607"
    document.body.style.color = "#fff"
    document.body.style.minHeight = "100vh"
    return () => {
      document.body.style.background = prevBackground
      document.body.style.color = prevColor
      document.body.style.minHeight = prevMinHeight
      ScrollTrigger.clearScrollMemory()
    }
  }, [])

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.15,
      smoothWheel: true,
      wheelMultiplier: 0.95,
    })

    // Sync ScrollTrigger with Lenis so pin positions don’t jump
    ScrollTrigger.scrollerProxy(document.body, {
      scrollTop(value?: number) {
        if (value !== undefined) lenis.scrollTo(value, { immediate: true })
        return lenis.scroll
      },
      getBoundingClientRect() {
        return { top: 0, left: 0, width: window.innerWidth, height: window.innerHeight }
      },
      pinType: "fixed",
    })

    lenis.on("scroll", ScrollTrigger.update)
    const tickerCallback = (time: number) => lenis.raf(time * 1000)
    gsap.ticker.add(tickerCallback)
    gsap.ticker.lagSmoothing(0)

    // Start at top and refresh ScrollTrigger after layout (fixes client-side nav from MORDOR)
    lenis.scrollTo(0, { immediate: true })
    const refreshId = setTimeout(() => {
      ScrollTrigger.refresh()
    }, 100)

    lenisCleanupRef.current = () => {
      clearTimeout(refreshId)
      gsap.ticker.remove(tickerCallback)
      lenis.off("scroll", ScrollTrigger.update)
      ScrollTrigger.scrollerProxy(document.body, {})
      ;(lenis as unknown as { destroy?: () => void })?.destroy?.()
      ScrollTrigger.clearScrollMemory()
    }
    return () => {
      lenisCleanupRef.current = null
    }
  }, [])

  useEffect(() => {
    const fallback: MordorStats = {
      avgAttendance: 40,
      avgIp: 1509,
      kills: 1800,
      deaths: 1100,
      killFame: "625.4m",
    }
    setStats(fallback)
    setStatsLoading(false)
  }, [])

  useEffect(() => {
    let ctx: ReturnType<typeof gsap.context> | null = null
    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    // Defer so refs and Lenis are ready after client-side nav (next frame + delay; works for EREBOR→MORDOR→EREBOR)
    const frameId = requestAnimationFrame(() => {
      timeoutId = setTimeout(() => {
        if (cancelled) return
        const hero = heroRef.current
        const doors = doorsRef.current
        const ring = runeRingRef.current
        const shatter = shatterRef.current
        if (!hero || !doors || !ring) return
        ScrollTrigger.clearScrollMemory()

        ctx = gsap.context(() => {
          gsap.fromTo(
            ring,
            { rotate: -18, opacity: 0, scale: 0.92 },
            { rotate: 0, opacity: 1, scale: 1, duration: 1.25, ease: "power3.out" }
          )

          // Shatter runes: scatter and fade as user scrolls past hero
          if (shatter) {
            const runeEls = shatter.querySelectorAll("[data-shatter-rune]")
            runeEls.forEach((el, i) => {
              const angle = (i / runeEls.length) * 360
              const dist = 80 + Math.random() * 120
              const tx = Math.cos((angle * Math.PI) / 180) * dist
              const ty = Math.sin((angle * Math.PI) / 180) * dist - 40
              gsap.to(el, {
                x: tx,
                y: ty,
                scale: 0.2,
                opacity: 0,
                rotate: (i % 2 === 0 ? 1 : -1) * (45 + Math.random() * 90),
                ease: "none",
                scrollTrigger: {
                  trigger: hero,
                  start: "top top",
                  end: "bottom top",
                  scrub: true,
                },
              })
            })
          }

          const leftDoor = doors.querySelector("[data-door='left']")
          const rightDoor = doors.querySelector("[data-door='right']")
          const haze = doors.querySelector("[data-layer='haze']")
          const dust = doors.querySelector("[data-layer='dust']")

          if (leftDoor && rightDoor) {
            gsap.to(leftDoor, {
              xPercent: -22,
              ease: "none",
              scrollTrigger: {
                trigger: hero,
                start: "top top",
                end: "bottom top",
                scrub: true,
              },
            })
            gsap.to(rightDoor, {
              xPercent: 22,
              ease: "none",
              scrollTrigger: {
                trigger: hero,
                start: "top top",
                end: "bottom top",
                scrub: true,
              },
            })
          }

          if (haze) {
            gsap.to(haze, {
              yPercent: 14,
              opacity: 0.9,
              ease: "none",
              scrollTrigger: {
                trigger: hero,
                start: "top top",
                end: "bottom top",
                scrub: true,
              },
            })
          }

          if (dust) {
            gsap.to(dust, {
              yPercent: -10,
              opacity: 0.75,
              ease: "none",
              scrollTrigger: {
                trigger: hero,
                start: "top top",
                end: "bottom top",
                scrub: true,
              },
            })
          }

          const sections = [aboutRef, mordorRef, perksRef, galleryRef, contactRef]
            .map((r) => r.current)
            .filter(Boolean) as HTMLElement[]

          sections.forEach((el) => {
            gsap.fromTo(
              el,
              { y: 36, opacity: 0 },
              {
                y: 0,
                opacity: 1,
                duration: 0.9,
                ease: "power3.out",
                scrollTrigger: {
                  trigger: el,
                  start: "top 78%",
                  end: "top 55%",
                  scrub: false,
                },
              }
            )
          })
        })

        if (!cancelled) {
          ScrollTrigger.refresh()
        }
      }, 120)
    })

    return () => {
      cancelled = true
      cancelAnimationFrame(frameId)
      if (timeoutId != null) clearTimeout(timeoutId)
      lenisCleanupRef.current?.()
      lenisCleanupRef.current = null
      if (ctx) ctx.revert()
      ScrollTrigger.clearScrollMemory()
    }
  }, [])

  const scrollTo = (id: "about" | "mordor" | "perks" | "gallery" | "contact") => {
    const map: Record<string, React.RefObject<HTMLDivElement | null>> = {
      about: aboutRef,
      mordor: mordorRef,
      perks: perksRef,
      gallery: galleryRef,
      contact: contactRef,
    }
    const el = map[id].current
    if (!el) return
    el.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    const { clientX, clientY } = e
    const x = (clientX / window.innerWidth) * 100
    const y = (clientY / window.innerHeight) * 100
    setMouse({ x, y })
  }

  return (
    <div
      className="min-h-screen bg-[#050607] text-white welcome-glow-on-load"
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setMouse({ x: 50, y: 50 })}
    >
      {/* Gold wash on open: fades out over 1s */}
      <div
        className="welcome-glow-overlay pointer-events-none fixed inset-0 z-[2]"
        style={{
          background: "radial-gradient(ellipse 120% 80% at 50% 30%, rgba(255,215,128,0.35) 0%, rgba(255,200,100,0.18) 40%, rgba(255,180,80,0.06) 70%, transparent 100%)",
        }}
        aria-hidden
      />
      {/* Cursor glow: gnomish lantern effect so text/letters glow under cursor */}
      <div
        className="pointer-events-none fixed inset-0 z-[1] opacity-60"
        style={{
          background: `radial-gradient(circle 180px at ${mouse.x}% ${mouse.y}%, rgba(255,210,120,0.22) 0%, rgba(255,180,80,0.08) 35%, transparent 70%)`,
        }}
        aria-hidden
      />
      <div className="welcome-text-glow relative z-10">
      <div className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-black/40 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <Link to="/" className="flex items-center gap-3 text-white hover:text-white/90 focus:outline-none focus:underline">
            <div className="h-9 w-9 rounded-xl border border-amber-200/25 bg-gradient-to-b from-amber-200/10 to-transparent shadow-[0_0_22px_rgba(255,210,120,0.12)]" />
            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-wide">EREBOR</div>
              <div className="text-[11px] text-white/55">PvE • Albion Online</div>
            </div>
          </Link>

          <div className="hidden items-center gap-5 text-sm text-white/70 md:flex">
            <button className="hover:text-white" onClick={() => scrollTo("about")}>О гильдии</button>
            <button className="hover:text-white" onClick={() => scrollTo("mordor")}>Mordor</button>
            <button className="hover:text-white" onClick={() => scrollTo("perks")}>Плюшки</button>
            <button className="hover:text-white" onClick={() => scrollTo("gallery")}>Галерея</button>
            <button className="hover:text-white" onClick={() => scrollTo("contact")}>Контакты</button>
          </div>

          <a
            href={DISCORD_INVITE}
            target="_blank"
            rel="noreferrer"
            className="group relative inline-flex items-center gap-2 rounded-xl border border-amber-200/30 bg-amber-200/10 px-4 py-2 text-sm font-semibold text-amber-100 shadow-[0_0_28px_rgba(255,214,120,0.12)] hover:bg-amber-200/14"
          >
            <span className="absolute -inset-8 -z-10 opacity-0 blur-2xl transition group-hover:opacity-100 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.28),transparent_60%)]" />
            Войти в Discord
            <span className="text-amber-200/70">↗</span>
          </a>
        </div>
      </div>

      <section ref={heroRef} className="relative min-h-[92vh] pt-16">
        <div className="absolute inset-0">
          <div
            className="absolute inset-0 opacity-90"
            style={{
              background: [
                "radial-gradient(ellipse 100% 80% at 40% 30%, rgba(255,210,120,0.14) 0%, rgba(255,210,120,0.10) 28%, rgba(255,208,115,0.06) 48%, rgba(255,200,100,0.02) 65%, transparent 78%)",
                "radial-gradient(ellipse 100% 85% at 70% 65%, rgba(120,170,255,0.12) 0%, rgba(120,168,252,0.08) 30%, rgba(130,178,255,0.04) 52%, rgba(140,188,255,0.01) 70%, transparent 82%)",
                "linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.68) 50%, rgba(0,0,0,0.9) 100%)",
              ].join(", "),
            }}
          />
          <FloatingRunes />
        </div>

        <div ref={doorsRef} className="pointer-events-none absolute inset-0 overflow-hidden">
          {/* Left door: visible panel + runic glyphs */}
          <div className="absolute inset-y-0 left-0 w-1/2" data-door="left">
            <div className="absolute inset-0 border-r-2 border-amber-400/30 bg-gradient-to-r from-stone-900/95 via-stone-900/80 to-transparent shadow-[4px_0_24px_rgba(0,0,0,0.4),inset_-1px_0_0_rgba(255,210,120,0.08)]" />
            <div className="absolute inset-0 opacity-80 [background:radial-gradient(circle_at_70%_50%,rgba(255,215,128,0.18),transparent_55%)]" />
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-[12%] py-[15%]" aria-hidden>
              {["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ"].map((rune, i) => (
                <span
                  key={i}
                  className="text-4xl md:text-5xl text-amber-200/50 drop-shadow-[0_0_8px_rgba(255,214,120,0.35)] font-medium"
                  style={{ textShadow: "0 0 12px rgba(255,210,120,0.25)" }}
                >
                  {rune}
                </span>
              ))}
            </div>
          </div>
          {/* Right door: visible panel + runic glyphs */}
          <div className="absolute inset-y-0 right-0 w-1/2" data-door="right">
            <div className="absolute inset-0 border-l-2 border-amber-400/30 bg-gradient-to-l from-stone-900/95 via-stone-900/80 to-transparent shadow-[-4px_0_24px_rgba(0,0,0,0.4),inset_1px_0_0_rgba(255,210,120,0.08)]" />
            <div className="absolute inset-0 opacity-80 [background:radial-gradient(circle_at_30%_50%,rgba(255,215,128,0.18),transparent_55%)]" />
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-[12%] py-[15%]" aria-hidden>
              {["ᛏ", "ᛋ", "ᛈ", "ᛇ", "ᛃ", "ᛁ", "ᚾ", "ᚺ"].map((rune, i) => (
                <span
                  key={i}
                  className="text-4xl md:text-5xl text-amber-200/50 drop-shadow-[0_0_8px_rgba(255,214,120,0.35)] font-medium"
                  style={{ textShadow: "0 0 12px rgba(255,210,120,0.25)" }}
                >
                  {rune}
                </span>
              ))}
            </div>
          </div>

          <div className="absolute inset-0 opacity-50" data-layer="haze">
            <div className="absolute -inset-24 blur-3xl [background:radial-gradient(circle_at_30%_60%,rgba(180,220,255,0.10),transparent_55%),radial-gradient(circle_at_70%_40%,rgba(255,210,120,0.10),transparent_55%)]" />
          </div>

          <div className="absolute inset-0 opacity-35" data-layer="dust">
            <div className="absolute inset-0 [background:radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.05),transparent_30%),radial-gradient(circle_at_80%_40%,rgba(255,255,255,0.04),transparent_35%),radial-gradient(circle_at_60%_80%,rgba(255,255,255,0.03),transparent_40%)]" />
          </div>

          {/* Rune line that shatters on scroll */}
          <div
            ref={shatterRef}
            className="pointer-events-none absolute left-1/2 top-1/2 z-10 flex -translate-x-1/2 -translate-y-1/2 flex-wrap justify-center gap-3 md:gap-4"
            aria-hidden
          >
            {["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛋ", "ᛏ"].map((r, i) => (
              <span
                key={i}
                data-shatter-rune
                className="text-2xl md:text-3xl text-amber-200/70 drop-shadow-[0_0_10px_rgba(255,214,120,0.4)]"
                style={{ textShadow: "0 0 14px rgba(255,210,120,0.35)" }}
              >
                {r}
              </span>
            ))}
          </div>
        </div>

        <div className="relative mx-auto flex max-w-6xl flex-col items-start px-5 pb-10 pt-16 md:pt-24">
          <div className="relative">
            <div
              ref={runeRingRef}
              className="absolute -left-10 -top-10 hidden h-32 w-32 rounded-full border border-amber-200/20 bg-amber-200/5 shadow-[0_0_50px_rgba(255,210,120,0.14)] md:block"
            />
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs tracking-widest text-white/65">
              <span className="text-amber-200/70">ᛖ</span> Врата открыты • 12:00–18:00 UTC
            </div>
          </div>

          <h1 className="rune-title mt-6 max-w-3xl text-4xl font-semibold leading-[1.06] tracking-tight md:text-6xl">
            <span className="mr-2 text-amber-200/80">ᛖ</span> Эребор — PvE-гильдия,
            <span className="block text-amber-100/90">
              <span className="mr-2 inline-block text-amber-200/70">ᛜ</span> где золото — не цель, а побочный эффект
            </span>
          </h1>

          <p className="mt-5 max-w-2xl text-base text-white/70 md:text-lg">
            Ну тут текст чисто рандомно сейчас накидан
            <span className="text-white/50"> потом и текст напишем нормальный</span>
            <span className="text-white/70"> • LFG каждый день • своя Ава-КП • доступ на мирку</span>
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a
              href={DISCORD_INVITE}
              target="_blank"
              rel="noreferrer"
              className="group relative inline-flex items-center justify-center rounded-2xl border border-amber-200/35 bg-amber-200/12 px-6 py-3 text-sm font-semibold text-amber-100 shadow-[0_0_40px_rgba(255,214,120,0.16)] hover:bg-amber-200/16"
            >
              <span className="absolute -inset-10 -z-10 opacity-0 blur-2xl transition group-hover:opacity-100 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.32),transparent_60%)]" />
              Войти в Discord
              <span className="ml-2 text-amber-200/70">↗</span>
            </a>

            <button
              onClick={() => scrollTo("about")}
              className="inline-flex items-center justify-center rounded-2xl border border-white/12 bg-white/5 px-6 py-3 text-sm font-semibold text-white/80 hover:bg-white/7"
            >
              Посмотреть, что внутри
              <span className="ml-2 text-white/50">↓</span>
            </button>
          </div>

          <div className="mt-10 grid w-full max-w-4xl grid-cols-1 gap-3 md:grid-cols-3">
            {[
              ["LFG", "Много групп", "Не ждёшь — играешь"],
              ["Налоги", "0%", "Лут твой, точка"],
              ["Prime", "12–18 UTC", "Живое окно активности"],
            ].map(([a, b, c]) => (
              <div
                key={a}
                className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4"
              >
                <div className="absolute -inset-20 opacity-20 blur-3xl [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.22),transparent_60%)]" />
                <div className="relative">
                  <div className="text-xs tracking-widest text-white/55">{a}</div>
                  <div className="mt-1 text-lg font-semibold">{b}</div>
                  <div className="mt-1 text-sm text-white/60">{c}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <main className="relative mx-auto max-w-6xl px-5 pb-24">
        <section ref={aboutRef} className="pt-16">
          <div className="grid gap-10 md:grid-cols-2 md:items-start">
            <div>
              <div className="flex items-center gap-2 text-xs tracking-widest text-amber-200/70">
                <span className="text-amber-200/60">ᛟ</span> О ГИЛЬДИИ
              </div>
              <h2 className="mt-3 text-3xl font-semibold md:text-4xl">Внутри — порядок, не «менеджмент»</h2>
              <p className="mt-4 text-white/70">
                Эребор — PvE-дом для всех уровней. Хочешь учиться — научим. Хочешь просто фармить в компании — контент будет собираться.
                Тебя не будут доить налогами и душить правилами ради галочки.
              </p>

              <ul className="mt-6 space-y-3 text-white/75">
                {[
                  ["Большое количество LFG", "Стабильно собираем группы на активности"],
                  ["Никаких налогов", "То, что выбил — твоё"],
                  ["Своя Ава-КП", "Собранная команда под ключевые форматы"],
                  ["Доступ на мирку", "Удобный старт и быстрая логистика"],
                ].map(([t, s]) => (
                  <li key={t} className="flex gap-3">
                    <span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-lg border border-amber-200/25 bg-amber-200/10 text-amber-200/80">
                      ᛟ
                    </span>
                    <div>
                      <div className="font-semibold text-white">{t}</div>
                      <div className="text-sm text-white/55">{s}</div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="absolute -inset-24 opacity-35 blur-3xl [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.24),transparent_60%),radial-gradient(circle_at_70%_65%,rgba(120,170,255,0.14),transparent_60%)]" />
              <div className="relative">
                <div className="text-xs tracking-widest text-white/60">РУННЫЙ КАМЕНЬ</div>
                <div className="mt-2 text-2xl font-semibold">Правила простые</div>
                <RuneDivider className="my-6" />
                <div className="space-y-4 text-sm text-white/70">
                  <div className="flex items-start justify-between gap-4">
                    <div>Налоги</div>
                    <div className="font-semibold text-amber-100">0%</div>
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <div>Прайм</div>
                    <div className="font-semibold text-amber-100">12–18 UTC</div>
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <div>LFG</div>
                    <div className="font-semibold text-amber-100">каждый день</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-white/65">
                    <div className="text-xs tracking-widest text-white/50">ПЛЕЙСХОЛДЕР</div>
                    <div className="mt-2">
                      
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section ref={mordorRef} className="pt-16">
          <div className="relative overflow-hidden rounded-3xl border border-amber-200/15 bg-gradient-to-b from-white/6 to-white/3">
            <div className="absolute inset-0 opacity-60 [background:radial-gradient(circle_at_20%_30%,rgba(120,170,255,0.12),transparent_55%),radial-gradient(circle_at_70%_60%,rgba(255,210,120,0.10),transparent_60%)]" />
            <div className="absolute inset-0 opacity-30 [background:linear-gradient(to_right,rgba(0,0,0,0.55),transparent_30%,rgba(0,0,0,0.55))]" />
            <div className="absolute left-3 top-3 text-2xl text-amber-200/30">ᚱ</div>
            <div className="absolute right-3 top-3 text-2xl text-amber-200/30">ᛏ</div>
            <div className="relative p-6 md:p-10">
              <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
                <div className="max-w-xl">
                  <div className="flex items-center gap-2 text-xs tracking-widest text-amber-200/70">
                    <span className="text-amber-200/60">ᛋ</span> PVP ДРУЗЬЯ
                  </div>
                  <h2 className="mt-3 text-3xl font-semibold md:text-4xl">У нас есть друзья: Mordor</h2>
                  <p className="mt-4 text-white/70">
                    Ты фокусишься на PvE, а рядом — гильдия, которая умеет в PvP и не выглядит как "пустой бренд".
                    Отдельный элемент союза — чтобы не путать роли: мы про фарм и стабильность, они про силу.
                  </p>

                  <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                    <a
                      href="https://europe.albionbb.com/guilds/nJTbhlRxTh2RAGMclSKk7A/attendance"
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center justify-center rounded-2xl border border-white/12 bg-white/6 px-6 py-3 text-sm font-semibold text-white/80 hover:bg-white/8"
                    >
                      Открыть статистику ↗
                    </a>
                    <a
                      href={DISCORD_INVITE}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center justify-center rounded-2xl border border-amber-200/30 bg-amber-200/10 px-6 py-3 text-sm font-semibold text-amber-100 hover:bg-amber-200/14"
                    >
                      Войти в Discord ↗
                    </a>
                  </div>
                </div>

                <div className="grid w-full gap-3 md:max-w-md md:grid-cols-2">
                  <StatCard
                    label="Average attendance"
                    value={`${stats?.avgAttendance ?? 0}`}
                    hint="Средняя явка"
                    loading={statsLoading}
                  />
                  <StatCard
                    label="Average IP"
                    value={`${stats?.avgIp ?? 0}`}
                    hint="Средний IP"
                    loading={statsLoading}
                  />
                  <StatCard
                    label="Kills / Deaths"
                    value={`${stats?.kills ?? 0} / ${stats?.deaths ?? 0}`}
                    hint="Суммарные"
                    loading={statsLoading}
                  />
                  <StatCard
                    label="Total kill fame"
                    value={`${stats?.killFame ?? "—"}`}
                    hint="Общий килл-фейм"
                    loading={statsLoading}
                  />
                </div>
              </div>

              <div className="mt-8 rounded-2xl border border-white/10 bg-black/25 p-5 text-sm text-white/65">
                <div className="text-xs tracking-widest text-white/45">ПРИМЕЧАНИЕ</div>
                <div className="mt-2">
                  Сейчас цифры — заглушки. Потом добавлю fetch к <span className="text-white/80">/api/mordor-stats</span> — и станет динамика
                </div>
              </div>
            </div>
          </div>
        </section>

        <section ref={perksRef} className="pt-16">
          <div className="flex items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 text-xs tracking-widest text-amber-200/70">
                <span className="text-amber-200/60">ᛖ</span> НАШИ ПЛЮШКИ
              </div>
              <h2 className="mt-3 text-3xl font-semibold md:text-4xl">Сделано для игры, не для отчётов</h2>
              <p className="mt-4 max-w-2xl text-white/70">
                Всё просто: тебе дают условия, в которых можно спокойно фармить, расти и находить группы — без кта и отвлечений
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              { t: "LFG каждый день", s: "Внутри всегда есть кому пойти в активность", r: "ᛖ" },
              { t: "Без налогов", s: "Никаких налогов «потому что так принято»", r: "ᛜ" },
              { t: "Своя Ава-КП", s: "Стабильная команда под важные форматы", r: "ᛞ" },
              { t: "Доступ на мирку", s: "Удобная логистика и быстрый старт", r: "ᛃ" },
              { t: "Прайм 12–18 UTC", s: "Активное окно — не «когда-нибудь»", r: "ᛇ" },
              { t: "Союз с PvP", s: "Сильные друзья рядом, без будок не останешься", r: "ᚱ" },
            ].map((x, i) => (
              <motion.div
                key={x.t}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-120px" }}
                transition={{ duration: 0.45, delay: i * 0.05 }}
                className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6"
              >
                <div className="absolute -inset-24 opacity-0 blur-3xl transition group-hover:opacity-100 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.22),transparent_60%)]" />
                <div className="relative">
                  <div className="flex items-center gap-3">
                    <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-amber-200/25 bg-amber-200/10 text-lg text-amber-200/80 shadow-[0_0_24px_rgba(255,214,120,0.10)] transition group-hover:scale-[1.03]">
                      {x.r}
                    </div>
                    <div className="text-lg font-semibold">{x.t}</div>
                  </div>
                  <div className="mt-3 text-sm text-white/65">{x.s}</div>
                  <div className="mt-5 h-px w-full bg-gradient-to-r from-transparent via-white/12 to-transparent" />
                  <div className="mt-4 text-xs text-white/45">
                    Плейсхолдер под лор-фразу/мем гильдии
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        <section ref={galleryRef} className="pt-16">
          <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="flex items-center gap-2 text-xs tracking-widest text-amber-200/70">
                <span className="text-amber-200/60">ᛃ</span> ГАЛЕРЕЯ
              </div>
              <h2 className="mt-3 text-3xl font-semibold md:text-4xl">Кадры из тьмы, добыча из золота</h2>
            </div>
            <a
              href={DISCORD_INVITE}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-2xl border border-amber-200/30 bg-amber-200/10 px-6 py-3 text-sm font-semibold text-amber-100 hover:bg-amber-200/14"
            >
              Забрать место в Discord ↗
            </a>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-12">
            <div className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 md:col-span-7">
              <div className="absolute inset-0 opacity-0 transition group-hover:opacity-100 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.08),transparent_60%)]" />
              <div className="relative aspect-video w-full">
                <iframe
                  src="https://www.youtube.com/embed/f10-kEjQRmg?si=bljIBqHlU0mM2Sxt"
                  title="YouTube video"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="h-full w-full rounded-2xl border-0"
                />
              </div>
              <div className="relative border-t border-white/10 p-4">
                <div className="text-xs tracking-widest text-white/55">ВИДЕО</div>
                <div className="mt-1 text-lg font-semibold">Спуск в глубины</div>
              </div>
            </div>

            <div className="grid gap-4 md:col-span-5">
              {[
                { label: "Наши пингвинчики :з", imageUrl: "https://media.discordapp.net/attachments/1473059682997502012/1473059801658298512/image.png?ex=699626d8&is=6994d558&hm=a65457356837f0212e818cf08dda06a28e67aaf7c81f17684d2f268f50b24d95&=&format=webp&quality=lossless", clipEmbedUrl: null },
                { label: "", imageUrl: "https://media.discordapp.net/attachments/1473059682997502012/1473059801952161974/image.png?ex=699626d8&is=6994d558&hm=d5350bcf8b51955babd3951c174014cd5e2e67a2c13abfd3d94518866f73b6ef&=&format=webp&quality=lossless", clipEmbedUrl: null },
                { label: "", imageUrl: null, clipEmbedUrl: "https://www.youtube.com/embed/f10-kEjQRmg?si=bljIBqHlU0mM2Sxt" },
              ].map(({ label, imageUrl, clipEmbedUrl }) => (
                <div
                  key={label || "video"}
                  className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6"
                >
                  <div className="absolute inset-0 opacity-0 transition group-hover:opacity-80 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.16),transparent_60%)]" />
                  <div className="relative">
                    <div className="text-xs tracking-widest text-white/55">{label}</div>
                    {imageUrl ? (
                      <div className="mt-2 overflow-hidden rounded-xl">
                        <img
                          src={imageUrl}
                          alt={label}
                          className="h-auto w-full object-cover"
                        />
                      </div>
                    ) : clipEmbedUrl ? (
                      <div className="mt-2 aspect-video w-full overflow-hidden rounded-xl">
                        <iframe
                          src={clipEmbedUrl}
                          title={label}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowFullScreen
                          className="h-full w-full border-0"
                        />
                      </div>
                    ) : (
                      <div className="mt-2 text-sm text-white/65">
                        Плейсхолдер под скрин • подпись • формат
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="grid gap-4 md:col-span-12 md:grid-cols-3">
              {[
                { label: "Просто сундуки", imageUrl: "https://media.discordapp.net/attachments/1345612135388155954/1456653710867431628/image.png?ex=6995cafb&is=6994797b&hm=f9c8de8749ab086070d26b618f890629570b75e4a709bb6b81b6416f2dcdd884&=&format=webp&quality=lossless" },
                { label: "с одного", imageUrl: "https://cdn.discordapp.com/attachments/1345612135388155954/1456644031512576040/image.png?ex=6995c1f8&is=69947078&hm=cfa177a9538f5ca6bfe26cce4ef319c97a2b8560c192b10475f1ed3ebaaa835d&format=webp&quality=lossless"},
                { label: "ава-данжа", imageUrl: "https://cdn.discordapp.com/attachments/1345612135388155954/1456653749996224544/image.png?ex=6995cb05&is=69947985&hm=ab0353d6f49b7576228436add638279215e07e0a637e2b066a5457f663d9c8db&format=webp&quality=lossless" },
              ].map(({ label, imageUrl }) => (
                <div
                  key={label}
                  className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6"
                >
                  <div className="absolute inset-0 opacity-0 transition group-hover:opacity-80 [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.14),transparent_60%)]" />
                  <div className="relative">
                    <div className="text-xs tracking-widest text-white/55">{label}</div>
                    {imageUrl ? (
                      <div className="mt-2 overflow-hidden rounded-xl">
                        <img
                          src={imageUrl}
                          alt={label}
                          className="h-auto w-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="mt-2 text-sm text-white/65">
                        Плейсхолдер под скрины
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section ref={contactRef} className="pt-16">
          <div className="relative overflow-hidden rounded-3xl border border-amber-200/15 bg-white/5 p-10">
            <div className="absolute left-4 top-4 text-2xl text-amber-200/25">ᛜ</div>
            <div className="absolute right-4 top-4 text-2xl text-amber-200/25">ᚷ</div>
            <div className="absolute -inset-24 opacity-40 blur-3xl [background:radial-gradient(circle_at_30%_20%,rgba(255,215,128,0.24),transparent_60%),radial-gradient(circle_at_70%_70%,rgba(120,170,255,0.14),transparent_60%)]" />
            <div className="relative grid gap-8 md:grid-cols-2 md:items-center">
              <div>
                <div className="flex items-center gap-2 text-xs tracking-widest text-amber-200/70">
                  <span className="text-amber-200/60">ᚺ</span> КОНТАКТЫ
                </div>
                <h2 className="mt-3 text-3xl font-semibold md:text-4xl">Готов войти в Эребор?</h2>
                <p className="mt-4 text-white/70">
                  Жми кнопку. В Discord тебя подхватят. Напиши, чем занимаешься и что хочешь фармить — и тебе найдут группу
                </p>
                <div className="mt-5 text-sm text-white/60">
                  PvE • без налогов • LFG • своя Ава-КП • 12–18 UTC
                </div>
              </div>

              <div className="flex flex-col gap-4">
                <a
                  href={DISCORD_INVITE}
                  target="_blank"
                  rel="noreferrer"
                  className="relative inline-flex items-center justify-center rounded-3xl border border-amber-200/35 bg-amber-200/12 px-7 py-4 text-base font-semibold text-amber-100 shadow-[0_0_55px_rgba(255,214,120,0.18)] hover:bg-amber-200/16"
                >
                  <span className="absolute -inset-10 -z-10 animate-[pulseGlow_7s_ease-in-out_infinite] opacity-40 blur-2xl [background:radial-gradient(circle_at_50%_45%,rgba(255,215,128,0.32),transparent_62%)]" />
                  Войти в Discord ↗
                </a>
                <div className="rounded-2xl border border-white/10 bg-black/25 p-5 text-sm text-white/65">
                  <div className="text-xs tracking-widest text-white/45">СОВЕТ</div>
                  <div className="mt-2">
                    Для первого сообщения: ник в Albion, что любишь (HCE/Авалонки/мирка/фарм), и активное время
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="py-10 text-center text-xs text-white/40">
            Erebor • Albion Online • Мория внутри, золото снаружи
          </div>
        </section>
      </main>
      </div>
    </div>
  )
}
