# Single L4 Spot infrastructure benchmark

This is a hardware, checkpoint and cloud lifecycle test, not a scientific model fit.
Uses experiment 29's full 48 x 32 x 32 six-channel CNN with separate output heads and physical loss. Two existing training frames (20 and 22 seconds) are spatially subsampled by four then nearest-upsampled for targets. Weights are freshly initialized; no held-out data is used. Thus timings assess architecture execution, not final predictive accuracy or full-dataset throughput.

The underlying FDS case has a generic 3 m diameter / 8 m tall cone crown at z=2–10 m, frozen vegetation particles, fixed moisture, artificial 20-second hot-particle ignition, 0.5 m cells, bare nonflammable ground and no trunks/buildings/embers. Those physics are unchanged; this benchmark generates no FDS simulations.

One g2-standard-4 Spot VM (one 24 GB L4, four vCPU, 16 GiB RAM), official PyTorch 2.5.1 CUDA 12.4 container, Batch-installed drivers. Existing worker and watchdog accounts only; no IAM changes.

Budget: $1 reserved before submission, no recycling or automatic retries. Published Google Spot reference $0.402748/h (https://cloud.google.com/spot-vms/pricing); conservative envelope $0.80/h for 50 minutes plus $0.3333 for ancillary costs/cleanup. This is an operational bound, not a billing-account hard cap or invoice amount.

Cloud Workflows cancels if no VM exists after 30 minutes, or any matching VM exceeds 20 minutes of age (creation timestamp, including setup). An absolute 50-minute deadline bounds the entire attempt. Polling adds up to 30 seconds plus deletion latency; ancillary allowance covers that margin. Batch task itself has a 15-minute limit. Controller deletes Batch job and checks/deletes matching VMs independently of the laptop. No automatic retry. Batch boot disks are temporary and collection verifies their absence.

Training: 5 warmup steps, 100 timed AdamW steps with checkpoint upload every 25 steps, next-step restoration consistency, then four 91-frame inference passes. Timing includes checkpoint uploads; inference is GPU-only without exporting fields. Checkpoints remain in cloud storage if Spot loss occurs after upload; no automatic continuation. Latest local training processes remain SIGSTOP suspended.

Run order: prepare.py (lightweight sample packaging), launch.py (one-shot reservation/submission), collect.py (poll/download/cleanup verification). Cloud submission is explicit; DVC does not automatically launch paid compute. All bulk checkpoints and raw outputs remain under data/.
