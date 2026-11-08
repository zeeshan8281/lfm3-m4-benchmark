# LFM3 animated line-chart dashboard

16 seconds / 1920×1080 / 60 fps / silent. Five animated line charts replace the bars: individual decode intervals, all 15 raw decode-speed samples, cumulative 64 token arrivals, median first-token latency, and median peak MLX memory. Numeric labels reflect recorded values. Lines connect observed points without smoothing; interpolation is visual, not an additional measurement.

Token arrivals and the decode-step cursor replay real timestamps every four seconds. The run-by-run chart cycles a visual highlight through existing repetitions; it does not represent new runs. All slow samples remain included. Functional results and the factual failure remain visible. No personal branding, laptop illustration, soundtrack or narration.

Run npm install, then npx remotion render index.jsx LFM3Bento lfm3-bento-v3.mp4 --concurrency=2. Versions are pinned in package.json. No model download needed.
