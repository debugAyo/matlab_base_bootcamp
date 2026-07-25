(() => {
  "use strict";

  /* ===== PRELOADER ===== */
  const preloader = document.getElementById("preloader");
  window.addEventListener("load", () => {
    setTimeout(() => {
      preloader.classList.add("fade-out");
      document.body.classList.remove("loading");
      setTimeout(() => preloader.remove(), 600);
    }, 2000);
  });
  document.body.classList.add("loading");

  /* ===== HERO CANVAS — PARTICLES ===== */
  const canvas = document.getElementById("heroCanvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    let w, h, particles = [], mouse = { x: -1000, y: -1000 };

    function resize() {
      w = canvas.width = canvas.parentElement.offsetWidth;
      h = canvas.height = canvas.parentElement.offsetHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    class Particle {
      constructor() { this.reset(); }
      reset() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.r = Math.random() * 2 + 0.5;
        this.alpha = Math.random() * 0.4 + 0.1;
        this.color = Math.random() > 0.7 ? "73,195,195" : "255,255,255";
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        const dx = mouse.x - this.x, dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) { this.x -= dx * 0.008; this.y -= dy * 0.008; }
        if (this.x < 0 || this.x > w) this.vx *= -1;
        if (this.y < 0 || this.y > h) this.vy *= -1;
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this.color},${this.alpha})`;
        ctx.fill();
      }
    }

    const count = Math.min(Math.floor((w * h) / 8000), 120);
    for (let i = 0; i < count; i++) particles.push(new Particle());

    function connectParticles() {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 140) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(73,195,195,${0.08 * (1 - dist / 140)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
    }

    function animateParticles() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => { p.update(); p.draw(); });
      connectParticles();
      requestAnimationFrame(animateParticles);
    }
    animateParticles();

    canvas.parentElement.addEventListener("mousemove", e => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    canvas.parentElement.addEventListener("mouseleave", () => { mouse.x = -1000; mouse.y = -1000; });
  }

  /* ===== NAVBAR ===== */
  const navbar = document.getElementById("navbar");
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");

  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 60);
  });

  if (navToggle) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("open");
      navToggle.classList.toggle("active");
    });
    navLinks.querySelectorAll("a").forEach(a => {
      a.addEventListener("click", () => {
        navLinks.classList.remove("open");
        navToggle.classList.remove("active");
      });
    });
  }

  /* ===== SCROLL REVEAL ===== */
  const reveals = document.querySelectorAll(".reveal");
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
  reveals.forEach(el => revealObserver.observe(el));

  /* ===== COUNTER ANIMATION ===== */
  const statNums = document.querySelectorAll(".hero-stat-num");
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const text = el.textContent;
        const match = text.match(/(\d+)/);
        if (match) {
          const target = parseInt(match[1]);
          const suffix = text.replace(match[1], "");
          let current = 0;
          const step = Math.ceil(target / 40);
          const timer = setInterval(() => {
            current += step;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = current + suffix;
          }, 30);
        }
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  statNums.forEach(el => counterObserver.observe(el));

  /* ===== FORM SUBMISSION ===== */
  const form = document.getElementById("registerForm");
  const msg = document.getElementById("formMessage");
  const submitBtn = document.getElementById("submitBtn");
  const API_URL = "/api/register";

  function saveLocally(data) {
    const existing = JSON.parse(localStorage.getItem("bootcamp_registrations") || "[]");
    existing.push({ ...data, timestamp: new Date().toISOString() });
    localStorage.setItem("bootcamp_registrations", JSON.stringify(existing));
  }

  function showMessage(text, type) {
    msg.textContent = text;
    msg.className = "form-message show " + type;
  }

  /* ===== MODAL ===== */
  const modal = document.getElementById("successModal");
  const modalName = document.getElementById("modalName");
  const modalClose = document.getElementById("modalClose");
  const modalDone = document.getElementById("modalDone");
  const googleCalLink = document.getElementById("googleCalLink");
  const downloadIcs = document.getElementById("downloadIcs");

  function openModal(name) {
    modalName.textContent = name.split(" ")[0];
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    buildCalendarLinks();
  }

  function closeModal() {
    modal.classList.remove("open");
    document.body.style.overflow = "";
  }

  if (modalClose) modalClose.addEventListener("click", closeModal);
  if (modalDone) modalDone.addEventListener("click", closeModal);
  if (modal) modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

  /* ===== CALENDAR ===== */
  const EVENT = {
    title: "FUTMinna MATLAB Base",
    start: "20260817T090000",
    end: "20260824T160000",
    location: "Engineering Complex, FUTMinna, Minna, Niger State, Nigeria",
    description: "A one-week, MATLAB-based engineering training at Federal University of Technology, Minna. Build real simulations, model physical systems, and earn a certificate."
  };

  function buildCalendarLinks() {
    const gUrl = "https://calendar.google.com/calendar/render?" + new URLSearchParams({
      action: "TEMPLATE",
      text: EVENT.title,
      dates: EVENT.start + "/" + EVENT.end,
      location: EVENT.location,
      details: EVENT.description,
      sf: "true",
      output: "xml"
    }).toString();
    googleCalLink.href = gUrl;
  }

  function generateICS() {
    const ics = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//FUTMinna MATLAB Base//EN",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
      "BEGIN:VEVENT",
      "DTSTART:" + EVENT.start,
      "DTEND:" + EVENT.end,
      "SUMMARY:" + EVENT.title,
      "LOCATION:" + EVENT.location,
      "DESCRIPTION:" + EVENT.description,
      "STATUS:CONFIRMED",
      "BEGIN:VALARM",
      "TRIGGER:-P1D",
      "ACTION:DISPLAY",
      "DESCRIPTION:FUTMinna MATLAB Base starts tomorrow!",
      "END:VALARM",
      "BEGIN:VALARM",
      "TRIGGER:-PT1H",
      "ACTION:DISPLAY",
      "DESCRIPTION:FUTMinna MATLAB Base starts in 1 hour!",
      "END:VALARM",
      "END:VEVENT",
      "END:VCALENDAR"
    ].join("\r\n");

    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "futminna-matlab-base.ics";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  if (downloadIcs) downloadIcs.addEventListener("click", generateICS);

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      submitBtn.classList.add("loading");

      const data = {
        fullname: document.getElementById("fullname").value.trim(),
        email: document.getElementById("email").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        level: document.getElementById("level").value,
        department: document.getElementById("department").value.trim(),
        expectation: document.getElementById("expectation").value
      };

      if (!data.fullname || !data.email || !data.phone || !data.level || !data.department || !data.expectation) {
        showMessage("Please fill in all fields.", "error");
        submitBtn.classList.remove("loading");
        return;
      }

      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Server error");
        form.reset();
        msg.className = "form-message";
        openModal(data.fullname);
      } catch {
        saveLocally(data);
        form.reset();
        msg.className = "form-message";
        openModal(data.fullname);
      } finally {
        submitBtn.classList.remove("loading");
      }
    });
  }

  /* ===== SMOOTH ANCHOR SCROLL ===== */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener("click", (e) => {
      const target = document.querySelector(a.getAttribute("href"));
      if (target) {
        e.preventDefault();
        const offset = navbar.offsetHeight + 20;
        window.scrollTo({ top: target.offsetTop - offset, behavior: "smooth" });
      }
    });
  });

})();
